#!/usr/bin/env python3
"""
One-shot hop: Telegram AI Hangout → Perplexity (research) → Grok (analysis).

- Pulls recent context from the AI Hangout (DuckDB signals preferred, fallback to local chat-history.json).
- Runs Perplexity (sonar-pro) for grounded research on the discussion.
- Feeds results + context to Grok for adversarial synthesis + implications.
- AUTO-INGESTS the full agent responses (Perplexity + Grok) into the compound:
    * Structured hop dir under hops/telegram-ai-hangout-perplexity-grok/<ts>/
    * Appends to memory-bank/knowledge/hangout-hops.md (portable knowledge)
    * Writes staging/ artifact for HUB_INTAKE / agent pickup
- Works across environments (relative paths from script, standard kestrel layout).
- Pure one-shot: run manually or trigger from chat when needed.

Usage:
  python3 one-shot-hangout-perplexity-grok.py                 # latest hangout context
  python3 one-shot-hangout-perplexity-grok.py "your seed question or topic from the chat"

Requires OPENROUTER_API_KEY (falls back to ~/.hermes/.env).
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────────────
# Paths (portable across environments: huntsystems, kestrel, etc.)
# ──────────────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
KESTREL_ROOT = SCRIPT_DIR.parent
HOPS_DIR = KESTREL_ROOT / "hops" / "telegram-ai-hangout-perplexity-grok"
MEMORY_KNOWLEDGE = KESTREL_ROOT / "memory-bank" / "knowledge"
STAGING_DIR = KESTREL_ROOT / "staging"
DATA_DIR = KESTREL_ROOT / "data"
SIGNALS_DB = KESTREL_ROOT / "signals.duckdb"
CHAT_HISTORY = DATA_DIR / "chat-history.json"

HANGOUT_SOURCE_ID = "%AIHangout%"
GROUP_CHAT_ID = "-5087043705"

# OpenRouter
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
if not OPENROUTER_API_KEY:
    for env_path in [
        Path.home() / ".hermes" / ".env",
        KESTREL_ROOT / ".env",
    ]:
        if env_path.exists():
            try:
                for line in env_path.read_text().splitlines():
                    if line.strip().startswith("OPENROUTER_API_KEY="):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if val and val != "YOUR_KEY_HERE":
                            OPENROUTER_API_KEY = val
                            break
            except Exception:
                pass
            if OPENROUTER_API_KEY:
                break

if not OPENROUTER_API_KEY:
    print("ERROR: OPENROUTER_API_KEY not found (env or ~/.hermes/.env)", file=sys.stderr)
    sys.exit(1)

# Models for this hop (research + sharp analysis)
PERPLEXITY_MODEL = "perplexity/sonar-pro"
GROK_MODEL = "x-ai/grok-2-1212"  # Strong Grok model on OpenRouter; change if needed

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def now_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")

def read_json_safe(path: Path) -> dict | list:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {} if path.suffix == ".json" else []

def get_recent_hangout_context(max_messages: int = 20, max_age_hours: int = 6) -> str:
    """
    Best-effort recent AI Hangout context.
    1. DuckDB signals (real-time ingested chat) — preferred.
    2. Fallback to local chat-history.json (hermes + user messages).
    """
    messages = []
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=max_age_hours)).isoformat()

    # Try DuckDB first (used by inversion-cron and ingestion)
    if SIGNALS_DB.exists():
        try:
            import duckdb
            con = duckdb.connect(str(SIGNALS_DB), read_only=True)
            rows = con.execute("""
                SELECT ingested_at, headline, body_text, source_id
                FROM signals
                WHERE source_id LIKE ?
                  AND event_type NOT IN ('reaction', 'edit')
                  AND ingested_at >= ?
                ORDER BY ingested_at DESC
                LIMIT ?
            """, (HANGOUT_SOURCE_ID, cutoff, max_messages)).fetchall()
            con.close()
            for r in reversed(rows):  # chronological
                ts, headline, body, src = r
                text = (headline or "") + " " + (body or "")
                if text.strip():
                    messages.append(f"[{ts}] {text.strip()[:600]}")
        except Exception as e:
            print(f"[context] DuckDB fallback: {e}", file=sys.stderr)

    # Fallback to chat-history.json (session chat dumps)
    if not messages and CHAT_HISTORY.exists():
        try:
            history = read_json_safe(CHAT_HISTORY)
            if isinstance(history, list):
                # Prefer non-hermes (human + other agents) for "discussion"
                recent = [h for h in history if "hermes" not in str(h.get("source", "")).lower()]
                for item in recent[-max_messages:]:
                    content = item.get("content", "")
                    dt = item.get("dt", "")
                    if content and len(content) > 10:
                        messages.append(f"[{dt}] {content.strip()[:600]}")
        except Exception as e:
            print(f"[context] chat-history fallback: {e}", file=sys.stderr)

    if not messages:
        return "No recent AI Hangout context found (DuckDB or chat-history.json)."

    header = f"Recent AI Hangout discussion (last ~{max_age_hours}h, up to {max_messages} msgs):\n"
    return header + "\n".join(messages[-max_messages:])

def call_openrouter(model: str, prompt: str, max_tokens: int = 2500) -> dict:
    """Direct OpenRouter call (same style as perplexity_search.py for portability)."""
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.3,
    }).encode()

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/synczus/kestrel",
            "X-Title": "Kestrel One-Shot Hangout Hop",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode())
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return {
            "model": model,
            "content": content,
            "usage": usage,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:500]
        raise RuntimeError(f"OpenRouter HTTP {e.code}: {body}")
    except Exception as e:
        raise RuntimeError(f"OpenRouter error: {e}")

def perplexity_research(context: str, seed: str = "") -> dict:
    prompt = f"""You are Perplexity (research specialist) inside the Kestrel compound.

