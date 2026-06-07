#!/usr/bin/env python3
"""
Post-Ingest Scoring Engine v1.0
Implements Perplexity Round 3 design: 6-step post-ingest scoring pipeline.

Scores events from the 'signals' table against the signal_scores table.
Computes recency decay, cross-source agreement boost, false-positive penalty,
tier multipliers, and bluechip boosts.

Usage:
  python3 score_batch.py                             # Score all unscored events
  python3 score_batch.py --update-agreement           # Rebuild agreement buckets
  python3 score_batch.py --queue                      # Output ranked top-20 queue
  python3 score_batch.py --reset                      # Re-score everything
  python3 score_batch.py --stats                      # Show scoring stats
"""
import argparse
import hashlib
import json
import math
import os
import sys
from datetime import datetime, timezone

KESTREL_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(KESTREL_ROOT, "signals.duckdb")
QUEUE_PATH = os.path.join(KESTREL_ROOT, "pulse", "ranked-queue.json")

# ─── Tier Configuration ─────────────────────────────────────────────────────────

TIER_OF_SOURCE = {
    # lead_indicator: on-chain data that moves before headlines
    "whale-alert":  "lead_indicator",
    "fear-greed":   "lead_indicator",
    # catalyst_confirmation: confirms a move
    "striker-crypto":  "catalyst_confirmation",
    "cointelegraph":   "catalyst_confirmation",
    "coindesk":        "catalyst_confirmation",
    "disclosetv":      "catalyst_confirmation",
    "defillama":       "catalyst_confirmation",
    # narrative_formation: explains why
    "a16z-crypto":    "narrative_formation",
    "coinstack":      "narrative_formation",
    "the-tech-buzz":  "narrative_formation",
    "bankless":       "narrative_formation",
    "tldr":           "narrative_formation",
    "hacker-news":    "narrative_formation",
    "arxiv-ai":       "narrative_formation",
    "techcrunch":     "narrative_formation",
}

TIER_HALF_LIVES = {
    "lead_indicator":        30,
    "catalyst_confirmation": 120,
    "narrative_formation":   720,
}

TIER_MULTIPLIERS = {
    "lead_indicator":        1.15,
    "catalyst_confirmation": 1.00,
    "narrative_formation":   0.90,
}

BLUECHIPS = {"BTC", "ETH", "SOL"}
BLUECHIP_MULT = 1.10

SOURCE_PRIORS = {
    "whale-alert":    0.90,
    "a16z-crypto":    0.86,
    "coinstack":      0.84,
    "the-tech-buzz":  0.80,
    "fear-greed":     0.75,
    "bankless":       0.71,
    "defillama":      0.55,
    "striker-crypto": 0.50,
    "arxiv-ai":       0.35,
    "hacker-news":    0.36,
    "coindesk":       0.25,
    "cointelegraph":  0.25,
    "tldr":           0.24,
    "techcrunch":     0.20,
    "disclosetv":     0.20,
}

# ─── Schema ─────────────────────────────────────────────────────────────────────

CREATE_SIGNAL_SCORES = """
CREATE TABLE IF NOT EXISTS signal_scores (
    score_id VARCHAR PRIMARY KEY,
    signal_id VARCHAR NOT NULL,
    source_id VARCHAR NOT NULL,
    asset_symbol VARCHAR,
    event_type VARCHAR NOT NULL,
    event_ts TIMESTAMP NOT NULL,
    ingested_ts TIMESTAMP,
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
    scored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_SOURCE_FEEDBACK = """
