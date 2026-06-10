#!/usr/bin/env python3
"""
vision_handler.py — Telegram TradingView chart analyzer

Watches OpenClaw's inbound media directory for new screenshots.
When a .jpg appears (from the AI Hangout group), it:
  1. Sends to a vision model (Gemini 2.5 Flash by default) via OpenRouter
  2. Gets structured trade analysis
  3. Writes it as a chart_analysis signal into the pipeline

Usage:
  python3 vision_handler.py                    # one-shot: process all unprocessed images
  python3 vision_handler.py --watch            # daemon mode: poll every 10s
  python3 vision_handler.py /path/to/image.jpg # analyze specific image
"""

import argparse
import base64
import json
import logging
import os
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("vision")

# ── config ──────────────────────────────────────────────────────────────
INBOUND_DIR = Path("/home/synczus/.openclaw/media/inbound")
PROCESSED_DIR = Path("/home/synczus/kestrel/vision/processed")
SIGNALS_PATH = Path("/home/synczus/kestrel/dashboard/pending.json")
TRACKER_PATH = Path("/home/synczus/kestrel/vision/tracker.json")

# OpenRouter config
OR_API_KEY = "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"
OR_BASE = "https://openrouter.ai/api/v1/chat/completions"

# Vision model — cheap + good at charts
DEFAULT_MODEL = "google/gemini-2.5-flash"
HEAVY_MODEL = "anthropic/claude-sonnet-4.5"

# Trading analysis prompt
CHART_PROMPT = """You are a ruthless professional trader analyzing a multi-timeframe TradingView screenshot.

Identify:
1. Key support/resistance levels (with specific prices)
2. Current trend (direction, strength, timeframe)
3. Volume profile (any divergence or confirmation)
4. Patterns (flag, wedge, double top/bottom, head and shoulders, etc.)
5. Order blocks / liquidity zones
6. Confluence across timeframes

Output ONLY valid JSON with this exact schema:
{
  "symbol": "<best guess ticker or null>",
  "timeframe_hint": "<if visible>",
  "bias": "bullish|bearish|neutral",
  "confidence": 0.0-1.0,
  "key_levels": {"support": ["$price1", "$price2"], "resistance": ["$price1"]},
  "entry_zones": ["zone description"],
  "take_profit": ["$price"],
  "stop_loss": ["$price"],
  "patterns": ["pattern name"],
  "trend": "uptrend|downtrend|ranging",
  "volume_note": "observation",
  "summary": "one-sentence actionable take"
}

No explanations, no markdown, no code fences. Pure JSON."""


def load_tracker() -> dict:
    if TRACKER_PATH.exists():
        return json.loads(TRACKER_PATH.read_text())
    return {"processed": [], "last_run": None}


def save_tracker(tracker: dict):
    TRACKER_PATH.parent.mkdir(parents=True, exist_ok=True)
    TRACKER_PATH.write_text(json.dumps(tracker, indent=2))


