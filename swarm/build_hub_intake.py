"""
Build HUB_INTAKE.md — a daily-refreshed context file every agent loads on session start.

Sources:
  - memory-bank/SUMMARY.md (propositions + CTF results)
  - memory-bank/knowledge/noise-gate-context.md (kill/promote ratios)
  - agent-pulses/{today}/*.md (battle, keygame, CTF results)

Output: kestrel/HUB_INTAKE.md
"""
from __future__ import annotations

import re
import sys
from datetime import date, timezone, datetime
from pathlib import Path

KESTREL_ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = KESTREL_ROOT / "HUB_INTAKE.md"
SUMMARY_PATH = KESTREL_ROOT / "memory-bank" / "SUMMARY.md"
NOISE_CTX_PATH = KESTREL_ROOT / "memory-bank" / "knowledge" / "noise-gate-context.md"
PULSE_ROOT = KESTREL_ROOT / "agent-pulses"

MAX_SUMMARY_CHARS = 2000
MAX_NOISE_CHARS = 1200
MAX_PULSE_CHARS = 800
MAX_PULSE_FILES = 5


def _read_safe(path: Path, max_chars: int) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8").strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit("\n", 1)[0] + "\n_[truncated]_"


def _latest_pulses(today: str) -> list[tuple[str, str]]:
    pulse_dir = PULSE_ROOT / today
    if not pulse_dir.exists():
        return []
    files = sorted(pulse_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    results: list[tuple[str, str]] = []
    for f in files[:MAX_PULSE_FILES]:
        text = f.read_text(encoding="utf-8").strip()
        if len(text) > MAX_PULSE_CHARS:
            text = text[:MAX_PULSE_CHARS].rsplit("\n", 1)[0] + "\n_[truncated]_"
        results.append((f.name, text))
    return results


def build(today: str | None = None) -> str:
    if today is None:
        today = date.today().isoformat()

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    lines: list[str] = [
        f"# HUB_INTAKE — {today}",
        f"_Generated: {ts}_",
        "",
        "Load this file at session start to wake up with full pipeline context.",
        "",
    ]

    summary = _read_safe(SUMMARY_PATH, MAX_SUMMARY_CHARS)
    if summary:
        lines += ["## Memory Bank Summary", "", summary, ""]

    noise = _read_safe(NOISE_CTX_PATH, MAX_NOISE_CHARS)
    if noise:
        # Strip PURGE entries with "No significant markers found" — dead bytes
        noise = "\n".join(
            ln for ln in noise.split("\n")
            if not ln.strip().startswith("- PURGE")
            or "reason=No significant markers found" not in ln
        )
        lines += ["## Noise Gate Context (last 24h)", "", noise, ""]

    pulses = _latest_pulses(today)
    if pulses:
        lines += ["## Today's Pulses (newest first)", ""]
        for fname, content in pulses:
            lines += [f"### {fname}", "", content, ""]

    if not summary and not noise and not pulses:
        lines += ["_No context available yet today._", ""]

    return "\n".join(lines)


def main() -> None:
    today = sys.argv[1] if len(sys.argv) > 1 else None
    content = build(today)
    OUT_PATH.write_text(content, encoding="utf-8")
    print(f"HUB_INTAKE.md written ({len(content)} chars) -> {OUT_PATH}")


if __name__ == "__main__":
    main()
