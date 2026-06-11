#!/usr/bin/env python3
"""
feedback-collector.py

Observes agent outputs from event-bus.md and HUB_INTAKE.md, extracts
per-agent performance signals, and stores them to AgentMemory and DuckDB.

Design: purely observational — never generates new outputs, never triggers
actions. Runs as a systemd timer every 30 minutes.

Dependencies: pip install duckdb requests
"""

import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import requests

# ─── Configuration ───────────────────────────────────────────────────────
KESTREL_DIR = Path("/home/synczus/kestrel")
EVENT_BUS = KESTREL_DIR / "event-bus.md"
HUB_INTAKE = KESTREL_DIR / "HUB_INTAKE.md"
FEEDBACK_DB = Path(__file__).parent / "feedback.duckdb"

AGENTMEMORY_URL = os.environ.get("AGENTMEMORY_URL", "http://localhost:3111")
AGENTMEMORY_SECRET = os.environ.get("AGENTMEMORY_SECRET", "")

LOOP_COUNT = int(os.environ.get("FEEDBACK_LOOP_COUNT", "50"))
PIPELINE_LINE_LIMIT = int(os.environ.get("FEEDBACK_PIPELINE_LINES", "200"))

AGENTS = ["kestrelmarkets_bot", "nemoclaw", "kairos", "shannon", "hermes"]
AGENT_ALIASES = {
    "openclaw": "kestrelmarkets_bot",
    "kestrel": "kestrelmarkets_bot",
    "nemoclaw8364_bot": "nemoclaw",
    "kairos8638_bot": "kairos",
    "shannonrefereebot": "shannon",
    "codex": "hermes",
}


# ─── Helpers ─────────────────────────────────────────────────────────────
def agentmemory_headers():
    h = {"Content-Type": "application/json"}
    if AGENTMEMORY_SECRET:
        h["Authorization"] = f"Bearer {AGENTMEMORY_SECRET}"
    return h


def resolve_agent(name: str) -> str | None:
    """Normalize various agent name formats to canonical names."""
    raw = name.strip().lower()
    if raw in AGENT_ALIASES:
        return AGENT_ALIASES[raw]
    if raw.startswith("@"):
        raw = raw[1:]
    for alias, canonical in AGENT_ALIASES.items():
        if raw == alias or raw == canonical:
            return canonical
    # Fuzzy match against canonical names
    for canonical in AGENTS:
        if raw in canonical or canonical in raw:
            return canonical
    return None


def read_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"[feedback] ⚠ Could not read {path}: {e}", file=sys.stderr)
        return ""


def parse_timestamp(line: str) -> str | None:
    """Extract timestamp from various line formats used in the pipeline."""
    patterns = [
        r"\[(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2}))\]",
        r"^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})",
        r"\|\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})\s+\|",
    ]
    for pat in patterns:
        m = re.search(pat, line)
        if m:
            return m.group(1)
    return None


def extract_signals_from_event_bus(text: str) -> list[dict]:
    """Parse event-bus.md lines into structured agent feedback records."""
    signals = []
    lines = text.split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        ts = parse_timestamp(line)
        if not ts:
            continue

        # Detect agent mentions
        detected_agent = None
        for agent_canonical in AGENTS + list(AGENT_ALIASES.keys()):
            pattern = rf"(?i)\[?{re.escape(agent_canonical)}\]?"
            if re.search(pattern, line):
                resolved = resolve_agent(agent_canonical)
                if resolved:
                    detected_agent = resolved
                    break

        if not detected_agent:
            continue

        # Classify output type
        output_type = "signal"
        if re.search(r"\bHLM\b|highest.leverage", line, re.IGNORECASE):
            output_type = "HLM"
        elif re.search(r"\bpropos(?:e|al|ition)\b", line, re.IGNORECASE):
            output_type = "proposition"
        elif re.search(r"\bmonitor|health|uptime|audit\b", line, re.IGNORECASE):
            output_type = "monitor"
        elif re.search(r"\bexecut|run|cycle|trigger\b", line, re.IGNORECASE):
            output_type = "execution"
        elif re.search(r"\bcode|build|write|deploy\b", line, re.IGNORECASE):
            output_type = "build"
        elif re.search(r"\breview|audit|score|analyze\b", line, re.IGNORECASE):
            output_type = "analysis"
        elif re.search(r"\bfix|error|fail|recover\b", line, re.IGNORECASE):
            output_type = "recovery"

        # Extract context tags from line content
        tags = []
        topics = ["pipeline", "signal", "scouting", "coordination",
                   "market", "infrastructure", "cost", "monitoring",
                   "security", "vote", "code", "testing", "deploy"]
        for topic in topics:
            if topic in line.lower():
                tags.append(topic)

        # Infer quality score from signal characteristics
        score = 0.5  # neutral default
        if re.search(r"\bfixed|resolved|complete|deployed|success\b", line, re.IGNORECASE):
            score = 0.85
        elif re.search(r"\bfail|error|stale|broken|🔴|🔵\b", line, re.IGNORECASE):
            score = 0.3
        elif re.search(r"\bscored|ranked|analyzed\b", line, re.IGNORECASE):
            score = 0.75
        elif re.search(r"\bpropos|suggest|recommend\b", line, re.IGNORECASE):
            score = 0.65

        signals.append({
            "agent_name": detected_agent,
            "timestamp": str(datetime.now(timezone.utc)),
            "detected_from": str(ts),
            "output_type": output_type,
            "quality_score": score,
            "context_tags": ",".join(tags) if tags else "general",
            "raw_summary": line[:500],
            "source": "event-bus",
        })

    return signals


