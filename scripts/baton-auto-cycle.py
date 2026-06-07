#!/usr/bin/env python3
"""
Baton Auto-Cycle — when a cycle completes, immediately start the next P0.
No human needed to unpark. Runs every 15 minutes.
"""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BATON = Path("/home/synczus/kestrel/active-baton.json")
TODO = Path("/home/synczus/kestrel/master-todo.md")
EVENT_BUS = Path("/home/synczus/kestrel/event-bus.md")
INIT_SCRIPT = Path("/home/synczus/kestrel/shared-skills/scripts/hop-baton-init.py")

P0_AGENTS = {
    "Infra": "openclaw",
    "Config": "openclaw",
    "Cost": "hermes",
    "Credentials": "openclaw",
    "Orchestration": "hermes",
    "Monitoring": "kairos",
    "Awareness": "hermes",
    "Resilience": "nemoclaw",
    "Execution": "hermes",
    "Identity": "nemoclaw",
    "Cron": "hermes",
    "Pipeline": "hermes",
    "Striker": "kairos",
    "Pulse": "hermes",
    "Protocol": "hermes",
}

def log(msg):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    with open(EVENT_BUS, "a") as f:
        f.write(f"\n{ts} | baton-auto-cycle | {msg}")
    print(msg)

def get_baton_state():
    if not BATON.exists():
        return None
    return json.loads(BATON.read_text())

def find_next_p0():
    """Scrape master-todo.md for the highest-priority unassigned P0."""
    if not TODO.exists():
        return None

    text = TODO.read_text()
    lines = text.split("\n")
    
    in_sprint3 = False
    for i, line in enumerate(lines):
        if "SPRINT 3" in line:
            in_sprint3 = True
        if in_sprint3 and line.startswith("### Priority: P0"):
            # Look at the table rows after this header
            for j in range(i + 1, min(i + 20, len(lines))):
                row = lines[j]
                if row.startswith("|") and "🔴" in row or "🟡" in row:
                    parts = [p.strip() for p in row.split("|")]
                    if len(parts) >= 5:
                        lane = parts[1] if len(parts) > 1 else ""
                        item = parts[2] if len(parts) > 2 else ""
                        status = parts[4] if len(parts) > 4 else ""
                        if status in ("🔴 Needs exec", "🟡 Needs 1 command", "🔴 Needs setup", "🔴 Needs design"):
                            return {"lane": lane, "item": item, "status": status}
            break
    
    # Fallback: look for any 🔴 in P1
    in_sprint3 = False
    for i, line in enumerate(lines):
        if "SPRINT 3" in line:
            in_sprint3 = True
        if in_sprint3 and line.startswith("### Priority: P1"):
            for j in range(i + 1, min(i + 20, len(lines))):
                row = lines[j]
                if row.startswith("|") and "🔴" in row:
                    parts = [p.strip() for p in row.split("|")]
                    if len(parts) >= 5:
                        lane = parts[1] if len(parts) > 1 else ""
                        item = parts[2] if len(parts) > 2 else ""
                        status = parts[4] if len(parts) > 4 else ""
                        return {"lane": lane, "item": item, "status": status}
            break
    
    return None

def init_new_cycle(work_item, mission_type, why):
    """Call the hop-baton-init script."""
    result = subprocess.run(
        [sys.executable, str(INIT_SCRIPT), "kairos", 
         f"hop-auto-{datetime.now().strftime('%Y%m%d-%H%M')}",
         work_item, mission_type, why],
        capture_output=True, text=True, timeout=30
    )
    log(result.stdout.strip())
    if result.returncode != 0:
        log(f"Init failed: {result.stderr.strip()}")

def main():
    baton = get_baton_state()
    if not baton:
        log("No baton file found")
        return

    # Check if current cycle is parked/idle or completed
    cycle_id = baton.get("cycle_id", "")
    stage = baton.get("stage", "")
    
    # If baton is idle or parked, auto-start next cycle
    if stage == "intake" and "auto" not in cycle_id:
        # This is a manually-created cycle, let it run
        log(f"Manual cycle active: {cycle_id} — standing by")
        return
    
    if not cycle_id or cycle_id == "parked":
        next_work = find_next_p0()
        if next_work:
            agent = P0_AGENTS.get(next_work["lane"], "kairos")
            log(f"Auto-starting cycle: {next_work['lane']} | {next_work['item']}")
            init_new_cycle(
                next_work["item"],
                "local_execution",
                f"Auto-picked P0 from Sprint 3: {next_work['item']}"
            )
        else:
            log("No pending P0/P1 work found on board")
    
    # Write heartbeat
    hb_dir = Path("/home/synczus/kestrel/cron-health")
    hb_dir.mkdir(exist_ok=True)
    hb = {
        "name": "baton-auto-cycle",
        "status": "ok",
        "last_run": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "epoch": int(datetime.now(timezone.utc).timestamp())
    }
    (hb_dir / "baton-auto-cycle.heartbeat").write_text(json.dumps(hb, indent=2))

if __name__ == "__main__":
    main()