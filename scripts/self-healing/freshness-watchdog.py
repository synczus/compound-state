#!/usr/bin/env python3
"""
Freshness Watchdog — checks every source against expected cadence
Runs every 60 seconds (or from cron), costs $0 in LLM calls.
Quarantines stale sources after 10 cycles.

Reads:
  - DuckDB signals table for last_seen per source
  - coordination.yaml for expected_cadence_minutes, tiers
  - cycle-state/current.json for stale_cycles state

Writes:
  - cycle-state/current.json (updates source health/quarantine flags)
  - DuckDB source_feedback (quarantine events)
"""
import json, os, sys, yaml
from datetime import datetime, timezone

KESTREL = "/home/synczus/kestrel"
DB = os.path.join(KESTREL, "signals.duckdb")
CONFIG = os.path.join(KESTREL, "manifests", "coordination.yaml")
STATE = os.path.join(KESTREL, "cycle-state", "current.json")

# Expected cadence per tier (minutes)
DEFAULT_CADENCES = {
    "lead_indicator": 1,
    "catalyst_confirmation": 15,
    "narrative_formation": 1440,
    "archival_reference": 99999
}

def load_config():
    with open(CONFIG) as f:
        return yaml.safe_load(f)

def load_state():
    try:
        with open(STATE) as f:
            return json.load(f)
    except:
        return {"sources": {}, "alerts": []}

def save_state(state):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE, "w") as f:
        json.dump(state, f, indent=2)

try:
    import duckdb

    cfg = load_config()
    state = load_state()
    now = datetime.now(timezone.utc)
    
    baselines = cfg["signal_ingestion"]["source_baselines"]
    con = duckdb.connect(DB)
    
    # Get last_seen per source from events table
    try:
        last_seen_rows = con.execute("""
            SELECT source_id, MAX(timestamp) as last_seen
            FROM events
            WHERE timestamp IS NOT NULL
            GROUP BY source_id
        """).fetchall()
    except:
        last_seen_rows = []
    
    last_seen_map = {row[0]: row[1] for row in last_seen_rows}
    
    # Initialize/update source tracking
    if "sources" not in state or not isinstance(state["sources"], dict):
        state["sources"] = {}
    
    source_alerts = []
    
    for sid, bl in baselines.items():
        tier = bl.get("tier", "unknown")
        cadence = DEFAULT_CADENCES.get(tier, 60)
        
        # Initialize source tracking if new
        if sid not in state["sources"]:
            state["sources"][sid] = {
                "tier": tier,
                "enabled": True,
                "last_seen": None,
                "stale_cycles": 0,
                "quarantined": False,
                "quarantine_reason": None
            }
        
        src = state["sources"][sid]
        
        # Update last_seen from DuckDB
        ls = last_seen_map.get(sid)
        if ls:
            src["last_seen"] = str(ls)
        else:
            ls = src.get("last_seen")
            if ls:
                try:
                    ls = datetime.fromisoformat(ls)
                except:
                    ls = None
        
        # Skip quarantine check for disabled/planned/research sources
        if not src.get("enabled", True) or bl.get("status") in ("planned", "needs_research", "deprecated"):
            continue
        
        if ls:
            age_minutes = (now - ls.replace(tzinfo=timezone.utc)).total_seconds() / 60
        else:
            age_minutes = 99999
        
        # Classify freshness
        if age_minutes <= cadence:
            src["stale_cycles"] = 0
            src["freshness"] = "fresh"
        elif age_minutes <= cadence * 2:
            src["stale_cycles"] = src.get("stale_cycles", 0) + 1
            src["freshness"] = "stale"
        elif age_minutes <= cadence * 4:
            src["stale_cycles"] = src.get("stale_cycles", 0) + 1
            src["freshness"] = "drift"
        else:
            src["stale_cycles"] = src.get("stale_cycles", 0) + 1
            src["freshness"] = "quarantine"
        
        src["age_minutes"] = round(age_minutes, 1)
        src["cadence_minutes"] = cadence
        src["last_checked"] = now.isoformat()
        
        # Auto-quarantine logic
        if not src.get("quarantined"):
            if src["freshness"] == "quarantine" and age_minutes > cadence * 4:
                # Check parse_fail_rate from config (simplified: use stale_cycles threshold)
                if src.get("stale_cycles", 0) >= 10:
                    src["quarantined"] = True
                    src["enabled"] = False
                    src["quarantine_reason"] = f"Stale for {age_minutes:.0f}min ({src['stale_cycles']} cycles)"
                    
                    source_alerts.append({
                        "source": sid,
                        "severity": "warning",
                        "reason": f"Quarantined: {src['quarantine_reason']}",
                        "created_at": now.isoformat()
                    })
                    
                    print(f"[watchdog] QUARANTINED {sid}: {src['quarantine_reason']}")
        
        # Auto-recovery: if quarantined and now fresh, start probation
        elif src.get("quarantined") and src["freshness"] == "fresh":
            probation = src.get("probation_cycles", 0) + 1
            src["probation_cycles"] = probation
            if probation >= 3:
                src["quarantined"] = False
                src["enabled"] = True
                src["quarantine_reason"] = None
                src["probation_cycles"] = 0
                source_alerts.append({
                    "source": sid,
                    "severity": "info",
                    "reason": f"Auto-recovered after 3 fresh cycles",
                    "created_at": now.isoformat()
                })
                print(f"[watchdog] RECOVERED {sid}: back online after quarantine")
    
    # Append new alerts to state
    if "alerts" not in state:
        state["alerts"] = []
    state["alerts"].extend(source_alerts)
    # Keep last 50 alerts
    state["alerts"] = state["alerts"][-50:]
    
    state["timestamp"] = now.isoformat()
    
    # Counts
    total = len(state["sources"])
    enabled = sum(1 for s in state["sources"].values() if s.get("enabled"))
    quarantined = sum(1 for s in state["sources"].values() if s.get("quarantined"))
    
    save_state(state)
    
    print(f"[watchdog] Checked {total} sources: {enabled} enabled, {quarantined} quarantined, {len(source_alerts)} new alerts")
    
except ImportError:
    print("[watchdog] duckdb not installed. Install: pip3 install duckdb")
    sys.exit(1)
except Exception as e:
    print(f"[watchdog] Error: {e}")
    sys.exit(1)
