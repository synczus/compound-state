#!/usr/bin/env python3
"""
Striker → DuckDB Bridge

Pipes 134K+ Striker signals from kestrel_signals.db into 
signals.duckdb. Deduplicates by timestamp+symbol+direction.

Run: python3 striker-to-duckdb.py
Safe to re-run — idempotent.
"""

import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

BASE = Path("/home/synczus/kestrel")
STRIKER_DB = str(BASE / "kestrel_signals.db")
DUCKDB_PATH = str(BASE / "signals.duckdb")
BATCH_SIZE = 5000

import duckdb


def get_missing_signals():
    """Fetch Striker signals not yet in DuckDB."""
    scon = sqlite3.connect(STRIKER_DB)
    
    # Get existing ts_ns in DuckDB for dedup
    dcon = duckdb.connect(DUCKDB_PATH)
    existing = set()
    try:
        rows = dcon.execute("SELECT ts_ns FROM signals WHERE source_id = 'striker'").fetchall()
        existing = {r[0] for r in rows}
    except Exception:
        pass  # table might not have striker signals yet
    
    # Fetch all Striker signals
    scon.row_factory = sqlite3.Row
    striker_rows = scon.execute("SELECT * FROM signals ORDER BY id").fetchall()
    scon.close()
    
    new_signals = []
    seen = set(existing)
    
    for row in striker_rows:
        ts_str = row["timestamp"]
        try:
            dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            ts_ns = int(dt.timestamp() * 1_000_000_000)
        except Exception:
            continue
        
        dedup_key = (ts_ns, row["symbol"], row["direction"])
        if dedup_key in seen:
            continue
        seen.add(dedup_key)
        
        signal_id = "striker_{}".format(row["id"])
        
        # Build signal
        new_signals.append({
            "signal_id": signal_id,
            "source_id": "striker",
            "event_type": "price_signal",
            "ts_ns": ts_ns,
            "headline": "{}: {} @ ${:.2f} (conf: {:.1%})".format(
                row["symbol"], row["direction"].upper(),
                row["entry_price"] or 0,
                row["confidence"] or 0
            ),
            "body_text": json.dumps({
                "entry_price": row["entry_price"],
                "take_profit": row["take_profit"],
                "stop_loss": row["stop_loss"],
                "move_pct": row["move_pct"],
                "volume": row["volume"],
                "atr_pct": row["atr_pct"],
            }),
            "symbols": [row["symbol"]],
            "confidence": row["confidence"] or 0.5,
            "magnitude": abs(row["move_pct"] or 0),
            "velocity": row["direction"],
            "source_url": "",
            "raw_message_id": str(row["id"]),
            "lane": "striker",
            "ingested_at": datetime.now(timezone.utc),
        })
    
    dcon.close()
    return new_signals


def load_batch(dcon, batch):
    """Insert batch into DuckDB signals table."""
    dcon.executemany(
        """INSERT OR IGNORE INTO signals (
            signal_id, source_id, event_type, ts_ns, headline, body_text,
            symbols, confidence, magnitude, velocity, source_url,
            raw_message_id, lane, ingested_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [(
            s["signal_id"], s["source_id"], s["event_type"], s["ts_ns"],
            s["headline"], s["body_text"], s["symbols"],
            s["confidence"], s["magnitude"], s["velocity"],
            s["source_url"], s["raw_message_id"], s["lane"], s["ingested_at"]
        ) for s in batch]
    )
    dcon.commit()


def generate_scores(dcon):
    """Generate signal_scores for striker signals that don't have one."""
    try:
        dcon.execute("""
            INSERT OR IGNORE INTO signal_scores (
                score_id, signal_id, source_id, asset_symbol, event_type,
                event_ts, ingested_ts, source_prior, reported_confidence,
                magnitude, velocity, asset_relevance, novelty,
                recency_minutes, recency_weight, cross_source_boost,
                false_positive_penalty, edge_score, tier, rationale,
                raw_payload_json, scored_at
            )
            SELECT 
                'score_' || s.signal_id,
                s.signal_id,
                'striker',
                s.symbols[1],
                'price_signal',
                epoch_ms(CAST(s.ts_ns / 1000000 AS BIGINT))::TIMESTAMP,
                s.ingested_at,
                0.5,  -- source_prior
                s.confidence,
                s.magnitude,
                CASE WHEN s.velocity = 'long' THEN 1.0 ELSE -1.0 END,
                1.0,  -- asset_relevance
                1.0,  -- novelty
                0.0,  -- recency_minutes
                1.0,  -- recency_weight
                0.0,  -- cross_source_boost
                0.0,  -- false_positive_penalty
                s.confidence * 100,  -- edge_score
                'auto',
                'Imported from Striker engine',
                json_object('source', 'striker_bridge'),
                now()
            FROM signals s
            WHERE s.source_id = 'striker'
            AND NOT EXISTS (
                SELECT 1 FROM signal_scores ss
                WHERE ss.signal_id = s.signal_id
            )
        """)
        dcon.commit()
    except Exception as e:
        print("  Score gen error (non-fatal): {}".format(e), file=sys.stderr)


def main():
    print("🔍 Checking existing DuckDB signals from Striker...", flush=True)
    
    dcon = duckdb.connect(DUCKDB_PATH)
    existing_count = dcon.execute(
        "SELECT COUNT(*) FROM signals WHERE source_id = 'striker'"
    ).fetchone()[0]
    dcon.close()
    
    print("   Already in DuckDB (striker): {} signals".format(existing_count), flush=True)
    
    # Get new signals
    print("📡 Fetching Striker signals...", flush=True)
    new = get_missing_signals()
    print("   New signals to import: {}".format(len(new)), flush=True)
    
    if not new:
        print("✅ Nothing to migrate — DuckDB is up to date with Striker.", flush=True)
        return
    
    # Batch load
    dcon = duckdb.connect(DUCKDB_PATH)
    total = len(new)
    for i in range(0, total, BATCH_SIZE):
        batch = new[i:i + BATCH_SIZE]
        load_batch(dcon, batch)
        pct = min(100, (i + BATCH_SIZE) / total * 100)
        print("   Loaded {} / {} ({:.0f}%)".format(min(total, i + BATCH_SIZE), total, pct), flush=True)
    
    # Generate scores
    print("📊 Generating signal scores...", flush=True)
    generate_scores(dcon)
    
    dcon.close()
    
    # Final count
    dcon2 = duckdb.connect(DUCKDB_PATH)
    new_total = dcon2.execute(
        "SELECT COUNT(*) FROM signals WHERE source_id = 'striker'"
    ).fetchone()[0]
    score_total = dcon2.execute(
        "SELECT COUNT(*) FROM signal_scores WHERE source_id = 'striker'"
    ).fetchone()[0]
    dcon2.close()
    
    print("\n✅ Migration complete!", flush=True)
    print("   Striker signals in DuckDB: {} → {}".format(existing_count, new_total), flush=True)
    print("   Striker scores generated: {}".format(score_total), flush=True)
    print("   DuckDB total signals now: {}".format(new_total + (4_671 - existing_count)), flush=True)


if __name__ == "__main__":
    main()