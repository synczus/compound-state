"""
Striker Bridge — full wiring:
 DuckDB signal_scores -> confidence threshold -> position size -> POST FreqTrade API
 -> journal to DuckDB trade_log
"""
import json, logging, time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import duckdb, requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)

DUCKDB_PATH = str(Path.home() / "kestrel/data/striker.duckdb")
FT_API_BASE = "http://127.0.0.1:8080/api/v1"
FT_USER = "ftuser"
FT_PASS = "ftpass123"
SOURCE_PRIORS = {
    "whale-alert": 0.384, "defillama": 0.340,
    "telegram-@AIHangout": 0.161, "telegram-@GemHunterrs": 0.153,
    "telegram-@BinanceKillers": 0.121, "telegram-@disclosetv": 0.121,
    "generic-unlabeled": 0.061, "pump-channel-generic": 0.047,
}
FT_PAIR_MAP = {"BTC": "BTC/USDT:USDT", "ETH": "ETH/USDT:USDT", "SOL": "SOL/USDT:USDT"}

def ft_get(endpoint):
    try:
        r = requests.get(f"{FT_API_BASE}{endpoint}", auth=HTTPBasicAuth(FT_USER, FT_PASS), timeout=5)
        r.raise_for_status(); return r.json()
    except Exception as e:
        logger.error(f"FT GET {endpoint} failed: {e}"); return None

def ft_post(endpoint, payload):
    try:
        r = requests.post(f"{FT_API_BASE}{endpoint}", json=payload, auth=HTTPBasicAuth(FT_USER, FT_PASS), timeout=5)
        r.raise_for_status(); return r.json()
    except Exception as e:
        logger.error(f"FT POST {endpoint} failed: {e}"); return None

def get_daily_spend(engine="freqtrade"):
    try:
        con = duckdb.connect(DUCKDB_PATH, read_only=True)
        r = con.execute("""
            SELECT COALESCE(SUM(amount_usd), 0) FROM trade_log
            WHERE date_trunc('day', executed_at) = date_trunc('day', NOW()) AND engine = ?
        """, [engine]).fetchone()
        con.close(); return float(r[0]) if r else 0.0
    except Exception as e:
        logger.error(f"Daily spend query failed: {e}"); return 50.0

def fetch_top_signals():
    try:
        cutoff = (datetime.utcnow() - timedelta(minutes=30)).isoformat()
        con = duckdb.connect(DUCKDB_PATH, read_only=True)
        rows = con.execute("""
            SELECT event_id, asset, signal_direction, CAST(score AS DOUBLE) AS score, source, created_at
            FROM signal_scores
            WHERE asset IN ('BTC', 'ETH', 'SOL') AND created_at >= ? AND CAST(score AS DOUBLE) >= 0.15
            ORDER BY score DESC LIMIT 20
        """, [cutoff]).fetchall()
        con.close()
        return [{"event_id": r[0], "asset": r[1], "direction": r[2].upper(), "score": r[3], "source": r[4], "created_at": r[5]} for r in rows]
    except Exception as e:
        logger.error(f"fetch_top_signals error: {e}"); return []

def compute_stake(score, source):
    source_weight = SOURCE_PRIORS.get(source, 0.061)
    raw = 3.0 + (score * source_weight * 50.0)
    return round(min(raw, 10.0, 50.0 - get_daily_spend()), 2)

def journal_trade(event_id, asset, direction, stake, pair, ft_response):
    try:
        con = duckdb.connect(DUCKDB_PATH)
        con.execute("CREATE TABLE IF NOT EXISTS trade_log (id VARCHAR DEFAULT gen_random_uuid(), event_id VARCHAR, engine VARCHAR, asset VARCHAR, pair VARCHAR, direction VARCHAR, amount_usd DOUBLE, is_paper BOOLEAN, ft_trade_id VARCHAR, executed_at TIMESTAMP DEFAULT NOW())")
        con.execute("INSERT INTO trade_log (event_id, engine, asset, pair, direction, amount_usd, is_paper, ft_trade_id) VALUES (?, 'freqtrade', ?, ?, ?, ?, TRUE, ?)",
                    [event_id, asset, pair, direction, stake, str(ft_response.get("trade_id", ""))])
        con.close()
    except Exception as e:
        logger.error(f"journal_trade error: {e}")

def force_entry(pair, direction, stake):
    payload = {"pair": pair, "side": "long" if direction in ["BUY", "LONG", "BULLISH"] else "short", "stake_amount": stake, "ordertype": "market"}
    return ft_post("/forceentry", payload)

def run_bridge(paper_mode=True, poll_seconds=60):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [bridge] %(message)s")
    logger.info(f"Striker Bridge starting | paper={paper_mode}")
    if not ft_get("/ping"):
        logger.error("FreqTrade API not reachable"); return
    processed_ids = set()
    while True:
        try:
            remaining = 50.0 - get_daily_spend()
            if remaining < 5.0:
                logger.warning(f"Budget guard RED: remaining=${remaining:.2f}")
                time.sleep(poll_seconds); continue
            signals = fetch_top_signals()
            for sig in [s for s in signals if s["event_id"] not in processed_ids]:
                pair = FT_PAIR_MAP.get(sig["asset"])
                if not pair: continue
                stake = compute_stake(sig["score"], sig["source"])
                if stake < 1.0: continue
                logger.info(f"Signal: {sig['asset']} {sig['direction']} score={sig['score']:.3f} stake=${stake:.2f}")
                resp = force_entry(pair, sig["direction"], stake)
                if resp:
                    journal_trade(sig["event_id"], sig["asset"], sig["direction"], stake, pair, resp)
                    processed_ids.add(sig["event_id"])
                    logger.info(f"Trade injected: {pair} | FT trade_id={resp.get('trade_id')}")
                if len(processed_ids) > 10000:
                    processed_ids = set(list(processed_ids)[-5000:])
        except Exception as e:
            logger.error(f"Bridge loop error: {e}")
        time.sleep(poll_seconds)

if __name__ == "__main__":
    run_bridge(paper_mode=True)
