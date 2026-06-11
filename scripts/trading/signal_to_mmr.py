"""Adapter: reads DuckDB ranked queue, converts to MMR trade signals for equities/ETFs"""
import logging, sys, time
from datetime import datetime, timedelta
from pathlib import Path
import duckdb

logger = logging.getLogger(__name__)
DUCKDB_PATH = str(Path.home() / "projects/striker/data/signals.duckdb")
MMR_ROOT = str(Path.home() / "projects/metamarketrunner")

if MMR_ROOT not in sys.path:
    sys.path.insert(0, MMR_ROOT)

EQUITY_ASSET_MAP = {"SPY": "SPY", "QQQ": "QQQ", "AAPL": "AAPL", "NVDA": "NVDA", "MSFT": "MSFT"}

def get_equity_signals():
    try:
        con = duckdb.connect(DUCKDB_PATH, read_only=True)
        cutoff = (datetime.utcnow() - timedelta(seconds=300)).isoformat()
        rows = con.execute("""
            SELECT event_id, asset, signal_direction, score, source, created_at
            FROM signal_scores
            WHERE asset_type = 'equity' AND created_at >= ? AND score >= 75.0
            ORDER BY score DESC LIMIT 20
        """, [cutoff]).fetchall()
        con.close()
        return [{"event_id": r[0], "asset": r[1], "direction": r[2].upper(), "score": float(r[3]), "source": r[4]} for r in rows]
    except Exception as e:
        logger.error(f"Equity signal error: {e}"); return []

def budget_ok():
    try:
        con = duckdb.connect(DUCKDB_PATH, read_only=True)
        spent = con.execute("SELECT COALESCE(SUM(amount_usd), 0) FROM trade_log WHERE date_trunc('day', executed_at) = date_trunc('day', NOW()) AND engine = 'mmr'").fetchone()[0]
        con.close(); return (50.0 - spent) >= 5.0
    except: return False

def inject_signal(signal, paper=True):
    try:
        from metamarketrunner.strategies.ma_crossover import external_signal_override
        external_signal_override(symbol=signal["asset"], direction=signal["direction"], score=signal["score"], paper=paper)
        return True
    except ImportError:
        try:
            import requests
            requests.post("http://127.0.0.1:8081/api/v1/signal", json=signal | {"paper": paper, "source": "striker_duckdb"}, timeout=5)
            return True
        except: return False

def run(poll=30, paper=True):
    logging.basicConfig(level=logging.INFO)
    processed = set()
    while True:
        if budget_ok():
            for sig in [s for s in get_equity_signals() if s["event_id"] not in processed and s["asset"] in EQUITY_ASSET_MAP]:
                if inject_signal(sig, paper):
                    processed.add(sig["event_id"])
                    if len(processed) > 10000: processed = set(list(processed)[-5000:])
        time.sleep(poll)

if __name__ == "__main__":
    run()
