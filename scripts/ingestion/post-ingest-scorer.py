#!/usr/bin/env python3
"""
Post-Ingest Scorer — runs after every pulse batch (or cron 30s)
Implements Perplexity's Round 3 design: 9-step post-ingest scoring pipeline.

1. Load watermark from state
2. Query events WHERE scored=false AND event_ts > watermark
3. Compute recency_weight per tier half-life
4. Look up source_prior, tier, FP_penalty
5. Update cross-source agreement buckets
6. Compute edge_score
7. Insert into signal_scores (UPSERT)
8. Recompute top-20 queue
9. Update watermark
"""
import json, os, sys, copy, glob
from datetime import datetime, timezone
from math import exp, log as math_log

KESTREL = "/home/synczus/kestrel"
DB = os.path.join(KESTREL, "signals.duckdb")
CONFIG = os.path.join(KESTREL, "manifests", "coordination.yaml")
STATE = os.path.join(KESTREL, "cycle-state", "current.json")
QUEUE = os.path.join(KESTREL, "dashboard", "pending.json")

# Per-tier configuration
TIER_CONFIG = {
    "lead_indicator":       {"half_life_min": 30, "tier_mult": 1.15},
    "catalyst_confirmation":{"half_life_min": 120,"tier_mult": 1.00},
    "narrative_formation":  {"half_life_min": 720,"tier_mult": 0.90},
    "archival_reference":   {"half_life_min": 9999,"tier_mult": 0.50}
}

BLUECHIP_MULT = {"BTC": 1.10, "ETH": 1.10, "SOL": 1.10}

def log(s):
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[scorer {ts}] {s}")

try:
    import yaml
    import duckdb
except ImportError as e:
    log(f"Missing dep: {e}")
    sys.exit(1)
STAGING = os.path.join(KESTREL, "ingestion", "staging")

def load_config():
    with open(CONFIG) as f:
        return yaml.safe_load(f)

def load_watermark():
    """Load last scored timestamp from state file."""
    try:
        with open(STATE) as f:
            d = json.load(f)
        return d.get("scoring", {}).get("watermark", "1970-01-01T00:00:00Z")
    except:
        return "1970-01-01T00:00:00Z"

def save_watermark(ts):
    """Update watermark in state file."""
    try:
        with open(STATE) as f:
            d = json.load(f)
    except:
        d = {}
    if "scoring" not in d:
        d["scoring"] = {}
    d["scoring"]["watermark"] = ts
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE, "w") as f:
        json.dump(d, f, indent=2)

def save_top20(rows):
    """Write top-20 queue to JSON for Synapse dashboard."""
    os.makedirs(os.path.dirname(QUEUE), exist_ok=True)
    with open(QUEUE, "w") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "queue": rows,
            "count": len(rows)
        }, f, indent=2)

