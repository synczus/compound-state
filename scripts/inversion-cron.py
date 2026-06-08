#!/usr/bin/env python3
"""Grok inversion cron — every 30 min, challenge every compound assumption.
Reads chat history since last inversion so Grok responds to actual conversation."""

import json, os, sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path("/home/synczus/kestrel")
STAGING = BASE / "staging"
CURRENT_STATE = BASE / "cycle-state" / "current.json"
HOP_SEQUENCE = BASE / "cycle-state" / "hop-sequence.json"
LAST_INVERSION = STAGING / "last-inversion.json"

def read_json(path):
    try: return json.loads(path.read_text())
    except: return {}

def read_pipeline_state():
    """Query latest MTA verdicts from DuckDB."""
    try:
        import duckdb
        con = duckdb.connect(str(BASE / "signals.duckdb"), read_only=True)
        rows = con.execute(
            "SELECT asset, direction, verdict, consensus_strength, diagnosis_json, created_at "
            "FROM mtf_diagnosis ORDER BY created_at DESC LIMIT 10"
        ).fetchall()
        con.close()
        result = []
        for r in rows:
            diag = {}
            if isinstance(r[4], str):
                try: diag = json.loads(r[4])
                except: pass
            result.append({
                "asset": r[0], "direction": r[1], "verdict": r[2],
                "consensus_strength": r[3],
                "price": diag.get("price", "?"),
                "analyzed_at": r[5][:19] if r[5] else "?"
            })
        return result
    except:
        return []

def read_chat_since_last_inversion():
    """Read Telegram AI Hangout messages since the last inversion fired."""
    last_inv = read_json(LAST_INVERSION)
    last_ts = last_inv.get("timestamp", None)
    if not last_ts:
        return []

    try:
        import duckdb
        con = duckdb.connect(str(BASE / "signals.duckdb"), read_only=True)
        # First try: signals table (real-time chat, if being ingested)
        rows = con.execute("""
            SELECT 'chat' as src_type, signal_id, source_id, event_type, ingested_at, headline, body_text
            FROM signals
            WHERE ingested_at >= ?::TIMESTAMP
              AND source_id LIKE '%AIHangout%'
              AND event_type NOT IN ('reaction', 'edit')
            ORDER BY ingested_at ASC
            LIMIT 50
        """, (last_ts,)).fetchall()

        # Fallback: events table (pipeline outputs, analysis, decisions)
        if len(rows) == 0:
            rows = con.execute("""
                SELECT 'event' as src_type, row_id::VARCHAR, source_id, event_type, ingested_ts,
                       payload_headline, payload_body
                FROM events
                WHERE ingested_ts > ?::TIMESTAMP - INTERVAL '1 hour'
                ORDER BY ingested_ts ASC
                LIMIT 40
            """, (last_ts,)).fetchall()

        con.close()
        return rows
    except:
        return []

SYSTEM_PROMPT = """You are the compound's inversion layer — a ruthless assumption auditor.

Every 30 min you receive the system state AND the chat conversation that happened since your last inversion. Your job: find 3 things the compound is wrong about.

Rules:
- Attack every assumption. If the chat treated something as true, question it.
- Find contradictions between what was said in chat and what the system state reports.
- Find blind spots in the pipeline, stale market assumptions, gaps in the model of reality.
- Specifically reference what was said in the chat history. Quote the conversation.
- If the last inversion is still unresolved, flag it.
- Be specific. "The hop assumption is wrong" is useless. "Chase said they wanted X but the pipeline shows Y — that's a contradiction" is useful.
- Output in this format:

## 🎯 Inversion #{count}

### 1. [Blind Spot Title]
[Specific observation about what was said in chat vs reality]

### 2. [Blind Spot Title]  
[Specific observation]

### 3. [Blind Spot Title]
[Specific observation]

**Severity:** [HIGH/MEDIUM/LOW]

## 10-second Action
[One specific thing the compound should do about the #1 issue, actionable now]

Do NOT hedge. Do NOT soften. Be the agent that tells the compound what it doesn't want to hear."""

