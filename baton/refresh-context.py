#!/usr/bin/env python3
"""refresh-context.py — Refresh the shared context packet from live sources.
Run this at the start of any agent's cron cycle to snap-read compound state.
Usage: python3 /home/synczus/kestrel/baton/refresh-context.py
"""
import json, os, time, sqlite3, subprocess
from pathlib import Path

BATON = Path("/home/synczus/kestrel/baton")
PACKET = BATON / "context-packet.json"
HEALTH = Path("/home/synczus/kestrel/striker_health.json")
MONITOR = Path("/home/synczus/kestrel/kairos_monitor_state.json")
DB = Path("/home/synczus/kestrel/kestrel_signals.db")
EVENT_BUS = Path("/home/synczus/kestrel/event-bus.md")

def load_json(path):
    try:
        return json.loads(path.read_text())
    except: return {}

def get_striker_health():
    h = load_json(HEALTH)
    if not h: return {"status": "unknown", "pid": None, "health_age_ms": None}
    age = int((time.time() - h.get("timestamp", 0)) * 1000) if h.get("timestamp") else None
    return {
        "status": h.get("status", "unknown"),
        "pid": h.get("pid"),
        "health_age_ms": age,
        "signal_count": h.get("signals_processed", 0),
        "ws_subscriptions": h.get("subscriptions", [])
    }

def get_db_count():
    try:
        conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=1)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM signals")
        count = c.fetchone()[0]
        conn.close()
        return count
    except: return 0

def get_monitor_state():
    return load_json(MONITOR)

def get_cron_timestamps():
    # check master-todo and event bus for last activity
    lines = []
    if EVENT_BUS.exists():
        lines = EVENT_BUS.read_text().splitlines()[-50:]
    return {"recent_events": lines[-10:] if lines else []}

def get_active_baton():
    return load_json(BATON / "baton-current.json")

def get_inbox_counts():
    inboxes = {}
    for f in (BATON / "agent-inboxes").glob("*.json"):
        try:
            data = json.loads(f.read_text())
            msgs = [m for m in data.get("messages", []) if not m.get("read")]
            inboxes[f.stem] = {"unread": len(msgs), "last_message": msgs[-1].get("subject") if msgs else None}
        except:
            inboxes[f.stem] = {"unread": 0, "last_message": None}
    return inboxes

def main():
    packet = {
        "schema": "compound-context-packet.v1",
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "snapshot": {
            "striker": get_striker_health(),
            "kairos_monitor": get_monitor_state(),
            "cron": get_cron_timestamps(),
            "compound": {
                "signal_count": get_db_count(),
            }
        },
        "active_baton": get_active_baton(),
        "agent_inboxes": get_inbox_counts(),
    }
    PACKET.write_text(json.dumps(packet, indent=2))
    print(f"Context packet refreshed: {len(json.dumps(packet))} bytes")
    # Print actionable state for agent consumption
    s = packet["snapshot"]["striker"]
    m = packet["snapshot"]["kairos_monitor"]
    print(f"  Striker: {s['status']} | PID {s['pid']} | signals: {s['signal_count']}")
    print(f"  Monitor: {m.get('health_status','?')} | DB: {m.get('db_status','?')}")
    bat = packet["active_baton"]
    if bat and bat.get("next_agent_name"):
        print(f"  Baton: {bat['next_agent_name']} -> {bat.get('work_item','?')}")
    print(f"  Inboxes: {packet['agent_inboxes']}")

if __name__ == "__main__":
    main()