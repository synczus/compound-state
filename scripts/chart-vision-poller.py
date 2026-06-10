#!/usr/bin/env python3
"""
Chart Vision Poller — watches Telegram for TradingView screenshots,
analyzes them with a vision model, writes structured output to DuckDB,
and posts analysis to the group.

Designed for cron (no_agent=True): no LLM loop, just raw script.
"""

import base64
import json
import os
import sqlite3
import sys
import time
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────────
KESTREL = Path(__file__).resolve().parent.parent
ENV_FILE = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes"))) / ".env"

def load_env():
    """Load env vars from Hermes .env file."""
    env = {}
    if ENV_FILE.exists():
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    return env

env = load_env()

TELEGRAM_TOKEN = env.get("HERMES_BOT_TOKEN") or env.get("TELEGRAM_BOT_TOKEN", "")
OPENROUTER_KEY = env.get("OPENROUTER_API_KEY", "")
HOME_CHANNEL = env.get("TELEGRAM_HOME_CHANNEL", "-5087043705")
VISION_MODEL = "anthropic/claude-sonnet-4"
# Premium model for chart analysis — Claude Sonnet 4 is best-in-class for chart reading

# State file: tracks last processed message ID so we don't re-process
STATE_FILE = KESTREL / "data" / "chart-vision-state.json"
DUCKDB_PATH = KESTREL / "signals.duckdb"

# ── Trading System Prompt ────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a ruthless professional trader analyzing a TradingView chart screenshot.

Analyze the chart across all visible timeframes. Output your analysis as valid JSON ONLY — no markdown, no explanation outside the JSON.

