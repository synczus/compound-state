"""
DuckDB signal store — replay, query, and scoring history.
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

log = logging.getLogger("tv-store")

DB_PATH = Path(__file__).resolve().parent / "signal_history.duckdb"


class SignalStore:
    """Persistent DuckDB-backed store for scored signal history."""

    def __init__(self, db_path: str | Path = DB_PATH):
        try:
            import duckdb
        except ImportError:
            log.info("DuckDB not installed, using JSONL fallback")
            duckdb = None
        self._duckdb = duckdb
        self._db_path = str(db_path)
        self._jsonl_path = str(db_path) + ".jsonl" if duckdb is None else None
        self._init_db()

    def _init_db(self):
        if self._duckdb:
            conn = self._duckdb.connect(self._db_path)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scored_signals (
                    id BIGINT PRIMARY KEY,
                    scored_at TIMESTAMP,
                    symbol VARCHAR,
                    price DOUBLE,
                    direction VARCHAR,
                    score DOUBLE,
                    bucket VARCHAR,
                    trend_regime DOUBLE,
                    volume_liquidity DOUBLE,
                    setup_quality DOUBLE,
                    timeframe_alignment DOUBLE,
                    freshness DOUBLE,
                    payload JSON,
                    llm_intervened BOOLEAN DEFAULT FALSE
                )
            """)
            conn.execute("""
                CREATE SEQUENCE IF NOT EXISTS signal_id_seq START 1
            """)
            conn.close()
            log.info("DuckDB initialised at %s", self._db_path)
        else:
            # JSONL fallback
            log.info("Using JSONL fallback at %s", self._jsonl_path)

    def store(self, result: dict) -> int:
        """Store a scored result, return signal ID."""
        s = result["signal"]
        bk = result["breakdown"]

        if self._duckdb:
            return self._store_duckdb(result, s, bk)
        return self._store_jsonl(result, s, bk)

    def _store_duckdb(self, result: dict, s: dict, bk: dict) -> int:
        conn = self._duckdb.connect(self._db_path)
        conn.execute("""
            INSERT INTO scored_signals (
                id, scored_at, symbol, price, direction,
                score, bucket, trend_regime, volume_liquidity,
                setup_quality, timeframe_alignment, freshness,
                payload, llm_intervened
            ) VALUES (
                nextval('signal_id_seq'),
                ?::TIMESTAMP, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?
            )
        """, [
            result["scored_at"],
            s["symbol"], s["price"], s["direction"],
            result["score"], result["bucket"],
            bk["trend_regime"], bk["volume_liquidity"],
            bk["setup_quality"], bk["timeframe_alignment"],
            bk["freshness"],
            json.dumps(result),
            result.get("llm_intervention_needed", False),
        ])
        sid = conn.execute("SELECT currval('signal_id_seq')").fetchone()[0]
        conn.close()
        return sid

    def _store_jsonl(self, result: dict, s: dict, bk: dict) -> int:
        import uuid
        sid = str(uuid.uuid4())
        entry = {"id": sid, **result}
        with open(self._jsonl_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
        return sid

    def recent(self, limit: int = 20, min_score: float = 0) -> list[dict]:
        """Return most recent scored signals."""
        if self._duckdb:
            conn = self._duckdb.connect(self._db_path)
            rows = conn.execute("""
                SELECT id, scored_at, symbol, price, direction,
                       score, bucket, payload
                FROM scored_signals
                WHERE score >= ?
                ORDER BY id DESC
                LIMIT ?
            """, [min_score, limit]).fetchall()
            conn.close()
            return [dict(r) for r in rows]

        # JSONL fallback — read last N
        if not self._jsonl_path or not Path(self._jsonl_path).exists():
            return []
        with open(self._jsonl_path) as f:
            lines = f.readlines()
        results = []
        for line in reversed(lines[-limit:]):
            entry = json.loads(line)
            if entry.get("score", 0) >= min_score:
                results.append(entry)
        return results

    def stats(self) -> dict:
        """Aggregate stats over all scored signals."""
        if self._duckdb:
            conn = self._duckdb.connect(self._db_path)
            row = conn.execute("""
                SELECT
                    COUNT(*) as total,
                    AVG(score) as avg_score,
                    MAX(score) as max_score,
                    SUM(CASE WHEN bucket='trade' THEN 1 ELSE 0 END) as trade_count,
                    SUM(CASE WHEN bucket='watch' THEN 1 ELSE 0 END) as watch_count,
                    SUM(CASE WHEN bucket='ignore' THEN 1 ELSE 0 END) as ignore_count
                FROM scored_signals
            """).fetchone()
            conn.close()
            return {
                "total": row[0],
                "avg_score": round(row[1], 1) if row[1] else 0,
                "max_score": row[2] or 0,
                "by_bucket": {
                    "trade": row[3] or 0,
                    "watch": row[4] or 0,
                    "ignore": row[5] or 0,
                },
            }
        return {"total": 0, "avg_score": 0, "max_score": 0, "by_bucket": {"trade": 0, "watch": 0, "ignore": 0}}