def run():
    now = datetime.now(timezone.utc)
    
    con = duckdb.connect(DB)
    
    # 0. Stage 0: Consume any JSONL staging files from archive-ingest
    # This avoids concurrent write conflicts — archive-ingest writes JSONL, scorer reads + inserts
    staging_files = sorted(glob.glob(os.path.join(STAGING, "events_*.jsonl")))
    if staging_files:
        staged_total = 0
        for sf in staging_files:
            try:
                with open(sf) as f:
                    events = [json.loads(line) for line in f if line.strip()]
                if not events:
                    os.remove(sf)
                    continue
                
                # Ensure events table exists
                con.execute('''
                    CREATE TABLE IF NOT EXISTS events (
                        row_id INTEGER PRIMARY KEY,
                        source_id VARCHAR NOT NULL,
                        event_type VARCHAR,
                        timestamp TIMESTAMP,
                        payload_headline VARCHAR,
                        payload_body TEXT,
                        symbols VARCHAR,
                        lane VARCHAR DEFAULT 'queue',
                        action VARCHAR DEFAULT 'archive_ingest',
                        confidence DOUBLE DEFAULT 0.3,
                        magnitude DOUBLE,
                        velocity VARCHAR,
                        provenance_source_url VARCHAR,
                        provenance_hash VARCHAR,
                        scored BOOLEAN DEFAULT false,
                        ingested_ts TIMESTAMP DEFAULT now()
                    )
                ''')
                
                # Get max row_id
                max_row = con.execute("SELECT COALESCE(MAX(row_id), 0) FROM events").fetchone()[0]
                
                batch = []
                for i, evt in enumerate(events):
                    max_row += 1
                    batch.append((
                        max_row,
                        evt.get("source_id", "unknown"),
                        evt.get("event_type", "general_news"),
                        evt.get("timestamp", now.isoformat()),
                        evt.get("headline", "")[:600],
                        evt.get("body", "")[:2000],
                        evt.get("symbols"),
                        "queue",
                        "archive_ingest",
                        0.30,
                        None,  # magnitude
                        None,  # velocity
                        evt.get("provenance_url"),
                        evt.get("provenance_hash", "")[:32]
                    ))
                
                con.executemany('''
                    INSERT INTO events (
                        row_id, source_id, event_type, timestamp, payload_headline,
                        payload_body, symbols, lane, action, confidence,
                        magnitude, velocity, provenance_source_url, provenance_hash
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', batch)
                
                os.remove(sf)
                staged_total += len(batch)
                log(f"Consumed {len(batch)} events from {os.path.basename(sf)}")
            except Exception as e:
                log(f"Failed to consume {sf}: {e}")
        
        if staged_total:
            log(f"Staging total: {staged_total} events written to DuckDB")
    
    watermark = load_watermark()
    
    # 1. Check if events table exists
    tables = [r[0] for r in con.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='main'").fetchall()]
    if "events" not in tables:
        log("No events table — skipping")
        return
    
    # 2. Query unscored events since watermark
    try:
        new_events = con.execute(f"""
            SELECT row_id, source_id, event_type, timestamp, confidence, 
                   magnitude, velocity, symbols, lane, action
            FROM events 
            WHERE (scored IS NULL OR scored = false)
              AND timestamp > '{watermark}'::TIMESTAMP
            ORDER BY timestamp ASC
        """).fetchall()
    except Exception as e:
        log(f"Query failed: {e}")
        return
    
    if not new_events:
        log("No new events to score")
        return
    
    log(f"Scoring {len(new_events)} new events")
    
    # Load config for source baselines/tiers
    config = load_config()
    baselines = config["signal_ingestion"]["source_baselines"]
    
    # Get source feedback
    try:
        feedback = con.execute("SELECT source_id, wolf_rate FROM source_feedback").fetchall()
        wolf_map = {r[0]: r[1] for r in feedback}
    except:
        wolf_map = {}
    
    scored_count = 0
    bucket_updates = set()  # Track which buckets need agreement rebuild
    
    for row in new_events:
        row_id, source_id, event_type, ts, confidence, magnitude, velocity, symbols, lane, action = row
        
        if not ts:
            continue
        
        # Convert ts to datetime if string
        if isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts)
            except:
                continue
        
        # 3. Compute recency_weight
        recency_min = (now - ts.replace(tzinfo=timezone.utc)).total_seconds() / 60
        
        # Look up source config
        bl = baselines.get(source_id, {})
        tier = bl.get("tier", "catalyst_confirmation")
        source_prior = bl.get("baseline", 0.5)
        
        tier_cfg = TIER_CONFIG.get(tier, TIER_CONFIG["catalyst_confirmation"])
        half_life = tier_cfg["half_life_min"]
        tier_mult = tier_cfg["tier_mult"]
        
        # recency_weight = exp(-ln(2) * recency_min / half_life)
        recency_weight = exp(-math_log(2) * recency_min / max(half_life, 1))
        
        # 4. Look up source additional factors
        fp_penalty = max(0.70, 1.0 - 0.40 * wolf_map.get(source_id, 0))
        
        # Asset relevance & novelty (defaults — can be enriched)
        asset_relevance = 1.0
        novelty = 1.0
        
        # Symbol-specific boosts
        bluechip_mult = 1.0
        asset_symbol = None
        if symbols:
            for sym in symbols:
                bm = BLUECHIP_MULT.get(sym.strip().upper())
                if bm:
                    bluechip_mult = max(bluechip_mult, bm)
                    asset_symbol = sym.strip().upper()
        
        # 5. Track bucket for cross-source agreement
        bucket_min = ts.replace(second=0, microsecond=0)
        bucket_key = (asset_symbol, bucket_min)
        if bucket_key:
            bucket_updates.add(bucket_key)
        
        # 6. Compute edge_score (cross_source_boost computed after batch)
        # Temporarily set to 1.0, will be updated after bucket rebuild
        cross_source_boost = 1.0
        
        edge_score = (
            source_prior *
            (confidence or 0.5) *
            asset_relevance *
            novelty *
            recency_weight *
            cross_source_boost *
            fp_penalty *
            tier_mult *
            bluechip_mult
        )
        
        # Build score_id
        score_id = f"{row_id}_{source_id}"
        
        # 7. Upsert into signal_scores
        try:
            con.execute("""
                INSERT INTO signal_scores (
                    score_id, signal_id, source_id, asset_symbol, event_type,
                    event_ts, ingested_ts, source_prior, reported_confidence,
                    magnitude, velocity, asset_relevance, novelty,
                    recency_minutes, recency_weight, cross_source_boost,
                    false_positive_penalty, edge_score, tier, rationale,
                    raw_payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, now(), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (score_id) DO UPDATE SET
                    recency_minutes = EXCLUDED.recency_minutes,
                    recency_weight = EXCLUDED.recency_weight,
                    edge_score = EXCLUDED.edge_score,
                    ingested_ts = now()
            """, (
                score_id, str(row_id), source_id, asset_symbol, event_type or "unknown",
                ts, source_prior, confidence or 0.5,
                magnitude, velocity, asset_relevance, novelty,
                round(recency_min, 2), round(recency_weight, 4),
                cross_source_boost, fp_penalty, round(edge_score, 4),
                tier, f"scored at {recency_min:.0f}m old", None
            ))
            
            # Mark event as scored
            con.execute("UPDATE events SET scored = true WHERE row_id = ?", (row_id,))
            scored_count += 1
        except Exception as e:
            log(f"Insert failed for {score_id}: {e}")
    
    # Rebuild cross-source agreement buckets
    for asset_symbol, bucket_min in bucket_updates:
        if not asset_symbol:
            continue
        try:
            # Count agreeing sources in this bucket
            rows = con.execute("""
                SELECT COUNT(DISTINCT source_id) as agreeing_sources
                FROM signal_scores
                WHERE asset_symbol = ?
                  AND date_trunc('minute', event_ts) = ?
            """, (asset_symbol, bucket_min)).fetchone()
            
            agreeing = rows[0] if rows else 0
            boost = 1.0 + min(0.35, 0.15 * max(0, agreeing - 1))
            
            # Extra boost for Whale Alert + Striker/CryptoQuant
            details = con.execute("""
                SELECT source_id FROM signal_scores
                WHERE asset_symbol = ?
                  AND date_trunc('minute', event_ts) = ?
                GROUP BY source_id
            """, (asset_symbol, bucket_min)).fetchall()
            source_ids = {r[0] for r in details}
            
            if ("whale-alert" in source_ids and 
                any(s in source_ids for s in ("striker-crypto", "cryptoquant"))):
                boost += 0.10
            
            # Update source_agreement table
            con.execute("""
                INSERT INTO source_agreement (signal_id, asset_symbol, bucket_minute, agreeing_sources, agreement_boost)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (signal_id, asset_symbol, bucket_minute) DO UPDATE SET
                    agreeing_sources = EXCLUDED.agreeing_sources,
                    agreement_boost = EXCLUDED.agreement_boost
            """, (f"bucket_{asset_symbol}_{bucket_min}", asset_symbol, bucket_min, agreeing, round(boost, 3)))
            
            # Re-score signals in this bucket with correct boost
            con.execute("""
                UPDATE signal_scores ss
                SET cross_source_boost = ?,
                    edge_score = source_prior * reported_confidence * asset_relevance * 
                                 novelty * recency_weight * ? * 
                                 false_positive_penalty * 
                                 CASE WHEN tier='lead_indicator' THEN 1.15 
                                      WHEN tier='narrative_formation' THEN 0.90 
                                      ELSE 1.00 END *
                                 CASE WHEN asset_symbol IN ('BTC','ETH','SOL') THEN 1.10 ELSE 1.00 END
                WHERE date_trunc('minute', event_ts) = ?
                  AND (asset_symbol = ? OR asset_symbol IS NULL)
            """, (round(boost, 3), round(boost, 3), bucket_min, asset_symbol))
            
        except Exception as e:
            log(f"Bucket rebuild failed for {asset_symbol}@{bucket_min}: {e}")
    
    # 8. Recompute top-20 queue
    try:
        top20 = con.execute("""
            SELECT signal_id, source_id, asset_symbol, event_type, 
                   ROUND(edge_score, 4) as edge_score, tier,
                   event_ts
            FROM signal_scores
            ORDER BY edge_score DESC, event_ts DESC
            LIMIT 20
        """).fetchall()
        
        queue_rows = []
        for r in top20:
            queue_rows.append({
                "signal_id": r[0],
                "source_id": r[1],
                "asset_symbol": r[2],
                "event_type": r[3],
                "edge_score": r[4],
                "tier": r[5],
                "event_ts": str(r[6]) if r[6] else None
            })
        
        save_top20(queue_rows)
    except Exception as e:
        log(f"Top-20 query failed: {e}")
    
    # 9. Update watermark to latest event timestamp
    try:
        latest = con.execute("SELECT MAX(timestamp) FROM events WHERE scored = true").fetchone()[0]
        if latest:
            save_watermark(str(latest))
    except:
        pass
    
    log(f"Scored {scored_count} events, {len(bucket_updates)} bucket rebuilds, top-20 written")

if __name__ == "__main__":
    run()