CREATE TABLE IF NOT EXISTS source_feedback (
    source_id VARCHAR PRIMARY KEY,
    true_positive INTEGER NOT NULL DEFAULT 0,
    false_positive INTEGER NOT NULL DEFAULT 0,
    neutral INTEGER NOT NULL DEFAULT 0,
    wolf_rate DOUBLE NOT NULL DEFAULT 0,
    updated_ts TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_SOURCE_AGREEMENT = """
CREATE TABLE IF NOT EXISTS source_agreement (
    bucket_id VARCHAR,
    signal_id VARCHAR,
    asset_symbol VARCHAR,
    bucket_minute TIMESTAMP,
    agreeing_sources INTEGER,
    agreement_boost DOUBLE,
    PRIMARY KEY(bucket_id, signal_id)
);
"""

SEED_FEEDBACK = """
INSERT OR IGNORE INTO source_feedback (source_id, true_positive, false_positive, neutral, wolf_rate, updated_ts)
VALUES
    ('whale-alert',      85,  5, 10, 0.05, CURRENT_TIMESTAMP),
    ('a16z-crypto',      60,  5, 35, 0.08, CURRENT_TIMESTAMP),
    ('coinstack',        45, 10, 45, 0.18, CURRENT_TIMESTAMP),
    ('the-tech-buzz',    40, 15, 45, 0.27, CURRENT_TIMESTAMP),
    ('fear-greed',       50,  5, 45, 0.09, CURRENT_TIMESTAMP),
    ('bankless',         55, 10, 35, 0.15, CURRENT_TIMESTAMP),
    ('defillama',        40, 10, 50, 0.20, CURRENT_TIMESTAMP),
    ('striker-crypto',   70, 15, 15, 0.18, CURRENT_TIMESTAMP),
    ('arxiv-ai',         30, 10, 60, 0.25, CURRENT_TIMESTAMP),
    ('hacker-news',      35, 15, 50, 0.30, CURRENT_TIMESTAMP),
    ('coindesk',         30, 30, 40, 0.50, CURRENT_TIMESTAMP),
    ('cointelegraph',    40, 25, 35, 0.38, CURRENT_TIMESTAMP),
    ('tldr',             50, 10, 40, 0.17, CURRENT_TIMESTAMP),
    ('techcrunch',       20, 20, 60, 0.50, CURRENT_TIMESTAMP),
    ('disclosetv',       35, 20, 45, 0.36, CURRENT_TIMESTAMP);
"""

DROP_SIGNAL_SCORES = "DROP TABLE IF EXISTS signal_scores;"
DROP_SOURCE_AGREEMENT = "DROP TABLE IF EXISTS source_agreement;"

# ─── Helpers ────────────────────────────────────────────────────────────────────


def log(msg: str):
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[scorer {ts}] {msg}", file=sys.stderr)


def make_score_id(signal_id: str, source_id: str) -> str:
    """Deterministic score_id from signal_id + source_id."""
    raw = f"{source_id}:{signal_id}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def make_bucket_id(asset_symbol: str, bucket_minute: datetime) -> str:
    return f"bucket_{asset_symbol}_{bucket_minute.strftime('%Y%m%d%H%M')}"


def db_connect():
    import duckdb
    return duckdb.connect(DB_PATH)


def init_db(con):
    """Create tables if they don't exist."""
    con.execute(CREATE_SIGNAL_SCORES)
    con.execute(CREATE_SOURCE_FEEDBACK)
    con.execute(CREATE_SOURCE_AGREEMENT)
    con.execute(SEED_FEEDBACK)


def get_unscored(con):
    """Return all signals not yet scored in signal_scores."""
    rows = con.execute("""
        SELECT s.signal_id, s.source_id, s.event_type, s.ts_ns,
               s.headline, s.body_text, s.symbols, s.confidence,
               s.magnitude, s.velocity, s.lane, s.ingested_at
        FROM signals s
        WHERE s.signal_id NOT IN (
            SELECT signal_id FROM signal_scores
        )
        ORDER BY s.ts_ns ASC
    """).fetchall()
    cols = [d[0] for d in con.execute("""
        SELECT s.signal_id, s.source_id, s.event_type, s.ts_ns,
               s.headline, s.body_text, s.symbols, s.confidence,
               s.magnitude, s.velocity, s.lane, s.ingested_at
        FROM signals s LIMIT 0
    """).description]
    return rows, cols


def get_all_signals(con):
    """Return ALL signals for --reset."""
    rows = con.execute("""
        SELECT s.signal_id, s.source_id, s.event_type, s.ts_ns,
               s.headline, s.body_text, s.symbols, s.confidence,
               s.magnitude, s.velocity, s.lane, s.ingested_at
        FROM signals s
        ORDER BY s.ts_ns ASC
    """).fetchall()
    cols = [d[0] for d in con.execute("SELECT * FROM signals LIMIT 0").description]
    return rows, cols


# ─── Scoring Core ───────────────────────────────────────────────────────────────


def compute_agreement_boost(con, source_id: str, event_ts: datetime,
                            asset_symbol: str) -> float:
    """
    Compute cross-source agreement boost.
    Bucket = 15-min window; count distinct sources; boost = 1.0 + min(0.35, 0.15*(n-1))
    Extra +0.10 if Whale Alert + Striker or Whale Alert + CryptoQuant agree.
    """
    if not asset_symbol:
        return 1.0

    bucket_min = event_ts.replace(minute=(event_ts.minute // 15) * 15,
                                  second=0, microsecond=0)
    bucket_end = bucket_min.replace(minute=bucket_min.minute + 15)

    try:
        sources = con.execute("""
            SELECT DISTINCT source_id FROM signal_scores
            WHERE asset_symbol = ?
              AND event_ts >= ?
              AND event_ts < ?
        """, (asset_symbol, bucket_min, bucket_end)).fetchall()
    except Exception:
        return 1.0

    source_ids = {r[0] for r in sources}
    agreeing = len(source_ids) + 1  # +1 for the event being scored now

    boost = 1.0 + min(0.35, 0.15 * max(0, agreeing - 1))

    # Extra +0.10 for Whale Alert + Striker / CryptoQuant
    if "whale-alert" in source_ids or source_id == "whale-alert":
        all_sources = source_ids | {source_id}
        if "striker-crypto" in all_sources or "cryptoquant" in all_sources:
            boost += 0.10

    return round(boost, 3)


def score_signal(con, row: dict, now: datetime, wolf_map: dict) -> dict | None:
    """Compute edge_score for one signal event. Returns score dict or None."""
    source_id = row["source_id"]
    event_type = row["event_type"]
    ts_ns = row["ts_ns"]
    symbols = row["symbols"]
    confidence = row["confidence"]
    magnitude = row["magnitude"]
    velocity = row["velocity"]
    signal_id = row["signal_id"]
    ingested_at = row["ingested_at"]

    # Convert ts_ns to timestamp
    try:
        event_ts = datetime.fromtimestamp(ts_ns / 1_000_000_000, tz=timezone.utc)
    except Exception:
        event_ts = now

    # Tier lookup
    tier = TIER_OF_SOURCE.get(source_id, "catalyst_confirmation")
    source_prior = SOURCE_PRIORS.get(source_id, 0.50)
    reported_confidence = float(confidence) if confidence else 0.50
    reported_confidence = max(0.0, min(1.0, reported_confidence))

    # Magnitude / velocity
    mag = float(magnitude) if magnitude else 0.0
    vel = str(velocity) if velocity else ""

    # Asset symbol: pick the first from symbols list
    symbol_list = symbols if isinstance(symbols, list) else []
    # DuckDB returns VARCHAR[] as Python list-of-strings
    asset_symbol = symbol_list[0].strip().upper() if symbol_list else None

    # Recency decay
    recency_minutes = (now - event_ts).total_seconds() / 60.0
    half_life = TIER_HALF_LIVES.get(tier, 120)
    recency_weight = math.exp(-math.log(2) * recency_minutes / max(half_life, 1))

    # Asset relevance (default 1.0 — no asset-specific enrichment yet)
    asset_relevance = 1.0
    # Novelty (default 1.0 — could be based on dedup analysis)
    novelty = 1.0

    # Cross-source agreement boost (looks at existing scores in same 15-min bucket)
    agreement_boost = compute_agreement_boost(con, source_id, event_ts, asset_symbol)

    # False-positive penalty from source_feedback
    wolf_rate = wolf_map.get(source_id, 0.0)
    false_positive_penalty = max(0.70, 1.0 - 0.40 * wolf_rate)

    # Tier multiplier
    tier_mult = TIER_MULTIPLIERS.get(tier, 1.00)

    # Bluechip multiplier
    bc_mult = BLUECHIP_MULT if asset_symbol in BLUECHIPS else 1.00

    # Final edge score
    edge_score = (
        source_prior *
        reported_confidence *
        asset_relevance *
        novelty *
        recency_weight *
        agreement_boost *
        false_positive_penalty *
        tier_mult *
        bc_mult
    )

    score_id = make_score_id(signal_id, source_id)

    rationale_parts = []
    if tier_mult != 1.0:
        rationale_parts.append(f"tier={tier}×{tier_mult:.2f}")
    if bc_mult != 1.0:
        rationale_parts.append(f"bluechip×{bc_mult:.2f}")
    if agreement_boost > 1.0:
        rationale_parts.append(f"agreement×{agreement_boost:.2f}")
    if false_positive_penalty < 1.0:
        rationale_parts.append(f"fp_penalty×{false_positive_penalty:.2f}")
    if recency_weight < 0.5:
        rationale_parts.append(f"decay_to_{recency_weight:.2f}")
    rationale = "; ".join(rationale_parts) if rationale_parts else "baseline"

    return {
        "score_id": score_id,
        "signal_id": signal_id,
        "source_id": source_id,
        "asset_symbol": asset_symbol,
        "event_type": event_type,
        "event_ts": event_ts,
        "ingested_ts": ingested_at if ingested_at else now,
        "source_prior": source_prior,
        "reported_confidence": reported_confidence,
        "magnitude": mag,
        "velocity": vel,
        "asset_relevance": asset_relevance,
        "novelty": novelty,
        "recency_minutes": round(recency_minutes, 2),
        "recency_weight": round(recency_weight, 4),
        "cross_source_boost": agreement_boost,
        "false_positive_penalty": round(false_positive_penalty, 4),
        "edge_score": round(edge_score, 4),
        "tier": tier,
        "rationale": rationale,
    }


def insert_score(con, score: dict):
    """Upsert one score row into signal_scores."""
    con.execute("""
        INSERT INTO signal_scores (
            score_id, signal_id, source_id, asset_symbol, event_type,
            event_ts, ingested_ts, source_prior, reported_confidence,
            magnitude, velocity, asset_relevance, novelty,
            recency_minutes, recency_weight, cross_source_boost,
            false_positive_penalty, edge_score, tier, rationale, scored_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                  CURRENT_TIMESTAMP)
        ON CONFLICT (score_id) DO UPDATE SET
            recency_minutes = EXCLUDED.recency_minutes,
            recency_weight = EXCLUDED.recency_weight,
            cross_source_boost = EXCLUDED.cross_source_boost,
            false_positive_penalty = EXCLUDED.false_positive_penalty,
            edge_score = EXCLUDED.edge_score,
            rationale = EXCLUDED.rationale,
            scored_at = CURRENT_TIMESTAMP
    """, (
        score["score_id"], score["signal_id"], score["source_id"],
        score["asset_symbol"], score["event_type"], score["event_ts"],
        score["ingested_ts"], score["source_prior"],
        score["reported_confidence"], score["magnitude"], score["velocity"],
        score["asset_relevance"], score["novelty"], score["recency_minutes"],
        score["recency_weight"], score["cross_source_boost"],
        score["false_positive_penalty"], score["edge_score"],
        score["tier"], score["rationale"],
    ))


# ─── Agreement Buckets ─────────────────────────────────────────────────────────


def rebuild_agreement_buckets(con):
    """
    Rebuild source_agreement table from scratch.
    Bucket events by 15-min windows per asset_symbol.
    Count distinct sources; compute agreement_boost.
    """
    log("Rebuilding agreement buckets...")

    con.execute("DELETE FROM source_agreement")

    # Get all scored events with asset symbols grouped into 15-min buckets
    buckets = con.execute("""
        SELECT DISTINCT
            asset_symbol,
            date_trunc('minute', event_ts) - INTERVAL (EXTRACT(MINUTE FROM event_ts)::INT % 15) MINUTE AS bucket_minute
        FROM signal_scores
        WHERE asset_symbol IS NOT NULL
          AND asset_symbol != ''
    """).fetchall()

    updated = 0
    for asset_symbol, bucket_min in buckets:
        # Count distinct sources in this bucket
        sources = con.execute("""
            SELECT DISTINCT source_id
            FROM signal_scores
            WHERE asset_symbol = ?
              AND date_trunc('minute', event_ts) >= ?
              AND date_trunc('minute', event_ts) < ? + INTERVAL '15 minutes'
        """, (asset_symbol, bucket_min, bucket_min)).fetchall()

        source_ids = {r[0] for r in sources}
        agreeing = len(source_ids)

        boost = 1.0 + min(0.35, 0.15 * max(0, agreeing - 1))

        # Extra boost for Whale Alert combinations
        if "whale-alert" in source_ids:
            if "striker-crypto" in source_ids or "cryptoquant" in source_ids:
                boost += 0.10

        boost = round(boost, 3)

        # Get all signal_ids in this bucket
        signals = con.execute("""
            SELECT signal_id
            FROM signal_scores
            WHERE asset_symbol = ?
              AND date_trunc('minute', event_ts) >= ?
              AND date_trunc('minute', event_ts) < ? + INTERVAL '15 minutes'
        """, (asset_symbol, bucket_min, bucket_min)).fetchall()

        bucket_id = make_bucket_id(asset_symbol, bucket_min)

        for sig in signals:
            signal_id = sig[0]
            try:
                con.execute("""
                    INSERT INTO source_agreement (
                        bucket_id, signal_id, asset_symbol,
                        bucket_minute, agreeing_sources, agreement_boost
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT (bucket_id, signal_id) DO UPDATE SET
                        agreeing_sources = EXCLUDED.agreeing_sources,
                        agreement_boost = EXCLUDED.agreement_boost
                """, (bucket_id, signal_id, asset_symbol,
                      bucket_min, agreeing, boost))
                updated += 1

                # Also update cross_source_boost in signal_scores
                con.execute("""
                    UPDATE signal_scores
                    SET cross_source_boost = ?
                    WHERE signal_id = ? AND asset_symbol = ?
                """, (boost, signal_id, asset_symbol))
            except Exception as e:
                log(f"Bucket insert error for {signal_id}: {e}")

    log(f"Agreement buckets rebuilt: {updated} entries")


# ─── Queue Output ───────────────────────────────────────────────────────────────


def write_ranked_queue(con):
    """Query top 20 signals and write to pulse/ranked-queue.json."""
    rows = con.execute("""
        SELECT signal_id, source_id, asset_symbol, event_type,
               event_ts, edge_score
        FROM signal_scores
        ORDER BY edge_score DESC, event_ts DESC
        LIMIT 20
    """).fetchall()

    queue = []
    for r in rows:
        queue.append({
            "signal_id": r[0],
            "source_id": r[1],
            "asset_symbol": r[2],
            "event_type": r[3],
            "event_ts": str(r[4]) if r[4] else None,
            "edge_score": round(r[5], 4),
        })

    os.makedirs(os.path.dirname(QUEUE_PATH), exist_ok=True)
    with open(QUEUE_PATH, "w") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "queue": queue,
            "count": len(queue),
        }, f, indent=2)

    log(f"Ranked queue written: {len(queue)} signals to {QUEUE_PATH}")

    # Also print to stdout
    if queue:
        print(f"\n{'Rank':>4s}  {'Signal ID':16s}  {'Source':20s}  {'Asset':8s}  "
              f"{'Type':22s}  {'Event TS':28s}  {'Score':>8s}")
        print("-" * 120)
        for i, q in enumerate(queue, 1):
            print(f"{i:4d}  {q['signal_id']:16s}  {q['source_id']:20s}  "
                  f"{(q['asset_symbol'] or 'N/A'):8s}  {q['event_type']:22s}  "
                  f"{q['event_ts']:28s}  {q['edge_score']:8.4f}")

    return queue