def build_context():
    """Build context: system state + chat history since last inversion."""
    hop = read_json(HOP_SEQUENCE)
    state = read_json(CURRENT_STATE)
    last_inv = read_json(LAST_INVERSION)
    mta = read_pipeline_state()

    is_active = hop.get('active', False)
    is_complete = hop.get('complete', False)
    query = hop.get('query', 'none')
    query_display = "None (last: " + query + ")" if is_complete else query

    lines = ["## System State"]
    lines.append(f"Active hop: {query_display}")
    lines.append(f"Hop active: {is_active}")
    lines.append(f"Hop complete: {is_complete}")
    # Time since last inversion
    inv_time = last_inv.get("timestamp", None)
    time_since = "first run"
    if inv_time:
        try:
            inv_dt = datetime.fromisoformat(inv_time.replace("Z", "+00:00"))
            elapsed = datetime.now(timezone.utc) - inv_dt
            mins = int(elapsed.total_seconds() / 60)
            if mins < 60:
                time_since = f"{mins} minutes ago"
            else:
                time_since = f"{mins//60}h {mins%60}m ago"
        except:
            time_since = "unknown"
    lines.append(f"Time since last inversion: {time_since}")

    if mta:
        lines.append("\n## MTA Verdicts")
        for r in mta[:6]:
            lines.append(f"{r['asset']}: {r['verdict']} @ ${r['price']} — strength {r['consensus_strength']}")

    if last_inv:
        lines.append(f"\n## Last Inversion ({last_inv.get('timestamp','?')})")
        lines.append(f"Claim: {last_inv.get('key_claim','none')}")
        status = "✅ RESOLVED" if last_inv.get('resolved') else "❌ UNRESOLVED"
        lines.append(f"Status: {status}")

    lines.append("\n## Active Blockers")
    blockers = state.get('blockers', [])
    if blockers:
        for b in blockers[:3]:
            lines.append(f"- {b.get('text','?')}")
    else:
        lines.append("None")

    # Chat history since last inversion
    chat_msgs = read_chat_since_last_inversion()
    if chat_msgs:
        lines.append(f"\n## Chat Since Last Inversion ({len(chat_msgs)} msgs)")
        for r in chat_msgs[-30:]:
            # r format: src_type, id, source_id, event_type, ts, headline, body
            source_raw = r[2] if len(r) > 2 else ''
            source = source_raw.split('-')[-1] if source_raw and '-' in source_raw else source_raw
            body = r[5] or r[6] or ''
            if len(body) > 200:
                body = body[:200] + '...'
            if body.strip():
                lines.append(f"[{source}] {body.strip()}")
    else:
        lines.append("\n## Chat Since Last Inversion")
        lines.append("(No new messages since last inversion)")

    return "\n".join(lines)

def call_grok(context):
    """Call Grok-4.20 via OpenRouter."""
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        return "[INVERSION ERROR] No OPENROUTER_API_KEY set"

    payload = {
        "model": "x-ai/grok-4.20",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": context}
        ],
        "max_tokens": 1024,
        "temperature": 0.9
    }

    try:
        import urllib.request
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/openclaw",
                "X-Title": "Kestrel Inversion Cron"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[INVERSION ERROR] API call failed: {e}"

def extract_key_claim(output):
    lines = output.strip().split("\n")
    for line in lines:
        line = line.strip()
        if line.startswith("### 1."):
            return line.replace("### 1.", "").strip()
        if line.startswith("**Severity:**"):
            return line.replace("**Severity:**", "").strip()
    return "See full output"

def save_inversion(output, key_claim):
    timestamp = datetime.now(timezone.utc).isoformat()
    STAGING.mkdir(parents=True, exist_ok=True)

    with open(LAST_INVERSION, "w") as f:
        json.dump({
            "timestamp": timestamp,
            "key_claim": key_claim,
            "challenge": output,
            "resolved": False
        }, f)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(STAGING / f"inversion_{ts}.md", "w") as f:
        f.write(output)

def main():
    context = build_context()
    output = call_grok(context)

    existing = list(STAGING.glob("inversion_*.md"))
    count = len(existing) + 1
    output = output.replace("{count}", str(count))

    key_claim = extract_key_claim(output)
    save_inversion(output, key_claim)

    # stdout → Hermes → Telegram
    print(output)

if __name__ == "__main__":
    main()