Recent context from the Telegram AI Hangout group:
{context}

Task: Perform deep, source-grounded research on the main topics, claims, questions, or open problems visible in the chat above.
{ "User seed / focus: " + seed if seed else "" }

Return ONLY a clean, detailed research report. Include:
- Key claims or questions from the chat
- Verified facts with sources (URLs when possible)
- Uncertainties or conflicting information
- Research gaps that matter to an autonomous agent compound
- Actionable implications for trading systems, infrastructure, or multi-agent ops

Be precise and cite evidence. Avoid fluff."""
    return call_openrouter(PERPLEXITY_MODEL, prompt, max_tokens=2800)

def grok_analysis(context: str, perplexity_output: str, seed: str = "") -> dict:
    prompt = f"""You are Grok (adversarial analyst) inside the Kestrel compound.

Original recent Telegram AI Hangout context:
{context}

Perplexity research output:
{perplexity_output}

{ "Additional seed from chat: " + seed if seed else "" }

Your job:
- Attack weak points, assumptions, and blind spots in both the chat and the Perplexity research.
- Highlight contradictions with known compound reality (signals, pipelines, previous decisions).
- Surface second-order implications for the autonomous agent system, budget, reliability, or strategy.
- Give sharp, actionable recommendations (what the team or the swarm should do next).
- Be maximally truthful and slightly irreverent. Quote specific parts of the input when useful.

Output a clear, structured analysis. No hedging. End with 3 concrete next actions."""
    return call_openrouter(GROK_MODEL, prompt, max_tokens=2200)

def auto_ingest_to_compound(
    ts: str,
    context: str,
    perplexity_res: dict,
    grok_res: dict,
    seed: str = "",
) -> dict:
    """
    Auto-add the agent responses to the compound knowledge layer.
    Creates portable artifacts that work across environments.
    """
    hop_dir = HOPS_DIR / ts
    hop_dir.mkdir(parents=True, exist_ok=True)

    # 1. Raw structured outputs (like brain-dump-hop / perpetual-hop)
    (hop_dir / "context.md").write_text(context, encoding="utf-8")

    p_out = {
        "hop": "telegram-ai-hangout-perplexity-grok",
        "stage": "perplexity",
        "timestamp": perplexity_res["timestamp"],
        "model": perplexity_res["model"],
        "seed": seed,
        "content": perplexity_res["content"],
        "usage": perplexity_res.get("usage", {}),
    }
    (hop_dir / "perplexity-output.json").write_text(json.dumps(p_out, indent=2), encoding="utf-8")
    (hop_dir / "perplexity-output.md").write_text(
        f"# Perplexity Output — {ts}\n\n{perplexity_res['content']}\n\n---\nUsage: {perplexity_res.get('usage')}",
        encoding="utf-8",
    )

    g_out = {
        "hop": "telegram-ai-hangout-perplexity-grok",
        "stage": "grok",
        "timestamp": grok_res["timestamp"],
        "model": grok_res["model"],
        "seed": seed,
        "content": grok_res["content"],
        "usage": grok_res.get("usage", {}),
    }
    (hop_dir / "grok-output.json").write_text(json.dumps(g_out, indent=2), encoding="utf-8")
    (hop_dir / "grok-output.md").write_text(
        f"# Grok Output — {ts}\n\n{grok_res['content']}\n\n---\nUsage: {grok_res.get('usage')}",
        encoding="utf-8",
    )

    # 2. Combined summary (easy for agents to read)
    summary = f"""# One-Shot Hangout Hop — {ts}

