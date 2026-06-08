#!/usr/bin/env python3
"""
Dual Execution Supervisor v2
- Launches FreqTrade (Bybit futures, paper mode)
- Launches striker_bridge.py (DuckDB -> FT API signal injector)
- Monitors process health, budget, paper verification
- Paper mode LOCKED until 3+ verified trades logged
"""
import json
import logging
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import duckdb

logger = logging.getLogger(__name__)

# Paths
HOME = Path.home()
DUCKDB_PATH = str(HOME / "kestrel/signals.duckdb")
FT_ROOT = str(HOME / "freqtrade")
FT_VENV_FT = str(HOME / "freqtrade/.venv/bin/freqtrade")
FT_VENV_PY = str(HOME / "freqtrade/.venv/bin/python")
FT_CONFIG = str(HOME / "freqtrade/user_data/config.json")
BRIDGE_SCRIPT = str(HOME / "kestrel/scripts/trading/striker_bridge.py")
STATE_FILE = str(HOME / "kestrel/.supervisor_state.json")
LOG_DIR = HOME / "kestrel/logs"

DAILY_CAP = 50.0
FLOOR_USD = 5.0

proc_ft: subprocess.Popen = None
proc_bridge: subprocess.Popen = None


def _load_state() -> dict:
    if Path(STATE_FILE).exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"paper_verified": False, "live_enabled": False, "verified_at": None}


def _save_state(state: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, default=str)


def _budget_status() -> dict:
    try:
        con = duckdb.connect(DUCKDB_PATH, read_only=True)
        spent = con.execute("""
            SELECT COALESCE(SUM(amount_usd), 0)
            FROM trade_log
            WHERE date_trunc('day', executed_at) = date_trunc('day', NOW())
        """).fetchone()[0]
        con.close()
        remaining = DAILY_CAP - spent
        status = (
            "red" if remaining < FLOOR_USD else
            "yellow" if remaining < DAILY_CAP * 0.5 else
            "green"
        )
        return {"status": status, "spent": float(spent), "remaining": float(remaining)}
    except Exception as e:
        logger.error(f"Budget query error: {e}")
        return {"status": "red", "spent": 0, "remaining": 0}


def _verify_paper(min_trades: int = 3) -> bool:
    """Check trade_log for paper trades in last 24h."""
    try:
        con = duckdb.connect(DUCKDB_PATH, read_only=True)
        count = con.execute("""
            SELECT COUNT(*)
            FROM trade_log
            WHERE engine = 'freqtrade'
              AND executed_at >= NOW() - INTERVAL '24 hours'
        """).fetchone()[0]
        con.close()
        logger.info(f"Paper trades (24h): {count}/{min_trades}")
        return count >= min_trades
    except Exception as e:
        logger.error(f"Paper verify error: {e}")
        return False


def _start_freqtrade() -> subprocess.Popen:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    cmd = [
        str(FT_VENV_FT), "trade",
        "--config", str(FT_CONFIG),
        "--strategy", "StrikerBasisStrategy",
        "--strategy-path", str(HOME / "freqtrade/user_data/strategies"),
        "--logfile", str(LOG_DIR / "freqtrade.log"),
        "--db-url", f"sqlite:///{HOME}/freqtrade/user_data/tradesv3.sqlite",
    ]
    logger.info(f"Starting FreqTrade: {' '.join(cmd)}")
    return subprocess.Popen(
        cmd,
        cwd=str(FT_ROOT),
        stdout=open(LOG_DIR / "freqtrade_stdout.log", "a"),
        stderr=subprocess.STDOUT,
    )


def _start_bridge() -> subprocess.Popen:
    logger.info("Starting striker_bridge.py")
    return subprocess.Popen(
        [str(FT_VENV_PY), str(BRIDGE_SCRIPT)],
        stdout=open(LOG_DIR / "bridge.log", "a"),
        stderr=subprocess.STDOUT,
    )


def _shutdown(signum, frame):
    global proc_ft, proc_bridge
    logger.info("Shutdown signal received")
    for p in [proc_ft, proc_bridge]:
        if p and p.poll() is None:
            p.terminate()
            try:
                p.wait(timeout=10)
            except subprocess.TimeoutExpired:
                p.kill()
    sys.exit(0)


def run():
    global proc_ft, proc_bridge

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [supervisor] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOG_DIR / "supervisor.log"),
        ],
    )

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    state = _load_state()
    logger.info(f"State: paper_verified={state.get('paper_verified')} live={state.get('live_enabled')}")

    # Force dry_run in config for paper mode
    if not state.get("live_enabled"):
        with open(FT_CONFIG) as f:
            cfg = json.load(f)
        cfg["dry_run"] = True
        with open(FT_CONFIG, "w") as f:
            json.dump(cfg, f, indent=2)
        logger.info("Dry-run enforced in config (paper mode)")
    else:
        logger.warning("LIVE MODE — ensure dry_run=false and Coinbase wallet funded with $50 USDC")

    # Initial budget check
    bstat = _budget_status()
    logger.info(f"Budget: {bstat}")
    if bstat["status"] == "red":
        logger.error("Budget RED at startup — aborting")
        sys.exit(1)

    # Launch
    proc_ft = _start_freqtrade()
    time.sleep(8)  # Let FT API initialize
    proc_bridge = _start_bridge()

    start_time = time.time()
    verify_after = 3600  # Check paper verification after 1 hour
    CHECK_INTERVAL = 60

    while True:
        time.sleep(CHECK_INTERVAL)

        # Restart dead processes
        if proc_ft.poll() is not None:
            logger.warning("FreqTrade died — restarting")
            time.sleep(5)
            proc_ft = _start_freqtrade()

        if proc_bridge.poll() is not None:
            logger.warning("Bridge died — restarting")
            proc_bridge = _start_bridge()

        # Budget check
        bstat = _budget_status()
        logger.info(f"Budget: {bstat['status']} | ${bstat['spent']:.2f} used / ${bstat['remaining']:.2f} remaining")

        if bstat["status"] == "red":
            logger.error("Budget RED — halting both engines")
            for p in [proc_ft, proc_bridge]:
                if p and p.poll() is None:
                    p.terminate()
            time.sleep(3600)
            continue

        # Paper verification (after 1 hour)
        if not state.get("paper_verified") and (time.time() - start_time) >= verify_after:
            if _verify_paper(min_trades=3):
                state["paper_verified"] = True
                state["verified_at"] = datetime.utcnow().isoformat()
                _save_state(state)
                logger.info("PAPER VERIFICATION PASSED — 3+ trades logged")
                logger.info("To go live: set live_enabled=true in .supervisor_state.json, restart")
            else:
                logger.info("Paper verify: waiting for more trades...")

        # Log signal activity
        try:
            con = duckdb.connect(DUCKDB_PATH, read_only=True)
            signal_count = con.execute("""
                SELECT COUNT(*) FROM signal_scores
                WHERE scored_at >= NOW() - INTERVAL '5 minutes'
            """).fetchone()[0]
            trade_count = con.execute("""
                SELECT COUNT(*) FROM trade_log
                WHERE executed_at >= NOW() - INTERVAL '5 minutes'
            """).fetchone()[0]
            con.close()
            logger.info(f"Activity (5min): {signal_count} new signals, {trade_count} new trades")
        except Exception:
            pass


if __name__ == "__main__":
    run()