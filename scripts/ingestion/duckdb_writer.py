#!/usr/bin/env python3
"""
DuckDB Ingestion Writer v0.2 — writes routed signal events to DuckDB.

Creates /home/synczus/kestrel/signals.duckdb on first run.
Table schema per the signal pipeline contract.

Usage:
  cat events.jsonl | python3 duckdb_writer.py --stdin              ← stdin insert
  python3 duckdb_writer.py --from-dir /path/to/pulse/              ← batch from pulse/ dir
  python3 duckdb_writer.py --query "SELECT ..."                    ← query and print results
  python3 duckdb_writer.py --stats                                 ← row counts per source_id
"""
import argparse
import hashlib
import json
import os
import sys
import duckdb

KESTREL_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(KESTREL_ROOT, "signals.duckdb")

TABLE = "signals"

CREATE_SQL = f"""
CREATE TABLE IF NOT EXISTS {TABLE} (
    signal_id VARCHAR PRIMARY KEY,
    source_id VARCHAR,
    event_type VARCHAR,
    ts_ns BIGINT,
    headline VARCHAR,
    body_text VARCHAR,
    symbols VARCHAR[],  -- DuckDB list
    confidence DOUBLE,
    magnitude DOUBLE,
    velocity VARCHAR,
    source_url VARCHAR,
    raw_message_id VARCHAR,
    lane VARCHAR,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""


def get_db():
    """Return a DuckDB connection (simple single-writer pattern)."""
    return duckdb.connect(DB_PATH)


def init_db():
    """Create the signals table if it doesn't exist."""
    con = get_db()
    con.execute(CREATE_SQL)
    con.close()


def make_signal_id(event: dict) -> str:
    """
    signal_id = hash(source_id + raw_message_id + ts_ns) truncated to 16 chars.
    Handles both router output (flat fields) and raw contract events.
    """
    source_id = event.get("source_id", "")
    ts_ns = event.get("ts_ns", event.get("timestamp", "0"))
    # Get raw_message_id from provenance or direct
    provenance = event.get("provenance", {})
    raw_message_id = event.get("raw_message_id", provenance.get("raw_message_id", ""))

    raw = f"{source_id}:{raw_message_id}:{ts_ns}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def extract_fields(event: dict) -> dict:
    """
    Extract fields from a signal event.
    Handles both router output (flat fields) and raw contract events.
    """
    # Fields that may be flat (router output) or nested (raw event)
    source_id = event.get("source_id", "")
    event_type = event.get("event_type", "")
    ts_ns = event.get("ts_ns", event.get("timestamp", 0))
    lane = event.get("lane", "")
    signal_id = event.get("signal_id", make_signal_id(event))

    # Payload fields
    payload = event.get("payload", {})
    if not isinstance(payload, dict):
        payload = {}

    headline = event.get("headline", payload.get("headline", ""))
    # body_text: router output doesn't have it; raw events have it in payload.body
    body_text_raw = event.get("body_text", payload.get("body", ""))
    # body is sometimes a JSON string — store the raw text
    body_text = body_text_raw

    symbols = event.get("symbols", payload.get("symbols", []))

    # Metrics
    metrics = event.get("metrics", payload.get("metrics", {}))

    # Handle case where metrics values might come from the flat event dict
    confidence = event.get("confidence") if event.get("confidence") is not None else metrics.get("confidence", 0.0)
    if confidence is None:
        confidence = 0.0
    confidence = float(confidence)

    magnitude = event.get("magnitude") if event.get("magnitude") is not None else metrics.get("magnitude", 0.0)
    if magnitude is None:
        magnitude = 0.0
    magnitude = float(magnitude)

    velocity = event.get("velocity", metrics.get("velocity", ""))

    # Provenance
    provenance = event.get("provenance", {})
    if not isinstance(provenance, dict):
        provenance = {}
    source_url = event.get("source_url", provenance.get("source_url", ""))
    raw_message_id = event.get("raw_message_id", provenance.get("raw_message_id", ""))

    return {
        "signal_id": signal_id,
        "source_id": source_id,
        "event_type": event_type,
        "ts_ns": int(ts_ns),
        "headline": str(headline),
        "body_text": str(body_text),
        "symbols": symbols if isinstance(symbols, list) else [],
        "confidence": confidence,
        "magnitude": magnitude,
        "velocity": str(velocity),
        "source_url": str(source_url),
        "raw_message_id": str(raw_message_id),
        "lane": str(lane),
    }