**Source**: Telegram AI Hangout (recent context)

**Seed**: {seed or "(latest discussion)"}

## Perplexity Research
{perplexity_res['content'][:4000]}

## Grok Analysis
{grok_res['content'][:4000]}

**Artifacts**:
- {hop_dir / 'perplexity-output.json'}
- {hop_dir / 'grok-output.json'}
"""
    (hop_dir / "summary.md").write_text(summary, encoding="utf-8")

    # 3. Auto-add to portable compound knowledge
    MEMORY_KNOWLEDGE.mkdir(parents=True, exist_ok=True)
    knowledge_file = MEMORY_KNOWLEDGE / "hangout-hops.md"
    entry = f"""

## {ts} — Hangout → Perplexity → Grok

**Context snippet**:
```
{context[:1500]}
```

**Perplexity key output** (truncated):
{perplexity_res['content'][:1200]}...

**Grok key output** (truncated):
{grok_res['content'][:1200]}...

**Hop dir**: {hop_dir}
"""
    with open(knowledge_file, "a", encoding="utf-8") as f:
        f.write(entry)

    # 4. Staging artifact for HUB_INTAKE / build_hub_intake pickup
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    staging_file = STAGING_DIR / f"hangout-hop-{ts}.md"
    staging_file.write_text(summary + f"\n\nFull hop directory: {hop_dir}\n", encoding="utf-8")

    # 5. Optional: light DuckDB event (best-effort, non-fatal)
    try:
        import duckdb
        con = duckdb.connect(str(SIGNALS_DB))
        con.execute("""
            CREATE TABLE IF NOT EXISTS events (
                row_id INTEGER,
                ingested_ts TIMESTAMP,
                source_id TEXT,
                event_type TEXT,
                payload_headline TEXT,
                payload_body TEXT
            )
        """)
        con.execute("""
            INSERT INTO events (ingested_ts, source_id, event_type, payload_headline, payload_body)
            VALUES (?, 'compound/hop', 'hangout-perplexity-grok', ?, ?)
        """, (
            datetime.now(timezone.utc),
            f"Hangout hop {ts}",
            json.dumps({"perplexity_model": perplexity_res["model"], "grok_model": grok_res["model"], "dir": str(hop_dir)}),
        ))
        con.close()
    except Exception:
        pass  # Ingestion is best-effort for one-shot

    return {
        "hop_dir": str(hop_dir),
        "knowledge_file": str(knowledge_file),
        "staging_file": str(staging_file),
        "perplexity_cost_hint": perplexity_res.get("usage"),
        "grok_cost_hint": grok_res.get("usage"),
    }

# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    seed = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else ""

    print("=== One-Shot Hangout → Perplexity → Grok Hop ===")
    print(f"Seed: {seed or '(latest hangout context)'}")

    print("\n[1/4] Collecting recent AI Hangout context...")
    context = get_recent_hangout_context()
    print(f"Context length: {len(context)} chars")

    ts = now_ts()
    print(f"\n[2/4] Running Perplexity research ({PERPLEXITY_MODEL})...")
    p_res = perplexity_research(context, seed)
    print("Perplexity complete.")

    print(f"\n[3/4] Running Grok analysis ({GROK_MODEL})...")
    g_res = grok_analysis(context, p_res["content"], seed)
    print("Grok complete.")

    print("\n[4/4] Auto-ingesting responses into compound...")
    ingest_result = auto_ingest_to_compound(ts, context, p_res, g_res, seed)

    print("\n=== DONE ===")
    print(f"Hop artifacts: {ingest_result['hop_dir']}")
    print(f"Knowledge appended: {ingest_result['knowledge_file']}")
    print(f"Staging for HUB: {ingest_result['staging_file']}")
    print("\nNext agent load (or manual HUB_INTAKE refresh) will see the new research + analysis.")
    print("The outputs are now part of the compound across environments.")

if __name__ == "__main__":
    main()
