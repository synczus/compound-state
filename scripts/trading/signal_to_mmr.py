#!/usr/bin/env python3
"""
signal_to_mmr.py — DuckDB → MMR signal adapter.

Reads top-20 equity/ETF signals from DuckDB signal_scores ranked queue,
injects into MMR's ma_crossover.py via external_signal_override().

Usage:
    python signal_to_mmr.py              # poll mode (default 60s)
    python signal_to_mmr.py --paper      # paper mode (default)
    python signal_to_mmr.py --once       # single-shot inject
    python signal_to_mmr.py --poll 30    # 30s poll interval

MMR injection point:
    /home/synczus/mmr/strategies/ma_crossover.py -> external_signal_override()
"""
import argparse
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import duckdb

# Add MMR to path for direct module injection
MMR_ROOT = Path.home() / "mmr"
sys.path.insert(0, str(MMR_ROOT))

logger = logging.getLogger(__name__)

# Paths
DUCKDB_PATH = str(Path.home() / "kestrel/signals.duckdb")
MMR_STRATEGY_DIR = MMR_ROOT / "strategies"
EXTERNAL_SIGNALS_FILE = MMR_STRATEGY_DIR / "external_signals.json"

# Budget
DAILY_CAP_USD = 50.0
FLOOR_USD = 5.0

# Score thresholds — edge_score range is 0.0-0.384
EQUITY_SCORE_THRESHOLD = 0.05  # minimum edge_score to inject
SIGNAL_TTL_MINUTES = 120        # signals older than this are stale
POLL_INTERVAL_SECONDS = 60     # default poll interval

# Equity assets we track (symbols that MMR trades)
EQUITY_ASSETS = {"SPY", "QQQ", "AAPL", "NVDA", "MSFT", "GOOGL", "AMZN", "TSLA",
                 "IWM", "TLT", "GLD", "SLV", "USO", "XLF", "XLE", "XLV"}


def get_equity_signals() -> list[dict]:
    """Fetch top-20 equity signals from DuckDB ranked queue."""
    try:
        cutoff = (datetime.now() - timedelta(minutes=SIGNAL_TTL_MINUTES)).isoformat()
        con = duckdb.connect(DUCKDB_PATH, read_only=True)
        rows = con.execute("""
            SELECT
                signal_id,
                asset_symbol,
                event_type,
                edge_score,
                source_id,
                scored_at
            FROM signal_scores
            WHERE asset_symbol IN ({})
            AND scored_at >= ?
            AND edge_score >= ?
            ORDER BY edge_score DESC
            LIMIT 20
        """.format(",".join(f"'{a}'" for a in EQUITY_ASSETS)),
            [cutoff, EQUITY_SCORE_THRESHOLD]).fetchall()
        con.close()
        return [
            {
                "event_id": r[0],
                "asset": r[1],
                "direction": _infer_direction(r[2]),
                "score": float(r[3]),
                "source": r[4],
                "created_at": r[5],
            }
            for r in rows
        ]
    except Exception as e:
        logger.error(f"DuckDB equity signal read error: {e}")
        return []


def get_crypto_signals() -> list[dict]:
    """Fetch top-20 crypto signals (BTC/ETH/SOL) from DuckDB."""
    try:
        cutoff = (datetime.now() - timedelta(minutes=SIGNAL_TTL_MINUTES)).isoformat()
        con = duckdb.connect(DUCKDB_PATH, read_only=True)
        rows = con.execute("""
            SELECT
                signal_id,
                asset_symbol,
                event_type,
                edge_score,
                source_id,
                scored_at
            FROM signal_scores
            WHERE asset_symbol IN ('BTC', 'ETH', 'SOL')
            AND scored_at >= ?
            AND edge_score >= ?
            ORDER BY edge_score DESC
            LIMIT 20
        """, [cutoff, EQUITY_SCORE_THRESHOLD]).fetchall()
        con.close()
        return [
            {
                "event_id": r[0],
                "asset": r[1],
                "direction": _infer_direction(r[2]),
                "score": float(r[3]),
                "source": r[4],
                "created_at": r[5],
            }
            for r in rows
        ]
    except Exception as e:
        logger.error(f"DuckDB crypto signal read error: {e}")
        return []


def _infer_direction(event_type: str) -> str:
    """Infer signal direction from event_type."""
    et = event_type.lower()
    if any(w in et for w in ["buy", "long", "bull", "whale_deposit", "inflow"]):
        return "BUY"
    if any(w in et for w in ["sell", "short", "bear", "whale_withdraw", "outflow"]):
        return "SELL"
    # Default: no directional bias
    return "NEUTRAL"


