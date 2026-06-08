#!/usr/bin/env python3
"""OpenClaw hop trigger — check if hop is idle and auto-initiate"""
import json, os, subprocess
from datetime import datetime, timezone

HOP = "/home/synczus/kestrel/cycle-state/hop-sequence.json"
TODO = "/home/synczus/kestrel/master-todo.md"
AGENT_PULSES = "/home/synczus/kestrel/agent-pulses"

def load_hop():
    try:
        with open(HOP) as f:
            return json.load(f)
    except: return None

def write_hop(h):
    with open(HOP, 'w') as f:
        json.dump(h, f, indent=2)

def datetime_parse(s):
    return datetime.fromisoformat(s.replace('Z','+00:00'))

def main():
    h = load_hop()
    if not h:
        return
    
    now = datetime.now(timezone.utc)
    
    # Mode 1: Active hop — my turn
    if h.get("active") and not h.get("openclaw_done") and h.get("current_step", 0) >= 2:
        # Already in my section of the chain — skip, main session handles it
        return
    
    # Mode 2: Stuck hop — Kairos didn't complete
    if h.get("active") and not h.get("kairos_done"):
        # Mark kairos done so nemoclaw can proceed
        h["kairos_done"] = True
        h["current_step"] = 1
        write_hop(h)
        return
    
    # Mode 3: Complete, idle > 30 min — propose new cycle
    if h.get("complete") and h.get("auto"):
        idle = h.get("idle_since", "")
        if idle:
            try:
                idle_dt = datetime_parse(idle)
                mins = (now - idle_dt).total_seconds() / 60
                if mins > 5:
                    # Check if there's P0/P1 work on the board
                    pending = []
                    with open(TODO) as f:
                        for line in f:
                            if line.startswith("- [ ]") and ("P0" in line or "P1" in line):
                                pending.append(line.strip())
                    
                    if pending:
                        query = pending[0].replace("- [ ] ","").replace(f"{datetime.now().strftime('%Y-%m-%d')} | ","")
                        h["active"] = True
                        h["chain"] = ["kairos", "nemoclaw", "openclaw"]
                        h["current_step"] = 0
                        h["query"] = query
                        h["requested_by"] = "openclaw-auto"
                        h["kairos_done"] = False
                        h["nemoclaw_done"] = False
                        h["openclaw_done"] = False
                        h["complete"] = False
                        h["auto"] = True
                        h["idle_since"] = ""
                        write_hop(h)
                        
                        # Write pulse
                        pulse_dir = f"{AGENT_PULSES}/{now.strftime('%Y-%m-%d')}"
                        os.makedirs(pulse_dir, exist_ok=True)
                        with open(f"{pulse_dir}/openclaw-hop-initiate.md", 'a') as f:
                            f.write(f"\n{now.isoformat()} | openclaw-auto | initiated new hop: {query[:80]}")
            except: pass

if __name__ == "__main__":
    main()
