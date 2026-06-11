#!/usr/bin/env python3
"""
Source Health Scorer — runs from compound-state.sh or standalone
Scores each source 0-100: freshness + volume_stability + delivery_reliability
Flags stale/drift/quarantine based on DuckDB event data
"""

import json
import os
import sys
from datetime import datetime, timezone

KESTREL_DIR = os.environ.get("KESTREL_DIR", os.path.expanduser("~/kestrel"))
DB_PATH = os.path.join(KESTREL_DIR, "signals.duckdb")
CONFIG_PATH = os.path.join(KESTREL_DIR, "manifests", "coordination.yaml")

def load_config():
    """Load coordination.yaml for source baselines, tiers, drop_order."""
    try:
        import yaml
        with open(CONFIG_PATH) as f:
            d = yaml.safe_load(f)
        return d["signal_ingestion"]["source_baselines"]
    except Exception as e:
        print(f"[ERROR] Cannot load config: {e}", file=sys.stderr)
        return {}

def score_sources():
    """Score each source from DuckDB data + config baselines."""
    baselines = load_config()
    
    try:
        import duckdb
        con = duckdb.connect(DB_PATH)
        
        # Per-source stats from DuckDB
        rows = con.execute("""
            SELECT 
                source_id,
                COUNT(*) as total_events,
                COUNT(DISTINCT DATE(timestamp)) as active_days,
                COUNT(CASE WHEN lane = 'urgent' THEN 1 END) as urgent_count,
                COUNT(CASE WHEN lane = 'high_signal' THEN 1 END) as high_count,
                MAX(timestamp) as last_seen,
                MIN(timestamp) as first_seen
            FROM events 
            GROUP BY source_id
        """).fetchall()
        
        if not rows:
            print('{"sources": {}, "error": "no_data"}')
            return
        
        scores = {}
        now = datetime.now(timezone.utc)
        
        for row in rows:
            sid, total, days, urgent, high, last_seen, first_seen = row
            
            # Default config for this source
            cfg = baselines.get(sid, {})
            tier = cfg.get("tier", "unknown")
            baseline_score = cfg.get("baseline", 0.5)
            drop_order = cfg.get("drop_order", 3)
            expected_cadence_min = {"lead_indicator": 1, "catalyst_confirmation": 15, "narrative_formation": 1440, "archival_reference": 99999}.get(tier, 60)
            
            # Freshness (0-40): how recent vs expected cadence
            if last_seen:
                hours_since = (now - last_seen.replace(tzinfo=timezone.utc)).total_seconds() / 3600
                expected_hours = expected_cadence_min / 60
                freshness = max(0, 40 - (hours_since / expected_hours) * 20)
            else:
                freshness = 0
                hours_since = 999
            
            # Volume stability (0-30): events per day vs tier expectation
            if days > 0:
                events_per_day = total / days
                expected_per_day = {"lead_indicator": 100, "catalyst_confirmation": 50, "narrative_formation": 2, "archival_reference": 0}.get(tier, 10)
                if expected_per_day > 0:
                    volume_ratio = min(events_per_day / expected_per_day, 3)
                    volume = 30 * (volume_ratio / 3)  # Scale to 0-30
                else:
                    volume = 15
            else:
                volume = 0
            
            # Quality (0-30): signal lane distribution
            total_signaled = urgent + high
            if total > 0:
                signal_ratio = total_signaled / total
                quality = 30 * min(signal_ratio * 2, 1)
            else:
                quality = 10
            
            # Total score
            health_score = min(100, round(freshness + volume + quality))
            
            # Stale flag: >2x expected cadence since last event
            stale = hours_since > (expected_cadence_min * 2 / 60)
            
            # Drift flag: volume anomaly (simplified)
            drift = health_score < 20 and total > 10
            
            scores[sid] = {
                "tier": tier,
                "baseline": baseline_score,
                "drop_order": drop_order,
                "health_score": health_score,
                "freshness": round(freshness, 1),
                "volume_stability": round(volume, 1),
                "quality_score": round(quality, 1),
                "last_seen": str(last_seen) if last_seen else None,
                "hours_since_update": round(hours_since, 1),
                "total_events": total,
                "active_days": days,
                "urgent_count": urgent,
                "high_signal_count": high,
                "stale": stale,
                "drift": drift
            }
        
        print(json.dumps({"sources": scores, "timestamp": now.isoformat()}))
        
    except Exception as e:
        print(json.dumps({"error": str(e), "sources": {}}))

if __name__ == "__main__":
    score_sources()