def budget_ok() -> bool:
    """Check daily spend against budget guard."""
    try:
        con = duckdb.connect(DUCKDB_PATH, read_only=True)
        result = con.execute("""
            SELECT COALESCE(SUM(amount_usd), 0)
            FROM trade_log
            WHERE date_trunc('day', executed_at) = date_trunc('day', NOW())
            AND engine = 'mmr'
        """).fetchone()
        con.close()
        spent = result[0] if result else 0
        remaining = DAILY_CAP_USD - spent
        return remaining >= FLOOR_USD
    except Exception as e:
        logger.error(f"Budget check error: {e}")
        return True  # default allow on error


def inject_signal(signal: dict, paper_mode: bool = True) -> bool:
    """
    Inject a signal into MMR via external_signal_override().

    Falls back to writing external_signals.json if direct import fails.
    """
    symbol = signal["asset"]
    direction = signal["direction"]
    score = signal["score"]

    # Try direct module injection into MMR's ma_crossover
    try:
        sys.path.insert(0, str(MMR_ROOT))
        from strategies.ma_crossover import external_signal_override
        result = external_signal_override(
            symbol=symbol,
            direction=direction,
            score=score,
            paper=paper_mode,
        )
        logger.info(f"MMR direct inject: {symbol} {direction} score={score:.3f} -> {result}")
        return True
    except ImportError as e:
        logger.warning(f"MMR direct import failed: {e} — falling back to JSON file")
    except Exception as e:
        logger.error(f"MMR direct inject error: {e}")

    # Fallback: write to external_signals.json
    try:
        MMR_STRATEGY_DIR.mkdir(parents=True, exist_ok=True)
        import json
        existing = {}
        if EXTERNAL_SIGNALS_FILE.exists():
            existing = json.loads(EXTERNAL_SIGNALS_FILE.read_text())
        existing[symbol] = {
            "direction": direction,
            "score": score,
            "paper": paper_mode,
            "injected_at": datetime.now().isoformat(),
        }
        EXTERNAL_SIGNALS_FILE.write_text(json.dumps(existing, indent=2))
        logger.info(f"MMR JSON inject: {symbol} {direction} score={score:.3f}")
        return True
    except Exception as e:
        logger.error(f"MMR JSON inject error: {e}")
        return False


def run_adapter(paper_mode: bool = True, poll_seconds: int = POLL_INTERVAL_SECONDS,
                once: bool = False):
    """Main loop: poll DuckDB, inject signals into MMR."""
    logger.info(f"MMR adapter started | paper={paper_mode} | poll={poll_seconds}s")
    processed_ids = set()

    while True:
        try:
            if not budget_ok():
                logger.warning("Budget guard RED — skipping cycle")
                if once:
                    break
                time.sleep(poll_seconds)
                continue

            signals = get_equity_signals() + get_crypto_signals()
            new_signals = [s for s in signals if s["event_id"] not in processed_ids]

            for sig in new_signals:
                ok = inject_signal(sig, paper_mode=paper_mode)
                if ok:
                    processed_ids.add(sig["event_id"])

            # Bound memory
            if len(processed_ids) > 10000:
                processed_ids = set(list(processed_ids)[-5000:])

            if once:
                logger.info(f"Single-shot: {len(processed_ids)} signals injected")
                return

        except Exception as e:
            logger.error(f"Adapter loop error: {e}")
            if once:
                return

        time.sleep(poll_seconds)


def main():
    parser = argparse.ArgumentParser(description="MMR signal adapter")
    parser.add_argument("--paper", action="store_true", default=True,
                       help="Paper mode (default: True)")
    parser.add_argument("--live", action="store_true",
                       help="Live mode override")
    parser.add_argument("--once", action="store_true",
                       help="Single-shot instead of poll loop")
    parser.add_argument("--poll", type=int, default=POLL_INTERVAL_SECONDS,
                       help=f"Poll interval seconds (default: {POLL_INTERVAL_SECONDS})")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [mmr_adapter] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(str(Path.home() / "kestrel/logs/mmr_adapter.log")),
        ],
    )

    paper_mode = not args.live if args.live else args.paper
    run_adapter(paper_mode=paper_mode, poll_seconds=args.poll, once=args.once)


if __name__ == "__main__":
    main()
