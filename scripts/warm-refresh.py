#!/usr/bin/env python3
"""
warm-refresh.py — Refresh warm memory + cross-agent context
Runs every hour via cron. Writes session context files for all agents
so every boot-up has recent context.

Outputs:
  memory-bank/warm/{agent}.md  — per-agent session briefings
  knowledge/chat-digest.md     — last 4h highlights for all agents
"""

import json, os, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

WARM_DIR = Path("/home/synczus/kestrel/memory-bank/warm")
KNOWLEDGE_DIR = Path("/home/synczus/kestrel/knowledge")
PROJECT_DIR = Path("/home/synczus/kestrel")

AGENTS = {
    "openclaw": "OpenClaw — config/infra/gateway — @kestrelmarkets_bot",
    "hermes": "Hermes — cron/execution/orchestration",
    "kairos": "Kairos — timing/ops/scouting — @Kairos8638_bot",
    "shannon": "Shannon — referee/code review — @ShannonRefereeBot",
    "nemoclaw": "Nemoclaw — identity/architecture — @Nemoclaw8364_bot",
}

def get_service_status():
    """Check gateway + service states for all agents."""
    status = {}
    for agent in AGENTS:
        svc_map = {
            "openclaw": "openclaw-gateway",
            "hermes": "hermes-gateway",
            "kairos": "kairos-gateway",
            "shannon": "shannon-gateway",
            "nemoclaw": "openclaw-nemoclaw",
        }
        try:
            result = subprocess.run(
                ["systemctl", "--user", "show", "-p", "ActiveState", svc_map[agent]],
                capture_output=True, text=True, timeout=5
            )
            status[agent] = result.stdout.strip().replace("ActiveState=", "")
        except:
            status[agent] = "unknown"

    # Also check freqtrade + striker
    try:
        r = subprocess.run(["systemctl", "--user", "show", "-p", "ActiveState", "freqtrade-coinbase.service"],
                          capture_output=True, text=True, timeout=5)
        status["freqtrade"] = r.stdout.strip().replace("ActiveState=", "")
    except:
        status["freqtrade"] = "unknown"

    try:
        r = subprocess.run(["systemctl", "--user", "show", "-p", "ActiveState", "kestrel-striker.service"],
                          capture_output=True, text=True, timeout=5)
        status["striker"] = r.stdout.strip().replace("ActiveState=", "")
    except:
        status["striker"] = "unknown"

    return status

def read_knowledge(knowledge_file):
    """Read first 100 lines of a knowledge file for digest."""
    path = KNOWLEDGE_DIR / knowledge_file
    if not path.exists():
        return "(no data)"
    content = path.read_text()
    lines = content.split("\n")
    # Extract key entries (anything that looks like a 1. 2. 3. list item)
    highlights = [l.strip() for l in lines if l.strip().startswith(("1.", "2.", "3.", "##", "- **"))]
    return "\n".join(highlights[:30]) or "(summary)"

def write_warm_memory(agent, status_map):
    """Write a warm memory file for one agent."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    gateway = status_map.get(agent, "unknown")

    content = f"""# {agent.title()} — Warm Memory
_Refreshed: {now}_

## Status
- Gateway: {gateway}
- Role: {AGENTS[agent]}

## Recent Context
"""
    # Add recent knowledge highlights
    for kf in ["chat-decisions.md", "chat-config-details.md", "chat-signals.md"]:
        path = KNOWLEDGE_DIR / kf
        if path.exists():
            content += f"\n### From {kf}\n"
            highlights = path.read_text().split("\n")[:15]
            content += "\n".join(highlights[:15]) + "\n"

    WARM_DIR.mkdir(parents=True, exist_ok=True)
    (WARM_DIR / f"{agent}.md").write_text(content)

def write_digest(status_map):
    """Write cross-agent digest."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [f"# Cross-Agent Digest — {now}", ""]

    # Services overview
    lines.append("## Service Status")
    for name, state in sorted(status_map.items()):
        icon = "✅" if state == "active" else "❌" if state == "inactive" else "⚠️"
        lines.append(f"- {icon} {name}: {state}")

    # Check for any changes
    lines.append("")
    lines.append("## Key Knowledge")
    for kf in ["chat-decisions.md", "chat-signals.md", "chat-config-details.md"]:
        path = KNOWLEDGE_DIR / kf
        if path.exists():
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            lines.append(f"- {kf}: updated {mtime.strftime('%H:%M UTC')}")

    # Quick pipeline state
    pending = PROJECT_DIR / "dashboard/pending.json"
    if pending.exists():
        try:
            signals = json.loads(pending.read_text())
            chart_sigs = [s for s in signals if isinstance(s, dict) and s.get("type") == "chart_analysis"]
            if chart_sigs:
                last = chart_sigs[-1]
                lines.append(f"\n- Latest chart signal: {last.get('bias')} on {last.get('symbol','?')} conf={last.get('confidence')}")
                lines.append(f"  {last.get('summary','')[:80]}")
        except:
            pass

    # Budget check
    or_budget = PROJECT_DIR / "dashboard/or-budget-state.json"
    if or_budget.exists():
        try:
            b = json.loads(or_budget.read_text())
            lines.append(f"\n- OR budget: ${b.get('daily','?')} / day")
        except:
            pass

    content = "\n".join(lines)
    (KNOWLEDGE_DIR / "chat-digest.md").write_text(content)

    # Also update warm memory for OpenClaw (primary agent)
    write_warm_memory("openclaw", status_map)

def main():
    WARM_DIR.mkdir(parents=True, exist_ok=True)
    status_map = get_service_status()

    # Write warm memory for all agents
    for agent in AGENTS:
        write_warm_memory(agent, status_map)

    # Write cross-agent digest
    write_digest(status_map)

    print(f"Warm memory refreshed for {len(AGENTS)} agents + digest")
    print(f"Services: {', '.join(f'{k}={v}' for k,v in status_map.items())}")

if __name__ == "__main__":
    main()