# ─── Stats ──────────────────────────────────────────────────────────────────────


def print_stats(con):
    """Print scoring stats: unscored count, breakdown by source_id and tier."""
    total_signals = con.execute("SELECT COUNT(*) FROM signals").fetchone()[0]
    total_scored = con.execute("SELECT COUNT(*) FROM signal_scores").fetchone()[0]
    unscored = total_signals - con.execute("""
        SELECT COUNT(*) FROM signal_scores ss
        INNER JOIN signals s ON ss.signal_id = s.signal_id
    """).fetchone()[0]

    print("=" * 70)
    print("  SIGNAL SCORING STATS")
    print("=" * 70)
    print(f"  Total signals:     {total_signals:>6d}")
    print(f"  Total scores:      {total_scored:>6d}")
    print(f"  Unscored (matching signals table): {unscored:>6d}")
    print()

    # Score counts by source_id
    print(f"  {'Source ID':25s}  {'Scored':>8s}  {'Avg Edge':>10s}  {'Tier':22s}")
    print(f"  {'-'*25}  {'-'*8}  {'-'*10}  {'-'*22}")
    rows = con.execute("""
        SELECT source_id, COUNT(*), ROUND(AVG(edge_score), 4), tier
        FROM signal_scores
        GROUP BY source_id, tier
        ORDER BY COUNT(*) DESC
    """).fetchall()
    for sid, cnt, avg_edge, tier in rows:
        print(f"  {sid:25s}  {cnt:8d}  {avg_edge:>10.4f}  {tier:22s}")

    # Score counts by tier
    print()
    print(f"  {'Tier':22s}  {'Scored':>8s}  {'Avg Edge':>10s}")
    print(f"  {'-'*22}  {'-'*8}  {'-'*10}")
    rows = con.execute("""
        SELECT tier, COUNT(*), ROUND(AVG(edge_score), 4)
        FROM signal_scores
        GROUP BY tier
        ORDER BY AVG(edge_score) DESC
    """).fetchall()
    for tier, cnt, avg_edge in rows:
        print(f"  {tier:22s}  {cnt:8d}  {avg_edge:>10.4f}")

    # Source feedback status
    print()
    print(f"  {'Source ID':25s}  {'Wolf Rate':>10s}  {'FP Penalty':>11s}")
    print(f"  {'-'*25}  {'-'*10}  {'-'*11}")
    rows = con.execute("""
        SELECT source_id, wolf_rate,
               ROUND(MAX(0.70, 1.0 - 0.40 * wolf_rate), 4) AS fp_penalty
        FROM source_feedback
        ORDER BY wolf_rate DESC
    """).fetchall()
    for sid, wolf, penalty in rows:
        print(f"  {sid:25s}  {wolf:>10.3f}  {penalty:>11.4f}")

    # Agreement bucket count
    bucket_count = con.execute("SELECT COUNT(DISTINCT bucket_id) FROM source_agreement").fetchone()[0]
    print()
    print(f"  Agreement buckets: {bucket_count}")
    print("=" * 70)


