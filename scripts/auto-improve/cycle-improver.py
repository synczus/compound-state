#!/usr/bin/env python3
"""
cycle-improver.py

Read-side script that agents call at session start to get a brief improvement
context string. Detects patterns (topic convergence, gaps) and returns
2-3 sentences of actionable context.

Usage:
    python3 cycle-improver.py --agent kairos
    python3 cycle-improver.py --agent nemoclaw --format json

Output is a lightweight string injected into the agent's next cycle, or
a JSON object with detailed analysis.

Dependencies: pip install duckdb requests
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import duckdb
import requests

# ─── Configuration ───────────────────────────────────────────────────────
KESTREL_DIR = Path("/home/synczus/kestrel")
FEEDBACK_DB = Path(__file__).parent / "feedback.duckdb"
AGENTMEMORY_URL = os.environ.get("AGENTMEMORY_URL", "http://localhost:3111")
AGENTMEMORY_SECRET = os.environ.get("AGENTMEMORY_SECRET", "")

# Topics that agent lanes should cover
LANE_TOPICS = {
    "kestrelmarkets_bot": ["config", "gateway", "model", "systemd", "service"],
    "nemoclaw": ["identity", "soul", "skill", "docs", "personality", "architecture"],
    "kairos": ["scouting", "signal", "security", "audit", "timing", "ops", "pipeline"],
    "shannon": ["review", "code", "analysis", "scoring", "arbitration", "testing"],
    "hermes": ["cron", "execution", "coordination", "striker", "hop", "monitoring"],
}

LANE_DISPLAY = {
    "kestrelmarkets_bot": "Config/Ops",
    "nemoclaw": "Identity/Build",
    "kairos": "Timing/Ops",
    "shannon": "Referee",
    "hermes": "Cron/Execution",
}


# ─── Helpers ─────────────────────────────────────────────────────────────
def agentmemory_headers():
    h = {"Content-Type": "application/json"}
    if AGENTMEMORY_SECRET:
        h["Authorization"] = f"Bearer {AGENTMEMORY_SECRET}"
    return h


def get_recent_from_agentmemory(agent: str, limit: int = 10) -> list[dict]:
    """Query AgentMemory for recent entries from a specific agent."""
    try:
        resp = requests.post(
            f"{AGENTMEMORY_URL}/agentmemory/search",
            headers=agentmemory_headers(),
            json={"query": agent, "limit": limit * 3},  # overfetch for filtering
            timeout=5,
        )
        if not resp.ok:
            return []

        data = resp.json()
        results = []
        for r in data.get("results", []):
            obs = r.get("observation", {})
            # Try to parse the stored content as JSON to check agent match
            content_str = ""
            facts = obs.get("facts", [])
            if facts:
                content_str = facts[0]
            elif obs.get("narrative"):
                content_str = obs.get("narrative", "")

            try:
                parsed = json.loads(content_str)
                if isinstance(parsed, dict) and parsed.get("agent") == agent:
                    results.append({
                        "id": obs.get("id", ""),
                        "timestamp": obs.get("timestamp", ""),
                        "output_type": parsed.get("output_type", "unknown"),
                        "score": parsed.get("score", 0.5),
                        "tags": parsed.get("tags", ""),
                        "summary": parsed.get("summary", ""),
                    })
            except (json.JSONDecodeError, TypeError):
                continue

        return results[:limit]
    except requests.RequestException as e:
        print(f"[cycle-improver] ⚠ AgentMemory query failed: {e}", file=sys.stderr)
        return []


def get_recent_from_duckdb(agent: str, limit: int = 10) -> list[dict]:
    """Query DuckDB for recent agent feedback."""
    try:
        conn = duckdb.connect(str(FEEDBACK_DB))
        rows = conn.execute(
            """
            SELECT agent, timestamp, output_type, quality_score,
                   context_tags, raw_summary
            FROM agent_feedback
            WHERE agent = ?
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            [agent, limit],
        ).fetchall()
        conn.close()
        return [
            {
                "agent": r[0],
                "timestamp": str(r[1]),
                "output_type": r[2],
                "score": r[3],
                "tags": r[4],
                "summary": r[5],
            }
            for r in rows
        ]
    except Exception as e:
        print(f"[cycle-improver] ⚠ DuckDB query failed: {e}", file=sys.stderr)
        return []


