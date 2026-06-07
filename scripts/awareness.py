#!/usr/bin/env python3
"""Compound state log — injects awareness into every agent response."""
import json
import os
import subprocess
import time
from datetime import datetime, timezone

STATE_FILE = "/home/synczus/kestrel/compound-state.json"
HISTORY_FILE = "/home/synczus/kestrel/compound-awareness.json"
BOARD_FILE = "/home/synczus/kestrel/master-todo.md"
STRIKER_HEALTH = "/home/synczus/huntsystems/kestrel-striker/striker_health.json"

def read_file_safe(path):
    try:
        with open(path) as f:
            return f.read()
    except:
        return None

def get_striker_status():
    health = read_file_safe(STRIKER_HEALTH)
    if health:
        try:
            h = json.loads(health)
            return {
                "status": h.get("status", "unknown"),
                "price": h.get("last_price", h.get("price", "unknown")),
                "symbol": h.get("symbol", "unknown"),
                "last_signal": h.get("last_signal", h.get("last_event", "none")),
            }
        except:
            return {"status": "unknown", "price": "unknown"}
    return {"status": "offline"}

def get_board_summary():
    board = read_file_safe(BOARD_FILE)
    if not board:
        return {"p0": 0, "p1": 0, "p2": 0, "claimed": 0}
    
    lines = board.split("\n")
    p0 = sum(1 for l in lines if "P0" in l and "Needs exec" in l)
    p1 = sum(1 for l in lines if "P1" in l and "Needs exec" in l)
    p2 = sum(1 for l in lines if "P2" in l and "Needs exec" in l)
    done = sum(1 for l in lines if "✅" in l)
    claimed = sum(1 for l in lines if "🟡" in l or "In Progress" in l)
    
    return {"p0_pending": p0, "p1_pending": p1, "p2_pending": p2, "done": done, "in_progress": claimed}

def get_recent_hlms():
    board = read_file_safe(BOARD_FILE)
    if not board:
        return []
    lines = board.split("\n")
    hlms = [l.strip() for l in lines if "Scraper" in l and "|" in l and "HLM" not in l]
    return hlms[-5:] if hlms else []

def build_state():
    state = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "epoch_seconds": int(time.time()),
        "board_summary": get_board_summary(),
        "striker": get_striker_status(),
        "recent_hlms": get_recent_hlms(),
        "last_agent_actions": [],
        "open_loops": [],
        "gif_api_status": "needs_key" if not os.environ.get("KLIPY_API_KEY", "") else "ready",
        "agents_active": ["hermes", "openclaw", "nemoclaw", "kairos", "shannon"],
    }
    
    # Load history for rolling context
    history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE) as f:
                history = json.load(f)
        except:
            history = []
    
    # Keep last 20 entries
    history = history[-20:]
    
    state["agent_history"] = [h for h in history[-5:]]
    
    return state, history

def record_action(agent: str, action: str, detail: str = ""):
    """Call this after any agent action to update awareness."""
    state, history = build_state()
    
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent": agent,
        "action": action,
        "detail": detail,
    }
    history.append(entry)
    
    # Keep last 50 actions
    history = history[-50:]
    
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)
    
    # Update live state
    state["last_action"] = entry
    state["agent_history"] = [h for h in history[-5:]]
    
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def get_awareness_context() -> str:
    """Returns a compact awareness block for agent system prompts."""
    state, _ = build_state()
    
    b = state["board_summary"]
    s = state["striker"]
    
    lines = []
    lines.append(f"## Compound Status ({state['timestamp'][:19]} UTC)")
    lines.append(f"Board: {b['p0_pending']} P0 · {b['p1_pending']} P1 · {b['p2_pending']} P2 pending · {b['in_progress']} in progress · {b['done']} done")
    lines.append(f"Striker: {s.get('status', 'unknown')} | {s.get('symbol', '?')} @ {s.get('price', '?')} | Last signal: {s.get('last_signal', 'none')}")
    
    if state.get("agent_history"):
        lines.append("Recent actions:")
        for h in state["agent_history"][-3:]:
            lines.append(f"  · {h['agent']}: {h['action']}")
    
    if state["recent_hlms"]:
        lines.append("Recent HLMs:")
        for hlm in state["recent_hlms"][-2:]:
            lines.append(f"  · {hlm}")
    
    lines.append(f"GIF API: {state['gif_api_status']}")
    lines.append(f"Agents: {', '.join(state['agents_active'])}")
    
    return "\n".join(lines)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "record":
        agent = sys.argv[2] if len(sys.argv) > 2 else "unknown"
        action = sys.argv[3] if len(sys.argv) > 3 else "action"
        detail = " ".join(sys.argv[4:]) if len(sys.argv) > 4 else ""
        record_action(agent, action, detail)
    elif len(sys.argv) > 1 and sys.argv[1] == "context":
        print(get_awareness_context())
    else:
        # Build fresh state
        state, history = build_state()
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
        print(f"State written to {STATE_FILE}")
        print(get_awareness_context())