def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def analyze_image(image_path: str, model: str = DEFAULT_MODEL) -> dict:
    """Send image to vision model via OpenRouter, return structured analysis."""
    image_b64 = encode_image(image_path)

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": CHART_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_b64}"
                        },
                    },
                ],
            }
        ],
        "max_tokens": 2000,
        "temperature": 0.1,
    }

    req = urllib.request.Request(
        OR_BASE,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {OR_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/synczus/kestrel",
            "X-Title": "Kestrel Vision Handler",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        log.error(f"OpenRouter HTTP {e.code}: {e.read().decode()[:200]}")
        return {"error": f"HTTP {e.code}"}
    except Exception as e:
        log.error(f"OpenRouter error: {e}")
        return {"error": str(e)}

    # Extract content from response
    try:
        content = result["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        log.error(f"Unexpected response: {json.dumps(result)[:200]}")
        return {"error": "unexpected response format"}

    # Try to parse JSON from the response
    # Remove any markdown code fences
    content_clean = re.sub(r"```(?:json)?\s*", "", content).strip()

    try:
        analysis = json.loads(content_clean)
    except json.JSONDecodeError:
        # Model didn't return valid JSON — wrap the raw text
        analysis = {
            "raw_text": content_clean,
            "bias": "unknown",
            "confidence": 0.0,
            "summary": content_clean[:200],
        }

    analysis["_model"] = model
    analysis["_analyzed_at"] = datetime.now(timezone.utc).isoformat()
    return analysis


def emit_signal(analysis: dict, image_name: str):
    """Write analysis as a pipeline signal."""
    signal = {
        "type": "chart_analysis",
        "source": "vision_handler",
        "source_image": image_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "symbol": analysis.get("symbol"),
        "bias": analysis.get("bias", "unknown"),
        "confidence": analysis.get("confidence", 0.0),
        "summary": analysis.get("summary", ""),
        "key_levels": analysis.get("key_levels", {}),
        "entry_zones": analysis.get("entry_zones", []),
        "patterns": analysis.get("patterns", []),
        "trend": analysis.get("trend", "unknown"),
        "model": analysis.get("_model", DEFAULT_MODEL),
    }

    # Append to pending signals queue
    SIGNALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = []
    if SIGNALS_PATH.exists():
        try:
            existing = json.loads(SIGNALS_PATH.read_text())
            if not isinstance(existing, list):
                existing = [existing]
        except json.JSONDecodeError:
            existing = []

    existing.append(signal)
    SIGNALS_PATH.write_text(json.dumps(existing, indent=2))
    log.info(f"Signal emitted: {signal['bias']} on {signal['symbol'] or '?'} (conf={signal['confidence']})")


def find_unprocessed(tracker: dict) -> list:
    """Find .jpg files in inbound dir not yet processed."""
    processed = set(tracker.get("processed", []))
    images = sorted(INBOUND_DIR.glob("*.jpg"), key=os.path.getmtime)
    return [img for img in images if img.name not in processed]


def process_one(image_path: Path, model: str = DEFAULT_MODEL, heavy: bool = False):
    """Analyze one image and emit the signal."""
    log.info(f"Analyzing {image_path.name} (model={'heavy ' + HEAVY_MODEL if heavy else DEFAULT_MODEL})...")
    
    analysis = analyze_image(str(image_path), model=model)
    
    if "error" in analysis:
        log.error(f"Failed: {analysis['error']}")
        # Try heavy model as fallback
        if not heavy:
            log.info(f"Retrying with heavy model {HEAVY_MODEL}...")
            return process_one(image_path, model=HEAVY_MODEL, heavy=True)
        return analysis
    
    emit_signal(analysis, image_path.name)
    
    # Archive the processed image
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    dest = PROCESSED_DIR / image_path.name
    image_path.rename(dest)
    
    log.info(f"Done — {image_path.name} → {analysis.get('bias', '?')} ({analysis.get('confidence', 0):.2f})")
    
    # Also log the structured output
    summary = analysis.get("summary", "")
    levels = analysis.get("key_levels", {})
    
    msg_parts = []
    if analysis.get("symbol"):
        msg_parts.append(f"${analysis['symbol']}")
    if levels:
        supports = levels.get("support", [])
        resistances = levels.get("resistance", [])
        if supports:
            msg_parts.append(f"Support: {', '.join(supports[:2])}")
        if resistances:
            msg_parts.append(f"Resistance: {', '.join(resistances[:2])}")
    if analysis.get("patterns"):
        msg_parts.append(f"Patterns: {', '.join(analysis['patterns'][:2])}")
    if summary:
        msg_parts.append(summary[:120])
    
    log.info(f"📊 {' | '.join(msg_parts)}")
    
    return analysis


def process_all(model: str = DEFAULT_MODEL):
    """Process all unprocessed images."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    tracker = load_tracker()
    
    images = find_unprocessed(tracker)
    if not images:
        log.info("No new images to process")
        return
    
    log.info(f"Found {len(images)} new image(s)")
    
    for img in images:
        tracker["processed"].append(img.name)
        result = process_one(img, model=model)
        if "error" in result and not result.get("raw_text"):
            # Keep in tracker but mark as failed
            tracker["processed"].append(f"{img.name}:FAILED")
    
    tracker["last_run"] = datetime.now(timezone.utc).isoformat()
    save_tracker(tracker)


def watch_loop(interval: int = 10, model: str = DEFAULT_MODEL):
    """Daemon mode — poll for new images every N seconds."""
    log.info(f"Watch mode started (interval={interval}s, model={model})")
    
    while True:
        try:
            process_all(model=model)
        except Exception as e:
            log.error(f"Watch loop error: {e}")
        time.sleep(interval)


# ── CLI ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="TradingView chart vision analyzer")
    parser.add_argument("image", nargs="?", help="Specific image path to analyze")
    parser.add_argument("--watch", action="store_true", help="Daemon mode: poll every 10s")
    parser.add_argument("--interval", type=int, default=10, help="Poll interval in seconds")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Vision model (default: {DEFAULT_MODEL})")
    parser.add_argument("--heavy", action="store_true", help="Use heavy model (Claude Sonnet)")
    
    args = parser.parse_args()
    
    # Resolve model
    model = HEAVY_MODEL if args.heavy else args.model
    
    if args.image:
        path = Path(args.image)
        if not path.exists():
            log.error(f"Image not found: {args.image}")
            sys.exit(1)
        result = process_one(path, model=model)
        print(json.dumps(result, indent=2))
    elif args.watch:
        watch_loop(interval=args.interval, model=model)
    else:
        process_all(model=model)


if __name__ == "__main__":
    main()