def extract_signals_from_hub_intake(text: str) -> list[dict]:
    """Parse HUB_INTAKE.md for agent propositions and performance signals."""
    signals = []
    lines = text.split("\n")
    in_propositions = False

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Detect propositions section
        if re.search(r"## Recent Propositions", line, re.IGNORECASE):
            in_propositions = True
            continue
        if re.search(r"## (Noise|Today|Memory)", line, re.IGNORECASE):
            in_propositions = False
            continue

        # Parse proposition lines like: `[hermes] [category] ...`
        prop_match = re.match(r"^`\[([^\]]+)\]`\s+\*{0,2}\[([^\]]*)\]\*{0,2}\s+(.*)", line)
        if prop_match:
            agent_raw = prop_match.group(1).lower().strip()
            category = prop_match.group(2).strip()
            summary = prop_match.group(3).strip()

            agent = resolve_agent(agent_raw)
            if not agent:
                continue

            # Determine output type based on category
            output_type = "signal"
            cat_lower = category.lower()
            if "infrastructure" in cat_lower:
                output_type = "build"
            elif "orchestration" in cat_lower:
                output_type = "proposition"
            elif "monitoring" in cat_lower or "observability" in cat_lower:
                output_type = "monitor"
            elif "optimization" in cat_lower or "cost" in cat_lower:
                output_type = "analysis"
            elif "security" in cat_lower:
                output_type = "analysis"

            score = 0.5
            if "🔴" in summary or "fail" in summary.lower():
                score = 0.25
            elif "🟢" in summary or "complete" in summary.lower():
                score = 0.9
            elif "🟡" in summary:
                score = 0.6

            tags = re.findall(r"\b\w+\b", category.replace("-", " "))
            tags = [t.lower() for t in tags if len(t) > 2]

            signals.append({
                "agent_name": agent,
                "timestamp": str(datetime.now(timezone.utc)),
                "detected_from": str(datetime.now(timezone.utc)),
                "output_type": output_type,
                "quality_score": score,
                "context_tags": ",".join(tags) if tags else "general",
                "raw_summary": summary[:500],
                "source": "hub_intake",
            })
            continue

        # Also detect lines with [agent][action] patterns
        agent_action_match = re.match(r"`?\[(\w+)\]`?\s*`?\[(\w+)\]`?\s*(.*)", line)
        if agent_action_match:
            agent_raw = agent_action_match.group(1).lower().strip()
            action = agent_action_match.group(2).strip()
            summary = agent_action_match.group(3).strip()
            agent = resolve_agent(agent_raw)
            if agent:
                signals.append({
                    "agent_name": agent,
                    "timestamp": str(datetime.now(timezone.utc)),
                    "detected_from": str(datetime.now(timezone.utc)),
                    "output_type": action,
                    "quality_score": 0.5,
                    "context_tags": "general",
                    "raw_summary": summary[:500],
                    "source": "hub_intake",
                })

    return signals


