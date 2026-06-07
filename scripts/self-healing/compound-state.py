#!/usr/bin/env python3
"""
Compound State Generator v0.2
Single-file source of truth for the compound — any agent reads this once.
Writes to: /home/synczus/kestrel/cycle-state/current.json
"""
import json, os, subprocess, sys
from datetime import datetime, timezone

KESTREL = "/home/synczus/kestrel"
DB = os.path.join(KESTREL, "signals.duckdb")
STATE = os.path.join(KESTREL, "cycle-state", "current.json")
BUDGET_FILE = os.path.expanduser("~/.hermes/budget-guard-state.json")
STRIKER_HEALTH = os.path.join(KESTREL, "striker_health.json")

def json_or(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except: return default

def service_status(name):
    r = subprocess.run(["systemctl", "is-active", "--quiet", name], capture_output=True)
    return "active" if r.returncode == 0 else "inactive"

def source_counts():
    try:
        import duckdb
        con = duckdb.connect(DB)
        rows = con.execute("SELECT source_id, lane, COUNT(*) FROM events GROUP BY source_id, lane").fetchall()
        s = {}
        for sid, lane, cnt in rows:
            s.setdefault(sid, {})[lane] = cnt
        return s if s else {"no_data": True}
    except: return {"db_offline": True}

now = datetime.now(timezone.utc).isoformat()

state = {
    "timestamp": now,
    "version": "0.1.0",
    "budget": json_or(BUDGET_FILE, {"usd_remaining": 999, "status": "unknown"}),
    "services": {
        "striker": {"status": service_status("kestrel-striker"), "health": json_or(STRIKER_HEALTH, {})},
        "wolfwatch": {"status": service_status("wolfwatch")}
    },
    "sources": source_counts(),
    "alerts": [],
    "degradation": {"active": False, "tier_cutoff": None, "reason": None},
    "agents": {
        "nemoclaw": {"status": "unknown"},
        "kairos": {"status": "unknown"},
        "kestrelmarkets": {"status": "unknown"},
        "shannon": {"status": "disabled"}
    }
}

# Budget alerts
b = state["budget"].get("usd_remaining", 999)
if isinstance(b, (int, float)):
    if b < 5:
        state["alerts"].append({"source": "budget", "severity": "warning", "reason": f"OR balance ${b:.2f} — below $5"})
    if b < 2:
        state["alerts"].append({"source": "budget", "severity": "critical", "reason": "Balance below $2 — guard will pause"})
        state["degradation"] = {"active": True, "tier_cutoff": "archival_reference", "reason": "Budget critical"}

# Service alerts
for svc in ["striker", "wolfwatch"]:
    if state["services"][svc]["status"] == "inactive":
        state["alerts"].append({"source": svc, "severity": "error", "reason": f"{svc} service inactive"})

os.makedirs(os.path.dirname(STATE), exist_ok=True)
with open(STATE, "w") as f:
    json.dump(state, f, indent=2)

budget_str = f"${b:.2f}" if isinstance(b, (int, float)) else "?"
print(f"[compound-state] {os.path.relpath(STATE)} — budget={budget_str} striker={state['services']['striker']['status']} alerts={len(state['alerts'])}")