{
  "symbol": "ticker if visible, else UNKNOWN",
  "timeframes": ["1m", "5m", "15m", "1h", "4h", "1d", "1w"],
  "bias": "long" | "short" | "neutral",
  "bias_confidence": 0.0-1.0,
  "key_levels": {
    "support": [{"price": 123.45, "strength": "weak"|"moderate"|"strong", "notes": "..."}],
    "resistance": [{"price": 123.45, "strength": "weak"|"moderate"|"strong", "notes": "..."}]
  },
  "entry_zones": {
    "long": [{"zone": "123-125", "reason": "..."}],
    "short": [{"zone": "130-132", "reason": "..."}]
  },
  "invalidation": {"price": 120.0, "reason": "..."},
  "volume_profile": "rising" | "falling" | "flat" | "unknown",
  "pattern": "ascending_triangle" | "double_top" | "head_and_shoulders" | "flag" | "wedge" | "range" | "breakout" | "none_detected",
  "market_regime": "trending_up" | "trending_down" | "ranging" | "volatile" | "unknown",
  "notes": "key confluence or warnings"
}"""

# ── Telegram API ─────────────────────────────────────────────────────────────

TG_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

def tg_call(method, data=None):
    """Call Telegram API. Returns parsed JSON or None."""
    url = f"{TG_API}/{method}"
    try:
        if data:
            req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode())
        else:
            req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, timeout=15)
        return json.loads(resp.read())
    except Exception as e:
        print(f"[ERROR] Telegram API {method}: {e}", file=sys.stderr)
        return None

def get_updates(offset=0):
    """Fetch recent messages from the home channel."""
    data = {
        "allowed_updates": json.dumps(["message"]),
        "timeout": 5,
    }
    if offset:
        data["offset"] = offset
    result = tg_call("getUpdates", data)
    if result and result.get("ok"):
        return result.get("result", [])
    return []

def get_file_path(file_id):
    """Get Telegram file path for downloading."""
    result = tg_call("getFile", {"file_id": file_id})
    if result and result.get("ok"):
        file_info = result.get("result", {})
        return file_info.get("file_path")
    return None

def download_file(file_id):
    """Download a Telegram photo file. Returns base64 image data."""
    file_path = get_file_path(file_id)
    if not file_path:
        return None
    url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
    try:
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, timeout=20)
        return base64.b64encode(resp.read()).decode()
    except Exception as e:
        print(f"[ERROR] Download {file_id}: {e}", file=sys.stderr)
        return None

def send_message(chat_id, text, reply_to=None):
    """Post a message to Telegram."""
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
    }
    if reply_to:
        data["reply_to_message_id"] = reply_to
    tg_call("sendMessage", data)

# ── Vision Analysis ──────────────────────────────────────────────────────────

def analyze_chart(image_b64):
    """Send chart image to vision model via OpenRouter. Returns parsed JSON."""
    payload = {
        "model": VISION_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Analyze this TradingView chart. Return JSON only."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
                ],
            },
        ],
        "temperature": 0.1,
        "max_tokens": 2000,
    }
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "HTTP-Referer": "https://kestrel.markets",
        },
    )
    content = ""
    try:
        resp = urllib.request.urlopen(req, timeout=60)
        result = json.loads(resp.read())
        content = result["choices"][0]["message"]["content"]
        # Extract JSON from response (in case model wraps it)
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            content = content.rsplit("```", 1)[0]
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:].strip()
            if content.endswith("```"):
                content = content[:-3].strip()
        return json.loads(content)
    except json.JSONDecodeError:
        snippet = content[:200] if content else "empty"
        print(f"[WARN] Vision response was not valid JSON: {snippet}", file=sys.stderr)
        return {"error": "parse_failed", "raw": snippet}
    except Exception as e:
        print(f"[ERROR] Vision API: {e}", file=sys.stderr)
        return {"error": str(e)}

# ── DuckDB Storage ───────────────────────────────────────────────────────────

def ensure_db():
    """Create chart_analysis table if it doesn't exist."""
    try:
        import duckdb
        con = duckdb.connect(str(DUCKDB_PATH))
        con.execute("""
            CREATE TABLE IF NOT EXISTS chart_analysis (
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                message_id BIGINT,
                symbol VARCHAR,
                timeframes VARCHAR,
                bias VARCHAR,
                bias_confidence DOUBLE,
                support_levels VARCHAR,
                resistance_levels VARCHAR,
                entry_zones VARCHAR,
                invalidation VARCHAR,
                volume_profile VARCHAR,
                pattern VARCHAR,
                market_regime VARCHAR,
                notes VARCHAR,
                raw_json VARCHAR,
                chat_id BIGINT
            )
        """)
        con.close()
        return True
    except Exception as e:
        print(f"[ERROR] DB setup: {e}", file=sys.stderr)
        return False

