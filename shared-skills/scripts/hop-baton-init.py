#!/usr/bin/env python3
"""
Hop Baton Initializer v4.0 — creates a new cycle from the parked baton.

Usage:
    python3 hop-baton-init.py <cycle_id> <selected_work_item> \
        <mission_type> <why_this_work_now>

Exits 0 on success, copies the parked baton with the cycle filled in.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

BATON_PATH = Path("/home/synczus/kestrel/active-baton.json")
ARCHIVE_DIR = Path("/home/synczus/kestrel/batons")

MISSION_TYPES = [
    "local_execution", "repo_debugging", "service_runtime", "research",
    "market", "creative", "system_design", "storage_banking", "planning", "mixed"
]

REQUIRED_ARGS = [
    ("cycle_id", "cycle-id (e.g., hop-YYYY-MM-DD-topic)"),
    ("work_item", "selected work item description"),
    ("mission_type", f"mission type: {MISSION_TYPES}"),
    ("why", "why this work now"),
]


def get_flag(args: list[str], flag: str) -> str:
    for i, a in enumerate(args):
        if a == f"--{flag}" and i + 1 < len(args):
            return args[i + 1]
    return ""


def set_flag(args: list[str], flag: str) -> bool:
    return f"--{flag}" in args


def main():
    args = sys.argv[1:]

    name = get_flag(args, "agent") or args[0] if args else ""
    cycle_id = args[1] if len(args) > 1 else ""
    work_item = args[2] if len(args) > 2 else ""
    mission_type = args[3] if len(args) > 3 else ""
    why = args[4] if len(args) > 4 else ""

    if not all([name, cycle_id, work_item, mission_type, why]):
        print("Usage: hop-baton-init.py <agent_name> <cycle_id> <work_item> <mission_type> <why>", file=sys.stderr)
        print(f"       [--external] [--inspect] [--terminal] [--risk] [--confirm]", file=sys.stderr)
        print(f"  mission_type one of: {MISSION_TYPES}", file=sys.stderr)
        sys.exit(1)

    if mission_type not in MISSION_TYPES:
        print(f"Invalid mission_type '{mission_type}'. Must be one of: {MISSION_TYPES}", file=sys.stderr)
        sys.exit(1)

    if not BATON_PATH.exists():
        print(f"ERROR: {BATON_PATH} not found. Run baton-create first.", file=sys.stderr)
        sys.exit(1)

    baton = json.loads(BATON_PATH.read_text(encoding="utf-8"))
    if baton.get("cycle_id") != "parked":
        print(f"WARNING: active-baton.json has cycle_id='{baton.get('cycle_id')}' — not parked.", file=sys.stderr)
        print("Archiving current baton first...")
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
        archive = ARCHIVE_DIR / f"hop-{baton['cycle_id']}.json"
        archive.write_text(json.dumps(baton, indent=2))
        print(f"Archived to {archive}")

    # Classify mission
    requires_external = set_flag(args, "external")
    requires_inspect = set_flag(args, "inspect")
    requires_terminal = set_flag(args, "terminal")
    requires_risk = set_flag(args, "risk")
    requires_confirm = set_flag(args, "confirm")
    requires_file_changes = mission_type in ("local_execution", "repo_debugging", "system_design")

    # Build new baton
    now = datetime.now(timezone.utc).isoformat()
    baton["cycle_id"] = cycle_id
    baton["current_agent"] = name
    baton["previous_agent"] = "AI Hangout Banking"
    baton["stage"] = "intake"
    baton["mission"]["selected_work_item"] = work_item
    baton["mission"]["real_goal"] = why
    baton["mission"]["why_this_work_now"] = why
    baton["mission"]["mission_type"] = mission_type
    baton["classification"] = {
        "requires_external_research": requires_external,
        "requires_repo_inspection": requires_inspect,
        "requires_terminal_execution": requires_terminal,
        "requires_file_changes": requires_file_changes,
        "requires_runtime_verification": requires_terminal,
        "requires_risk_gate": requires_risk,
        "requires_storage_commit": True,
        "requires_user_confirmation": requires_confirm,
    }
    baton["state"]["known_current_state"] = ["Baton initialized for new cycle"]
    baton["persistent_storage_update"]["should_store"] = True
    baton["persistent_storage_update"]["memory_summary"] = f"Cycle {cycle_id} started by {name}: {work_item}"
    baton["next_agent_routing"]["next_agent_name"] = "Dynamic — first agent needed for this mission"
    baton["next_agent_routing"]["reason_for_next_hop"] = "New cycle initialized. Route based on classification flags."

    BATON_PATH.write_text(json.dumps(baton, indent=2))
    print(f"✅ Baton initialized: {cycle_id}")
    print(f"   Agent: {name}")
    print(f"   Work: {work_item}")
    print(f"   Type: {mission_type}")
    print(f"   External research: {'yes' if requires_external else 'no'}")
    print(f"   Repo inspect: {'yes' if requires_inspect else 'no'}")
    print(f"   Terminal: {'yes' if requires_terminal else 'no'}")
    print(f"   Risk gate: {'yes' if requires_risk else 'no'}")
    print(f"   Confirm: {'yes' if requires_confirm else 'no'}")
    print(f"   File changes: {'yes' if requires_file_changes else 'no'}")


if __name__ == "__main__":
    main()