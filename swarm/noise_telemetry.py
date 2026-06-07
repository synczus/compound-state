"""
Noise gate telemetry and context export.

This is intentionally local and cheap: every gate decision is appended to JSONL,
then a compact markdown context is regenerated for AutoHOP agents.
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


KESTREL_ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_DIR = KESTREL_ROOT / "memory-bank" / "knowledge"
EVENTS_PATH = KNOWLEDGE_DIR / "noise-gate-events.jsonl"
CONTEXT_PATH = KNOWLEDGE_DIR / "noise-gate-context.md"
PULSE_ROOT = KESTREL_ROOT / "agent-pulses"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _safe_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, value in metadata.items():
        if any(token in key.lower() for token in ("secret", "token", "key", "password")):
            safe[key] = "<redacted>"
        elif isinstance(value, (str, int, float, bool)) or value is None:
            safe[key] = value
        else:
            safe[key] = str(value)[:240]
    return safe


def _read_recent_events(limit: int = 200) -> list[dict[str, Any]]:
    if not EVENTS_PATH.exists():
        return []
    lines = EVENTS_PATH.read_text(encoding="utf-8").splitlines()[-limit:]
    events: list[dict[str, Any]] = []
    for line in lines:
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def _write_context(events: list[dict[str, Any]]) -> None:
    now = _utc_now()
    cutoff = now - timedelta(hours=24)

    last_24h = []
    for event in events:
        try:
            ts = datetime.fromisoformat(str(event["timestamp"]).replace("Z", "+00:00"))
        except (KeyError, ValueError):
            continue
        if ts >= cutoff:
            last_24h.append(event)

    decision_counts = Counter(event.get("decision", "UNKNOWN") for event in last_24h)
    reason_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    for event in last_24h:
        source_counts[str(event.get("source", "unknown"))] += 1
        for reason in str(event.get("reasoning", "")).split(";"):
            reason = reason.strip()
            if reason:
                reason_counts[reason] += 1

    recent = events[-12:]

    lines = [
        "# Noise Gate Context",
        "",
        f"_Generated: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}_",
        "",
        "## Last 24h",
        "",
        f"- PROMOTE: {decision_counts.get('PROMOTE', 0)}",
        f"- PURGE: {decision_counts.get('PURGE', 0)}",
        f"- Total: {len(last_24h)}",
        "",
        "## Top Reasons",
        "",
    ]
    if reason_counts:
        for reason, count in reason_counts.most_common(8):
            lines.append(f"- {reason}: {count}")
    else:
        lines.append("- No decisions recorded yet")

    lines.extend(["", "## Sources", ""])
    if source_counts:
        for source, count in source_counts.most_common(8):
            lines.append(f"- {source}: {count}")
    else:
        lines.append("- No sources recorded yet")

    lines.extend(["", "## Recent Decisions", ""])
    if recent:
        for event in reversed(recent):
            preview = str(event.get("content_preview", "")).replace("\n", " ")[:120]
            lines.append(
                "- {decision} score={score} source={source} reason={reason} preview={preview}".format(
                    decision=event.get("decision", "UNKNOWN"),
                    score=event.get("score", "?"),
                    source=event.get("source", "unknown"),
                    reason=str(event.get("reasoning", ""))[:120],
                    preview=preview,
                )
            )
    else:
        lines.append("- No recent decisions")

    lines.extend(
        [
            "",
            "## Agent Use",
            "",
            "- Use PROMOTE/PURGE ratios to avoid repeating dead signal patterns.",
            "- If a source is repeatedly purged, demand stronger evidence or actionability.",
            "- If a reason repeatedly promotes, preserve that marker in future routing.",
        ]
    )

    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    CONTEXT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    pulse_dir = PULSE_ROOT / now.strftime("%Y-%m-%d")
    pulse_dir.mkdir(parents=True, exist_ok=True)
    (pulse_dir / "noise-gate-context.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def record_noise_gate_decision(
    *,
    input_id: str,
    source: str,
    content: str,
    score: int,
    threshold: int,
    is_noise: bool,
    reasoning: str,
    metadata: dict[str, Any],
) -> None:
    """Append one gate decision and refresh compact context."""
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": _utc_now().isoformat().replace("+00:00", "Z"),
        "input_id": input_id,
        "source": source,
        "decision": "PURGE" if is_noise else "PROMOTE",
        "score": score,
        "threshold": threshold,
        "reasoning": reasoning,
        "content_preview": content[:280],
        "metadata": _safe_metadata(metadata),
    }
    with EVENTS_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, sort_keys=True) + "\n")
    _write_context(_read_recent_events())


def get_noise_gate_context(max_chars: int = 2400) -> str:
    """Return compact context for agent prompts."""
    if not CONTEXT_PATH.exists():
        return ""
    text = CONTEXT_PATH.read_text(encoding="utf-8").strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit("\n", 1)[0] + "\n- Context truncated"