# ─── AgentMemory Storage ─────────────────────────────────────────────────
def store_to_agentmemory(signals: list[dict]) -> int:
    """Write each signal to AgentMemory via POST /agentmemory/remember."""
    stored = 0
    for sig in signals:
        content = json.dumps({
            "type": "agent_feedback",
            "agent": sig["agent_name"],
            "ts": sig["timestamp"],
            "output_type": sig["output_type"],
            "score": sig["quality_score"],
            "tags": sig["context_tags"],
            "summary": sig["raw_summary"],
        })
        try:
            resp = requests.post(
                f"{AGENTMEMORY_URL}/agentmemory/remember",
                headers=agentmemory_headers(),
                json={"content": content},
                timeout=5,
            )
            if resp.ok:
                stored += 1
        except requests.RequestException as e:
            print(f"[feedback] ⚠ AgentMemory write failed: {e}", file=sys.stderr)
    return stored


# ─── DuckDB Storage ──────────────────────────────────────────────────────
def init_duckdb():
    """Create the agent_feedback table if it doesn't exist."""
    conn = duckdb.connect(str(FEEDBACK_DB))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS agent_feedback (
            id UUID PRIMARY KEY,
            agent VARCHAR NOT NULL,
            timestamp TIMESTAMPTZ NOT NULL,
            output_type VARCHAR NOT NULL,
            quality_score DOUBLE PRECISION,
            context_tags VARCHAR,
            raw_summary TEXT,
            source VARCHAR DEFAULT 'event-bus',
            ingested_at TIMESTAMPTZ DEFAULT now()
        )
    """)
    # Create index for agent queries
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_feedback_agent
        ON agent_feedback (agent, timestamp DESC)
    """)
    conn.close()


def store_to_duckdb(signals: list[dict]) -> int:
    """Write each signal to DuckDB for queryable history."""
    stored = 0
    conn = duckdb.connect(str(FEEDBACK_DB))
    try:
        for sig in signals:
            conn.execute(
                """
                INSERT INTO agent_feedback (id, agent, timestamp, output_type,
                                            quality_score, context_tags,
                                            raw_summary, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    str(uuid.uuid4()),
                    sig["agent_name"],
                    sig["timestamp"],
                    sig["output_type"],
                    sig["quality_score"],
                    sig["context_tags"],
                    sig["raw_summary"],
                    sig.get("source", "event-bus"),
                ],
            )
            stored += 1
        conn.commit()
    finally:
        conn.close()
    return stored


# ─── Main ────────────────────────────────────────────────────────────────
def main():
    print("[feedback] Starting agent feedback collection cycle...", flush=True)

    # 1. Ensure DuckDB schema
    init_duckdb()

    # 2. Read pipeline sources
    event_text = read_file(EVENT_BUS)
    intake_text = read_file(HUB_INTAKE)

    if not event_text and not intake_text:
        print("[feedback] ⚠ No pipeline sources available", file=sys.stderr)
        return

    # 3. Extract signals
    signals = []
    if event_text:
        signals.extend(extract_signals_from_event_bus(event_text))
    if intake_text:
        signals.extend(extract_signals_from_hub_intake(intake_text))

    # Deduplicate by summary+agent
    seen = set()
    unique_signals = []
    for sig in signals:
        key = (sig["agent_name"], sig["raw_summary"][:100])
        if key not in seen:
            seen.add(key)
            unique_signals.append(sig)
    signals = unique_signals

    print(f"[feedback] Extracted {len(signals)} unique agent signals", flush=True)

    if not signals:
        print("[feedback] No new signals to store", flush=True)
        return

    # 4. Store to AgentMemory
    am_count = store_to_agentmemory(signals)
    print(f"[feedback] Stored {am_count}/{len(signals)} to AgentMemory", flush=True)

    # 5. Store to DuckDB
    db_count = store_to_duckdb(signals)
    print(f"[feedback] Stored {db_count}/{len(signals)} to DuckDB ({FEEDBACK_DB})", flush=True)

    # 6. Print per-agent summary
    agent_counts = {}
    for sig in signals:
        agent_counts[sig["agent_name"]] = agent_counts.get(sig["agent_name"], 0) + 1
    print(f"[feedback] Per-agent: {json.dumps(agent_counts)}", flush=True)


if __name__ == "__main__":
    main()