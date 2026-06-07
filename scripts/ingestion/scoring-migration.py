#!/usr/bin/env python3
"""
DuckDB Scoring Migration — adds 3 tables: signal_scores, source_feedback, source_agreement
Runs after existing duckdb_writer.py creates the base events table.
"""
import os, sys, json
from datetime import datetime, timezone

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "signals.duckdb")
DB = os.path.normpath(DB)
CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "manifests", "coordination.yaml")

MIGRATIONS = """
-- Table 1: Scored signals with cross-source agreement & decay
CREATE TABLE IF NOT EXISTS signal_scores (
    score_id VARCHAR PRIMARY KEY,
    signal_id VARCHAR NOT NULL,
    source_id VARCHAR NOT NULL,
    asset_symbol VARCHAR,
    event_type VARCHAR NOT NULL,
    event_ts TIMESTAMP NOT NULL,
    ingested_ts TIMESTAMP NOT NULL DEFAULT now(),
    source_prior DOUBLE NOT NULL,
    reported_confidence DOUBLE NOT NULL,
    magnitude DOUBLE,
    velocity DOUBLE,
    asset_relevance DOUBLE NOT NULL DEFAULT 1.0,
    novelty DOUBLE NOT NULL DEFAULT 1.0,
    recency_minutes DOUBLE NOT NULL,
    recency_weight DOUBLE NOT NULL,
    cross_source_boost DOUBLE NOT NULL DEFAULT 1.0,
    false_positive_penalty DOUBLE NOT NULL DEFAULT 1.0,
    edge_score DOUBLE NOT NULL,
    tier VARCHAR NOT NULL,
    rationale VARCHAR,
    raw_payload_json JSON,
    UNIQUE(signal_id, source_id)
);

-- Table 2: Source false-positive tracking
CREATE TABLE IF NOT EXISTS source_feedback (
    source_id VARCHAR PRIMARY KEY,
    true_positive INTEGER NOT NULL DEFAULT 0,
    false_positive INTEGER NOT NULL DEFAULT 0,
    neutral INTEGER NOT NULL DEFAULT 0,
    wolf_rate DOUBLE NOT NULL DEFAULT 0,
    updated_ts TIMESTAMP NOT NULL DEFAULT now()
);

-- Table 3: Cross-source agreement buckets
CREATE TABLE IF NOT EXISTS source_agreement (
    signal_id VARCHAR,
    asset_symbol VARCHAR,
    bucket_minute TIMESTAMP,
    agreeing_sources INTEGER,
    agreement_boost DOUBLE,
    PRIMARY KEY(signal_id, asset_symbol, bucket_minute)
);
"""

# Seed source_feedback with defaults from coordination.yaml
DEFAULT_FEEDBACK = """
INSERT OR IGNORE INTO source_feedback (source_id, true_positive, false_positive, neutral, wolf_rate, updated_ts)
VALUES
    ('whale-alert', 85, 5, 10, 0.05, now()),
    ('striker-crypto', 70, 15, 15, 0.18, now()),
    ('cointelegraph', 40, 25, 35, 0.38, now()),
    ('disclosetv', 35, 20, 45, 0.36, now()),
    ('tldr', 50, 10, 40, 0.17, now()),
    ('coindesk', 30, 30, 40, 0.50, now()),
    ('techcrunch', 20, 20, 60, 0.50, now()),
    ('a16z-crypto', 60, 5, 35, 0.08, now()),
    ('coinstack', 45, 10, 45, 0.18, now()),
    ('the-tech-buzz', 40, 15, 45, 0.27, now()),
    ('binance-killers', 10, 40, 50, 0.80, now());
"""

try:
    import duckdb
    con = duckdb.connect(DB)
    
    # Run migrations
    for stmt in MIGRATIONS.split(';'):
        stmt = stmt.strip()
        if stmt:
            con.execute(stmt)
    
    # Seed feedback defaults
    con.execute(DEFAULT_FEEDBACK)
    
    # Verify
    tables = con.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='main'").fetchall()
    print(f"[scoring] Tables created: {[t[0] for t in tables]}")
    
    # Counts
    for t in ['signal_scores', 'source_feedback', 'source_agreement']:
        cnt = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"[scoring]  {t}: {cnt} rows")
    
    # Show source feedback
    print("\n[scoring] Source default wolf_rates:")
    rows = con.execute("SELECT source_id, wolf_rate, true_positive, false_positive FROM source_feedback ORDER BY wolf_rate DESC").fetchall()
    for source, wolf, tp, fp in rows:
        print(f"  {source}: wolf_rate={wolf:.2f}, TP={tp}, FP={fp}")
        
except ImportError:
    print("[scoring] duckdb module not installed. Install: pip3 install duckdb")
    sys.exit(1)
except Exception as e:
    print(f"[scoring] Error: {e}")
    sys.exit(1)
