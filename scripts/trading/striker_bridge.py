"""
Striker Bridge — Full Execution Layer v2
- Reads DuckDB signal_scores ranked queue
- Checks daily budget guard ($50 cap, $5 floor, $10 per-trade)
- POSTs high-confidence signals to FreqTrade /api/v1/forceentry
- Journals every trade to DuckDB trade_log
- Paper-mode safe (all trades marked is_paper=True)
"""
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import duckdb
import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)

# Config
DUCKDB_PATH = str(Path.home() / "kestrel/signals.duckdb")
FT_API_BASE = "http://127.0.0.1:8080/api/v1"
FT_USER = "ftuser"
FT_PASS = "ftpass"

DAILY_CAP_USD = 50.0
FLOOR_USD = 5.0
PER_TRADE_CAP = 10.0
MIN_SCORE = 0.15
SIGNAL_TTL_MIN = 60
POLL_SECONDS = 60

# Map asset bases to Freqtrade pair format
FT_PAIR_MAP = {
    "BTC": "BTC/USDC",
    "ETH": "ETH/USDC",
    "SOL": "SOL/USDC",
}

# Event types that imply direction
BULLISH_EVENTS = {"whale_transfer", "funding_event", "crypto_narrative"}
BEARISH_EVENTS = {"regulatory_event", "geopolitical_event"}

# Source trust weights from pipeline priors
SOURCE_PRIORS = {
    "whale-alert": 0.384,
    "defillama": 0.340,
    "cointelegraph": 0.66,
    "coindesk": 0.60,
    "disclosetv": 0.121,
    "bankless": 0.108,
    "tldr": 0.106,
}


def _auth() -> HTTPBasicAuth:
    return HTTPBasicAuth(FT_USER, FT_PASS)


