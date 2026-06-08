#!/usr/bin/env python3
"""
DuckDB Maintenance — runs every 30 minutes via cron
Performs: CHECKPOINT, VACUUM ANALYZE on hot tables
Cost: $0 (no LLM calls)
"""
import os, sys

DB = os.path.expanduser("~/kestrel/signals.duckdb")

try:
    import duckdb
except:
    print("[maintenance] duckdb not available")
    sys.exit(0)

if not os.path.exists(DB):
    print("[maintenance] No DuckDB yet — skipping")
    sys.exit(0)

try:
    con = duckdb.connect(DB)
    
    # Step 1: CHECKPOINT — flushes WAL, reclaims space from deletes
    con.execute("CHECKPOINT")
    
    # Step 2: Refresh statistics on hot tables
    for table in ["events", "signal_scores", "source_feedback", "source_agreement"]:
        try:
            con.execute(f"VACUUM ANALYZE {table}")
        except:
            pass  # Table may not exist yet
    
    # Verify
    sizes = con.execute("""
        SELECT table_name, 
               ROUND(estimated_size::float / 1024, 1) as size_kb
        FROM duckdb_tables()
        ORDER BY estimated_size DESC
    """).fetchall()
    
    con.close()
    print(f"[maintenance] CHECKPOINT + ANALYZE done")
    for table, size in sizes:
        print(f"  {table}: {size} KB")
    
except Exception as e:
    print(f"[maintenance] Error: {e}")
    sys.exit(1)