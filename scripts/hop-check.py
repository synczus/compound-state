#!/usr/bin/env python3
"""
hop-check.py — Turn enforcement for the compound.

Every agent calls this before speaking in the group chat to determine
if it's their turn in the current hop cycle.

Usage:
  python3 hop-check.py --agent kairos
    → "your_turn" | "not_your_turn" | "hop_idle" | "hop_complete"

Exit codes:
  0 = your turn (speak now)
  1 = not your turn (wait)
  2 = hop idle/complete (free to speak per Standing Research Lane rules)
"""

import json
import sys
import os
import argparse

HOP_FILE = "/home/synczus/kestrel/cycle-state/hop-sequence.json"


def check_turn(agent_name: str) -> int:
    """Check if it's the agent's turn to speak."""
    try:
        with open(HOP_FILE) as f:
            hop = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # No hop file = no active cycle = free to speak
        print("hop_complete")
        return 2

    active = hop.get("active", False)
    complete = hop.get("complete", True)
    chain = hop.get("chain", [])
    step = hop.get("current_step", 0)

    if not active or complete:
        print("hop_complete")
        return 2

    if step >= len(chain):
        print("hop_complete")
        return 2

    current_agent = chain[step]
    agent_done = hop.get(f"{agent_name}_done", False)

    if current_agent == agent_name and not agent_done:
        print("your_turn")
        return 0
    else:
        current_done = hop.get(f"{current_agent}_done", False)
        if current_done:
            # The current step agent finished but step hasn't advanced
            # This could mean we need to wait for advance or it's stale
            print("hop_stale_advance")
        else:
            print(f"not_your_turn")
        return 1


def advance(agent_name: str, message: str = ""):
    """Mark the current agent's turn as done and advance to next."""
    try:
        with open(HOP_FILE) as f:
            hop = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("No active hop to advance", file=sys.stderr)
        return False

    if not hop.get("active"):
        print("Hop is not active", file=sys.stderr)
        return False

    hop[f"{agent_name}_done"] = True
    hop[f"{agent_name}_message"] = message
    hop["current_step"] = hop.get("current_step", 0) + 1

    # Check if cycle is complete
    if hop["current_step"] >= len(hop.get("chain", [])):
        hop["complete"] = True
        hop["active"] = False

    from datetime import datetime, timezone
    hop["last_updated"] = datetime.now(timezone.utc).isoformat()

    with open(HOP_FILE, "w") as f:
        json.dump(hop, f, indent=2)

    print(f"Advanced {agent_name}, step now {hop['current_step']}")
    if hop.get("complete"):
        print("Hop cycle complete!")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hop turn enforcement")
    parser.add_argument("--agent", required=True, help="Your agent name")
    parser.add_argument("--action", choices=["check", "advance"], default="check",
                        help="check turn status or advance the hop")
    parser.add_argument("--message", default="", help="Completion message (for advance)")

    args = parser.parse_args()

    if args.action == "advance":
        sys.exit(0 if advance(args.agent, args.message) else 1)
    else:
        sys.exit(check_turn(args.agent))