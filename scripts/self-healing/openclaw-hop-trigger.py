#!/usr/bin/env python3
"""Hop trigger — check if hop is idle, auto-initiate with full 5-agent chain"""
import json, os
from datetime import datetime, timezone

HOP = "/home/synczus/kestrel/cycle-state/hop-sequence.json"
TODO = "/home/synczus/kestrel/master-todo.md"
AGENT_PULSES = "/home/synczus/kestrel/agent-pulses"

CHAIN = ["kairos", "shannon", "nemoclaw", "hermes", "openclaw"]

def load_hop():
    try:
        with open(HOP) as f:
            return json.load(f)
    except:
        return None

def write_hop(h):
    with open(HOP, 'w') as f:
        json.dump(h, f, indent=2)

def datetime_parse(s):
    return datetime.fromisoformat(s.replace('Z', '+00:00'))

def main():
    h = load_hop()
    if not h:
        return

    now = datetime.now(timezone.utc)

    # Mode 1: Active hop — check if any agent is stuck
    if h.get("active") and not h.get("complete"):
        # Auto-advance stuck agents (idle > 30min without completion)
        for agent in CHAIN:
            done_key = f"{agent}_done"
            if h.get(done_key):
                continue
            # If this agent is the current step and it's been >30min, mark done
            if h.get("current_step", 0) >= CHAIN.index(agent):
                step_agent = CHAIN[h.get("current_step", 0)]
                # Only auto-advance the current step agent
                if step_agent == agent:
                    idle = h.get("idle_since", "")
                    if idle:
                        try:
                            idle_dt = datetime_parse(idle)
                            if (now - idle_dt).total_seconds() > 1800:  # 30 min
                                h[done_key] = True
                                h["current_step"] = min(h.get("current_step", 0) + 1, len(CHAIN) - 1)
                                h["idle_since"] = ""
                                write_hop(h)
                        except:
                            pass
        return

    # Mode 2: Complete, idle > 5 min — propose new cycle
    if h.get("complete") and h.get("auto"):
        idle = h.get("idle_since", "")
        if idle:
            try:
                idle_dt = datetime_parse(idle)
                mins = (now - idle_dt).total_seconds() / 60
                if mins > 5:
                    pending = []
                    with open(TODO) as f:
                        for line in f:
                            if line.startswith("- [ ]") and ("P0" in line or "P1" in line):
                                pending.append(line.strip())
                    if pending:
                        query = pending[0].replace("- [ ] ", "")
                        h = {
                            "active": True,
                            "chain": CHAIN,
                            "current_step": 0,
                            "query": query,
                            "requested_by": "auto-hop-trigger",
                            **{f"{a}_done": False for a in CHAIN},
                            "complete": False,
                            "auto": True,
                            "idle_since": "",
                            "last_updated": now.strftime("%Y-%m-%dT%H:%M:%SZ")
                        }
                        write_hop(h)
                        pulse_dir = f"{AGENT_PULSES}/{now.strftime('%Y-%m-%d')}"
                        os.makedirs(pulse_dir, exist_ok=True)
                        with open(f"{pulse_dir}/hop-initiate.md", 'a') as f:
                            f.write(f"\n{now.isoformat()} | auto | hop initiated: {query[:80]}")
            except:
                pass

if __name__ == "__main__":
    main()