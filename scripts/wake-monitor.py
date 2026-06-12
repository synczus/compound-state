#!/usr/bin/env python3
"""Wake-on-Stale trigger — alerts when board items sit unclaimed too long."""
import json, os, re, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

BOARD = Path("/home/synczus/kestrel/master-todo.md")
STATE = Path("/home/synczus/kestrel/wake-state.json")
WOLFWATCH = "http://127.0.0.1:18790/notify"
STALE_HOURS = 12

def read_board():
    if not BOARD.exists():
        return []
    text = BOARD.read_text()
    items = []
    for line in text.split("\n"):
        line = line.strip()
        # Match todo table rows with 🔴 or ⚪ status
        if ("🔴" in line or "⚪" in line) and "|" in line:
            parts = [p.strip() for p in line.split("|")]
            # Find the description column - it's usually the third non-empty part
            non_empty = [p for p in parts if p]
            desc = non_empty[2] if len(non_empty) > 2 else line[:80]
            priority = non_empty[0] if len(non_empty) > 0 else "?"
            # Clean priority field
            priority = priority.replace("||", "").replace("|", "").strip()
            desc = desc.strip().rstrip(",")
            items.append({"priority": priority, "category": "", "desc": desc[:80], "line": line[:100]})
    return items

def load_state():
    if STATE.exists():
        try:
            return json.loads(STATE.read_text())
        except:
            pass
    return {"last_alert": {}, "seen": []}

def save_state(s):
    STATE.write_text(json.dumps(s, indent=2))

def main():
    items = read_board()
    state = load_state()
    now = datetime.now(timezone.utc).isoformat()
    now_ts = datetime.now(timezone.utc).timestamp()
    
    stale_items = []
    for item in items:
        key = item["desc"][:50]
        if key not in state["last_alert"]:
            state["last_alert"][key] = now_ts
        elif now_ts - state["last_alert"][key] > STALE_HOURS * 3600:
            stale_items.append(item)
    
    if stale_items:
        msg_lines = [f"🧟 {len(stale_items)} item(s) stale >{STALE_HOURS}h:"]
        for item in stale_items[:5]:
            msg_lines.append(f"  · [{item['priority']}] {item['desc']}")
        
        body = "\n".join(msg_lines)
        payload = json.dumps({
            "source": "wake-monitor",
            "severity": "warning",
            "title": "Stale work items",
            "body": body
        })
        
        try:
            import urllib.request
            req = urllib.request.Request(WOLFWATCH, data=payload.encode(), 
                                        headers={"Content-Type": "application/json"},
                                        method="POST")
            resp = urllib.request.urlopen(req, timeout=10)
            print(f"Alert sent: {resp.status}")
        except Exception as e:
            print(f"Alert failed: {e}")
        
        # Reset alert timers for alerted items
        for item in stale_items:
            key = item["desc"][:50]
            state["last_alert"][key] = now_ts
    else:
        # Silent exit — nothing to report
        pass
    
    save_state(state)

if __name__ == "__main__":
    main()