def ingest_event(con, event: dict) -> bool:
    """Insert one event into the signals table. Returns True if inserted."""
    fields = extract_fields(event)
    try:
        con.execute(
            f"""INSERT OR IGNORE INTO {TABLE}
                (signal_id, source_id, event_type, ts_ns, headline, body_text,
                 symbols, confidence, magnitude, velocity, source_url,
                 raw_message_id, lane)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                fields["signal_id"],
                fields["source_id"],
                fields["event_type"],
                fields["ts_ns"],
                fields["headline"],
                fields["body_text"],
                fields["symbols"],
                fields["confidence"],
                fields["magnitude"],
                fields["velocity"],
                fields["source_url"],
                fields["raw_message_id"],
                fields["lane"],
            ],
        )
        return True
    except Exception as e:
        print(f"[duckdb] ERROR inserting event: {e}", file=sys.stderr)
        return False


def ingest_lines(lines) -> tuple[int, int, int]:
    """Insert events from JSONL lines. Returns (processed, inserted, skipped)."""
    con = get_db()
    processed = 0
    inserted = 0
    skipped = 0

    for line in lines:
        line = line.strip()
        if not line:
            continue
        processed += 1
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            skipped += 1
            continue
        if ingest_event(con, event):
            inserted += 1
        else:
            skipped += 1

    con.close()
    return processed, inserted, skipped


def ingest_from_dir(pulse_dir: str) -> tuple[int, int, int]:
    """
    Batch-process all *-inbox.jsonl files in the given directory.
    Returns (processed, inserted, skipped).
    """
    total_processed = 0
    total_inserted = 0
    total_skipped = 0

    if not os.path.isdir(pulse_dir):
        print(f"[duckdb] Directory not found: {pulse_dir}", file=sys.stderr)
        return 0, 0, 0

    con = get_db()
    for fname in sorted(os.listdir(pulse_dir)):
        if not fname.endswith("-inbox.jsonl") and not fname.endswith(".jsonl"):
            continue
        fpath = os.path.join(pulse_dir, fname)
        print(f"[duckdb] Processing: {fname}", file=sys.stderr)
        with open(fpath) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    total_skipped += 1
                    continue
                total_processed += 1
                if ingest_event(con, event):
                    total_inserted += 1
                else:
                    total_skipped += 1
    con.close()

    return total_processed, total_inserted, total_skipped


def run_query(query: str):
    """Execute a query and print results as a table."""
    con = get_db()
    try:
        result = con.execute(query)
        rows = result.fetchall()
        if result.description:
            cols = [d[0] for d in result.description]
            # Header
            print(" | ".join(cols))
            # Separator
            seps = []
            for c in cols:
                seps.append("-" * max(3, len(c)))
            print("-|-".join(seps))
            # Rows
            for row in rows:
                vals = []
                for v in row:
                    s = str(v) if v is not None else "NULL"
                    if len(s) > 60:
                        s = s[:57] + "..."
                    vals.append(s)
                print(" | ".join(vals))
        else:
            print(f"[duckdb] Query executed, {result} affected")
    except Exception as e:
        print(f"[duckdb] Query error: {e}", file=sys.stderr)
    con.close()


def print_stats():
    """Print row counts per source_id."""
    con = get_db()
    try:
        rows = con.execute(
            f"SELECT source_id, COUNT(*) as cnt FROM {TABLE} GROUP BY source_id ORDER BY cnt DESC"
        ).fetchall()
        print("[duckdb] Signal table stats:")
        print(f"  {'Source':25s} {'Count':>8s}")
        print(f"  {'-'*25} {'-'*8}")
        total = 0
        for sid, cnt in rows:
            print(f"  {sid:25s} {cnt:8d}")
            total += cnt
        print(f"  {'-'*25} {'-'*8}")
        print(f"  {'TOTAL':25s} {total:8d}")
    except Exception as e:
        print(f"[duckdb] Stats error: {e}", file=sys.stderr)
    con.close()


def main():
    parser = argparse.ArgumentParser(description="Signal Pipeline DuckDB Writer")
    parser.add_argument("--stdin", action="store_true",
                        help="Read JSONL from stdin and insert into DB")
    parser.add_argument("--from-dir", type=str,
                        help="Batch-process all *-inbox.jsonl files in a pulse directory")
    parser.add_argument("--query", type=str,
                        help="Run a SQL query against the signals table")
    parser.add_argument("--stats", action="store_true",
                        help="Print table row counts per source_id")
    args = parser.parse_args()

    # Always ensure DB+table exists
    init_db()

    if args.stdin:
        processed, inserted, skipped = ingest_lines(sys.stdin)
        print(f"[duckdb] stdin: {processed} processed, {inserted} inserted, {skipped} skipped",
              file=sys.stderr)
    elif args.from_dir:
        processed, inserted, skipped = ingest_from_dir(args.from_dir)
        print(f"[duckdb] from-dir: {processed} processed, {inserted} inserted, {skipped} skipped",
              file=sys.stderr)
    elif args.query:
        run_query(args.query)
    elif args.stats:
        print_stats()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()