# ─── Main Logic ─────────────────────────────────────────────────────────────────


def score_all(con, reset: bool = False):
    """Score all unscored (or all if reset=True) signals."""
    now = datetime.now(timezone.utc)

    # Load wolf_map
    wolf_rows = con.execute(
        "SELECT source_id, wolf_rate FROM source_feedback"
    ).fetchall()
    wolf_map = {r[0]: float(r[1]) for r in wolf_rows}

    if reset:
        log("Reset mode: clearing all signal_scores...")
        con.execute("DELETE FROM signal_scores")
        rows, cols = get_all_signals(con)
    else:
        rows, cols = get_unscored(con)

    if not rows:
        log("No new signals to score.")
        return 0

    log(f"Scoring {len(rows)} signals...")

    scored = 0
    for r in rows:
        row_dict = dict(zip(cols, r))
        score = score_signal(con, row_dict, now, wolf_map)
        if score:
            insert_score(con, score)
            scored += 1

    log(f"Scored {scored} signals")

    # Rebuild agreement buckets
    rebuild_agreement_buckets(con)

    return scored


def main():
    parser = argparse.ArgumentParser(
        description="Post-Ingest Scoring Engine for the Signal Pipeline"
    )
    parser.add_argument("--update-agreement", action="store_true",
                        help="Rebuild agreement buckets only")
    parser.add_argument("--queue", action="store_true",
                        help="Output the ranked queue only")
    parser.add_argument("--reset", action="store_true",
                        help="Re-score everything (for schema changes)")
    parser.add_argument("--stats", action="store_true",
                        help="Show scoring stats")
    args = parser.parse_args()

    import duckdb

    con = db_connect()
    init_db(con)

    if args.stats:
        print_stats(con)
    elif args.update_agreement:
        rebuild_agreement_buckets(con)
        con.close()
        log("Agreement buckets rebuilt.")
    elif args.queue:
        write_ranked_queue(con)
        con.close()
    elif args.reset:
        scored = score_all(con, reset=True)
        write_ranked_queue(con)
        con.close()
        log(f"Done. Scored {scored} total signals, queue written.")
    else:
        # Default: score all unscored
        scored = score_all(con, reset=False)
        write_ranked_queue(con)
        con.close()
        log(f"Done. Scored {scored} new signals, queue written.")


if __name__ == "__main__":
    main()