def store_analysis(analysis, message_id, chat_id):
    """Write vision analysis to DuckDB."""
    try:
        import duckdb
        con = duckdb.connect(str(DUCKDB_PATH))
        con.execute("""
            INSERT INTO chart_analysis (
                message_id, symbol, timeframes, bias, bias_confidence,
                support_levels, resistance_levels, entry_zones,
                invalidation, volume_profile, pattern, market_regime,
                notes, raw_json, chat_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            message_id,
            analysis.get("symbol", "UNKNOWN"),
            json.dumps(analysis.get("timeframes", [])),
            analysis.get("bias", "neutral"),
            analysis.get("bias_confidence", 0.0),
            json.dumps(analysis.get("key_levels", {}).get("support", [])),
            json.dumps(analysis.get("key_levels", {}).get("resistance", [])),
            json.dumps(analysis.get("entry_zones", {})),
            json.dumps(analysis.get("invalidation", {})),
            analysis.get("volume_profile", "unknown"),
            analysis.get("pattern", "none_detected"),
            analysis.get("market_regime", "unknown"),
            analysis.get("notes", ""),
            json.dumps(analysis),
            int(chat_id),
        ])
        con.close()
        return True
    except Exception as e:
        print(f"[ERROR] Store analysis: {e}", file=sys.stderr)
        return False

# ── State Management ─────────────────────────────────────────────────────────

def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {"last_update_id": 0, "processed_ids": []}

def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))

# ── Format for Telegram ──────────────────────────────────────────────────────

def format_analysis(analysis):
    """Format analysis into a concise Telegram message."""
    symbol = analysis.get("symbol", "UNKNOWN")
    bias = analysis.get("bias", "neutral").upper()
    conf = analysis.get("bias_confidence", 0) * 100
    regime = analysis.get("market_regime", "unknown").replace("_", " ")
    pattern = analysis.get("pattern", "none_detected").replace("_", " ")

    lines = [
        f"📊 *{symbol}* — {bias} ({conf:.0f}%)",
        f"📈 Regime: {regime}  |  Pattern: {pattern}",
    ]

    # Key levels
    levels = analysis.get("key_levels", {})
    supports = levels.get("support", [])
    resistances = levels.get("resistance", [])
    if supports:
        s = supports[0]
        lines.append(f"🟢 Support: ${s['price']} ({s['strength']})")
    if resistances:
        r = resistances[0]
        lines.append(f"🔴 Resistance: ${r['price']} ({r['strength']})")

    # Entry zones
    zones = analysis.get("entry_zones", {})
    if zones.get("long"):
        lines.append(f"📌 Long zone: {zones['long'][0]['zone']}")
    if zones.get("short"):
        lines.append(f"📌 Short zone: {zones['short'][0]['zone']}")

    # Invalidation
    inval = analysis.get("invalidation", {})
    if inval.get("price"):
        lines.append(f"⚠️ Invalidation: ${inval['price']}")

    # Notes
    notes = analysis.get("notes", "")
    if notes:
        lines.append(f"\n_{notes}_")

    return "\n".join(lines)

# ── Main Loop ────────────────────────────────────────────────────────────────

def main():
    state = load_state()
    last_id = state.get("last_update_id", 0)
    processed = set(state.get("processed_ids", []))

    updates = get_updates(last_id + 1)
    if not updates:
        print(f"[OK] No updates (last_id={last_id})", file=sys.stderr)
        return

    chat_id = HOME_CHANNEL  # Use -5087043705 as default

    for update in updates:
        update_id = update.get("update_id", 0)
        msg = update.get("message", {})
        msg_id = msg.get("message_id", 0)

        # Track update ID for offset
        if update_id > last_id:
            last_id = update_id

        # Only process photos
        photos = msg.get("photo")
        if not photos:
            continue

        # Skip already-processed
        if msg_id in processed:
            continue

        # Get the largest photo (best quality)
        largest = max(photos, key=lambda p: p.get("file_size", 0))
        file_id = largest["file_id"]
        msg_chat = msg.get("chat", {}).get("id", chat_id)

        print(f"[PROCESS] msg={msg_id} file={file_id}")

        # Download
        image_b64 = download_file(file_id)
        if not image_b64:
            print(f"[SKIP] msg={msg_id} download failed")
            processed.add(msg_id)
            continue

        # Analyze
        analysis = analyze_chart(image_b64)
        if not analysis or "error" in analysis:
            err = analysis.get("error", "unknown") if analysis else "no_response"
            print(f"[FAIL] msg={msg_id} vision error: {err}")
            processed.add(msg_id)
            continue

        # Store to DuckDB
        store_analysis(analysis, msg_id, msg_chat)

        # Post to Telegram
        summary = format_analysis(analysis)
        send_message(HOME_CHANNEL, summary, reply_to=msg_id)
        print(f"[OK] msg={msg_id} analyzed & posted")

        processed.add(msg_id)

    # Save state
    state["last_update_id"] = last_id
    state["processed_ids"] = list(processed)[-500:]  # keep last 500
    save_state(state)

    # Report total processed this run
    total = len(updates)
    photos = sum(1 for u in updates if u.get("message", {}).get("photo"))
    if photos > 0:
        print(f"[DONE] {photos}/{total} updates were photos — processed")
    else:
        print(f"[OK] {total} updates checked, no photos found", file=sys.stderr)


if __name__ == "__main__":
    main()