def _ft_get(endpoint: str) -> Optional[dict]:
    try:
        r = requests.get(f"{FT_API_BASE}{endpoint}", auth=_auth(), timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error(f"FT GET {endpoint}: {e}")
        return None


def _ft_post(endpoint: str, payload: dict) -> Optional[dict]:
    try:
        r = requests.post(f"{FT_API_BASE}{endpoint}", json=payload, auth=_auth(), timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error(f"FT POST {endpoint}: {e}")
        return None


def _budget_check() -> tuple[bool, float]:
    """
    Returns (ok: bool, remaining: float).
    ok=True if remaining budget >= floor.
    """
    try:
        con = duckdb.connect(DUCKDB_PATH, read_only=True)
        r = con.execute("""
            SELECT COALESCE(SUM(amount_usd), 0)
            FROM trade_log
            WHERE date_trunc('day', executed_at) = date_trunc('day', NOW())
        """).fetchone()
        con.close()
        spent = float(r[0]) if r else 0.0
        remaining = DAILY_CAP_USD - spent
        return remaining >= FLOOR_USD, remaining
    except Exception as e:
        logger.error(f"Budget check failed: {e}")
        return True, DAILY_CAP_USD  # fail open until trade_log exists


def _infer_direction(event_type: str, source_id: str) -> Optional[str]:
    """Infer trade direction from event type and source."""
    et = event_type.lower()
    if et in BULLISH_EVENTS:
        return "long"
    if et in BEARISH_EVENTS:
        return "short"
    # For neutral events, use source trust as heuristic
    if source_id in TRUSTED_SOURCES:
        # Whale alerts are typically sell pressure (short)
        if source_id == "whale-alert" and et == "general_news":
            return "short"
        # DefiLlama TVL inflow is bullish
        if source_id == "defillama":
            return "long"
    return None


TRUSTED_SOURCES = {"whale-alert", "defillama", "cointelegraph", "coindesk"}


def _fetch_signals() -> list[dict]:
    """Fetch top-ranked signals from DuckDB for BTC/ETH/SOL."""
    try:
        cutoff = (datetime.utcnow() - timedelta(minutes=SIGNAL_TTL_MIN)).isoformat()
        con = duckdb.connect(DUCKDB_PATH, read_only=True)
        rows = con.execute("""
            SELECT
                score_id,
                source_id,
                event_type,
                CAST(edge_score AS DOUBLE) AS edge_score,
                asset_symbol,
                event_ts,
                source_prior
            FROM signal_scores
            WHERE (
                asset_symbol IN ('BTC', 'ETH', 'SOL')
                OR source_id IN ('whale-alert', 'defillama')
            )
              AND scored_at >= ?
              AND CAST(edge_score AS DOUBLE) >= ?
            ORDER BY edge_score DESC
            LIMIT 20
        """, [cutoff, MIN_SCORE]).fetchall()
        con.close()
        return [
            {
                "score_id": r[0],
                "source": r[1],
                "event_type": r[2],
                "score": float(r[3]),
                "asset": r[4] or "BTC",  # default BTC if asset_symbol is null
                "event_ts": str(r[5]),
                "prior": float(r[6]),
            }
            for r in rows
        ]
    except Exception as e:
        logger.error(f"fetch_signals error: {e}")
        return []


def _compute_stake(signal: dict) -> float:
    """
    Position size: base $3 + score-weighted addition.
    Trusted sources get up to 2x weight.
    """
    score = signal["score"]
    source = signal["source"]
    source_weight = SOURCE_PRIORS.get(source, 0.061)
    raw = 3.0 + (score * source_weight * 50.0)
    return round(min(raw, PER_TRADE_CAP), 2)


def _journal_trade(signal: dict, pair: str, direction: str,
                    stake: float, ft_response: dict) -> None:
    """Write executed trade to DuckDB trade_log."""
    try:
        con = duckdb.connect(DUCKDB_PATH)
        con.execute("""
            INSERT INTO trade_log
                (pair, side, amount, price, amount_usd,
                 signal_score, source, engine, executed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'freqtrade', NOW())
        """, [
            pair,
            direction,
            stake / ft_response.get("filled_avg", 1.0),
            ft_response.get("filled_avg", 0.0),
            stake,
            signal["score"],
            signal["source"],
        ])
        con.close()
        logger.info(f"Journaled trade: {pair} {direction} ${stake:.2f}")
    except Exception as e:
        logger.error(f"Journal error: {e}")


def _force_entry(pair: str, direction: str, stake: float) -> Optional[dict]:
    """
    POST /api/v1/forceentry to inject trade.
    Requires force_entry_enable: true in config.
    """
    payload = {
        "pair": pair,
        "side": direction,
        "stake_amount": stake,
        "order_type": "market",
    }
    return _ft_post("/forceentry", payload)


def run(paper_mode: bool = True):
    """Main loop: poll DuckDB, check budget, inject trades via FT API."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [bridge] %(message)s",
    )
    logger.info(f"Bridge starting | paper={paper_mode}")

    # Check FT health
    health = _ft_get("/ping")
    if not health:
        logger.error("FreqTrade API unreachable — is it running on port 8080?")
        logger.info("Start FreqTrade first, then restart bridge")
        return

    logger.info(f"FreqTrade API healthy: {health}")

    processed_ids: set = set()

    while True:
        try:
            ok, remaining = _budget_check()
            if not ok:
                logger.warning(f"Budget guard RED: remaining=${remaining:.2f}")
                time.sleep(POLL_SECONDS)
                continue

            signals = _fetch_signals()
            new_signals = [
                s for s in signals
                if s["score_id"] not in processed_ids
            ]

            logger.info(f"Signals: {len(signals)} total, {len(new_signals)} new, budget=${remaining:.2f}")

            for sig in new_signals:
                direction = _infer_direction(sig["event_type"], sig["source"])
                if not direction:
                    logger.debug(f"Skipping {sig['score_id']}: no direction inferred")
                    continue

                asset = sig["asset"]
                pair = FT_PAIR_MAP.get(asset)
                if not pair:
                    logger.debug(f"Skipping {asset}: no pair mapping")
                    continue

                stake = _compute_stake(sig)
                if stake < 1.0:
                    continue

                logger.info(
                    f"Entry: {pair} {direction} score={sig['score']:.3f} "
                    f"source={sig['source']} stake=${stake:.2f}"
                )

                resp = _force_entry(pair, direction, stake)
                if resp:
                    _journal_trade(sig, pair, direction, stake, resp)
                    processed_ids.add(sig["score_id"])
                    logger.info(f"Trade injected: {pair} | {resp}")

                # Bound processed set
                if len(processed_ids) > 10000:
                    processed_ids = set(list(processed_ids)[-5000:])

        except Exception as e:
            logger.error(f"Loop error: {e}")

        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    run(paper_mode=True)