def detect_topic_convergence(recent: list[dict]) -> str | None:
    """Detect if last N outputs focused on the same topic."""
    if len(recent) < 3:
        return None
    last_3 = recent[:3]
    tag_sets = [set(s["tags"].split(",")) for s in last_3]
    common_tags = set.intersection(*tag_sets) if len(tag_sets) > 1 else tag_sets[0]
    # Filter out general tags
    common_tags = {t for t in common_tags if t not in ("general", "")}
    if len(common_tags) >= 1:
        topic = list(common_tags)[0]
        if len(recent) >= 5 and all(topic in s["tags"] for s in recent[:5]):
            return (
                f"⚠ Deep focus: last 5 outputs all on '{topic}'. "
                f"Consider diversifying across other lane topics."
            )
        return (
            f"📌 Convergence: last 3 outputs center on '{topic}'. "
            f"Good momentum — check if there's a next step or wrap up."
        )
    return None


def detect_gaps(agent: str, recent: list[dict]) -> str | None:
    """Detect if the agent hasn't covered expected topics in 24h."""
    lane_topics = LANE_TOPICS.get(agent, [])
    now = datetime.now(timezone.utc)
    cutoff_24h = now - timedelta(hours=24)

    # Collect topics covered in the last 24h
    covered_topics = set()
    for sig in recent:
        try:
            ts = datetime.fromisoformat(sig["timestamp"].replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            continue
        if ts >= cutoff_24h:
            tags = sig.get("tags", "").split(",")
            covered_topics.update(t.strip() for t in tags)

    missing = [t for t in lane_topics if t not in covered_topics]
    if missing:
        return (
            f"🔎 Gap detected: no '{', '.join(missing)}' "
            f"output in the last 24h. Recommend scoping one of these."
        )
    return None


def detect_quality_trend(recent: list[dict]) -> str | None:
    """Check if quality scores are trending up or down."""
    if len(recent) < 3:
        return None
    scores = [s["score"] for s in recent[:5] if "score" in s]
    if len(scores) < 3:
        return None
    avg_recent = sum(scores[:3]) / len(scores[:3])
    avg_older = sum(scores) / len(scores)
    diff = avg_recent - avg_older
    if diff > 0.1:
        return f"📈 Quality trending up (+{diff:.2f}) — pattern working."
    elif diff < -0.1:
        return f"📉 Quality dip ({diff:.2f}) — check recent outputs for issues."
    return None


def build_improvement_context(agent: str, format_json: bool = False) -> str | dict:
    """Main function: returns improvement context for an agent."""
    agent_canonical = agent
    lane_name = LANE_DISPLAY.get(agent_canonical, agent_canonical)

    # Try AgentMemory first, fall back to DuckDB
    recent = get_recent_from_agentmemory(agent_canonical, limit=10)
    if not recent:
        recent = get_recent_from_duckdb(agent_canonical, limit=10)

    findings = []

    # Pattern detection
    convergence = detect_topic_convergence(recent)
    if convergence:
        findings.append(convergence)

    gap = detect_gaps(agent_canonical, recent)
    if gap:
        findings.append(gap)

    quality = detect_quality_trend(recent)
    if quality:
        findings.append(quality)

    # Build context string
    if not findings:
        context = (
            f"{lane_name}: No improvement signals detected. "
            f"Proceed with lane priorities."
        )
    else:
        context = (
            f"{lane_name} improvement context — {len(findings)} signal(s): "
            + " | ".join(findings)
        )

    if format_json:
        # Count by output type
        type_counts = {}
        for s in recent:
            t = s.get("output_type", "unknown")
            type_counts[t] = type_counts.get(t, 0) + 1

        return {
            "agent": agent_canonical,
            "lane": lane_name,
            "recent_outputs_count": len(recent),
            "output_type_distribution": type_counts,
            "findings": findings,
            "context": context,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    return context


# ─── CLI ─────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Cycle improver — agent session start")
    parser.add_argument("--agent", required=True, help="Agent name to analyze")
    parser.add_argument("--format", choices=["text", "json"], default="text",
                        help="Output format (default: text)")
    args = parser.parse_args()

    context = build_improvement_context(
        args.agent,
        format_json=(args.format == "json"),
    )

    if isinstance(context, dict):
        print(json.dumps(context, indent=2))
    else:
        print(context)


if __name__ == "__main__":
    main()