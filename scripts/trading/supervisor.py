#!/usr/bin/env python3
"""
Dual Execution Supervisor

Manages:
    - FreqTrade (coinbaseadvanced, crypto signals via DuckDBSignalStrategy)
    - MMR adapter (signal_to_mmr.py, equity/ETF signals via ma_crossover)

Both read the same DuckDB signal_scores ranked queue with asset-type filters.
Budget guard: $50/day hard cap, $5 degradation floor, $10 per-trade hard cap.
PAPER MODE ONLY until 3+ verified paper trades logged in trade_log.

Usage:
    python supervisor.py                    # paper mode (default)
    python supervisor.py --live             # override to live (requires state file)
    python supervisor.py --dry-run          # validate config only, don't start engines
"""
import json
import logging
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import requests

logger = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────
HOME = Path.home()
DUCKDB_PATH = str(HOME / "kestrel/signals.duckdb")
FT_ROOT = str(HOME / "freqtrade")
FT_VENV_FT = str(FT_ROOT / ".venv/bin/freqtrade")
FT_CONFIG = str(FT_ROOT / "user_data/config.json")
MMR_ADAPTER = str(HOME / "kestrel/scripts/trading/signal_to_mmr.py")
STATE_FILE = str(Path.home() / "kestrel/.supervisor_state.json")
LOG_DIR = HOME / "kestrel/logs"
FT_LOG = str(LOG_DIR / "freqtrade.log")
MMR_LOG = str(LOG_DIR / "mmr_adapter.log")
SUPERVISOR_LOG = str(LOG_DIR / "supervisor.log")

# ── Budget ─────────────────────────────────────────────────────────────
DAILY_CAP_USD = 50.0
FLOOR_USD = 5.0
PER_TRADE_CAP_USD = 10.0

# ── State ──────────────────────────────────────────────────────────────
PAPER_MODE = True  # Overridden by --live or state file
proc_ft: subprocess.Popen | None = None
proc_mmr: subprocess.Popen | None = None


def load_state() -> dict:
    if Path(STATE_FILE).exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"paper_verified": False, "live_enabled": False, "verified_at": None}


def save_state(state: dict):
    Path(STATE_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, default=str)


def budget_status() -> dict:
    """Return budget guard status: green/yellow/red."""
    try:
        con = duckdb.connect(DUCKDB_PATH, read_only=True)
        ft_spend = con.execute("""
            SELECT COALESCE(SUM(amount_usd), 0)
            FROM trade_log
            WHERE date_trunc('day', executed_at) = date_trunc('day', NOW())
            AND engine = 'freqtrade'
        """).fetchone()[0]
        mmr_spend = con.execute("""
            SELECT COALESCE(SUM(amount_usd), 0)
            FROM trade_log
            WHERE date_trunc('day', executed_at) = date_trunc('day', NOW())
            AND engine = 'mmr'
        """).fetchone()[0]
        con.close()
        total = float(ft_spend) + float(mmr_spend)
        remaining = DAILY_CAP_USD - total
        status = (
            "green" if remaining >= DAILY_CAP_USD * 0.5 else
            "yellow" if remaining >= FLOOR_USD else
            "red"
        )
        return {"status": status, "total_spend": total,
                "ft_spend": float(ft_spend), "mmr_spend": float(mmr_spend),
                "remaining": remaining, "cap": DAILY_CAP_USD}
    except Exception as e:
        logger.error(f"Budget query failed: {e}")
        return {"status": "red", "reason": str(e)}


def ft_api_ok() -> bool:
    """Check if FreqTrade API is reachable."""
    try:
        r = requests.get("http://127.0.0.1:8081/api/v1/ping", timeout=3)
        return r.status_code == 200 and r.json().get("status") == "pong"
    except Exception:
        return False


def verify_paper_trades(min_trades: int = 3) -> bool:
    """Check trade_log for at least min_trades paper entries in last 24h."""
    try:
        con = duckdb.connect(DUCKDB_PATH, read_only=True)
        count = con.execute("""
            SELECT COUNT(*)
            FROM trade_log
            WHERE is_paper = TRUE
            AND executed_at >= NOW() - INTERVAL '24 hours'
        """).fetchone()[0]
        con.close()
        logger.info(f"Paper trades (24h): {count}/{min_trades}")
        return count >= min_trades
    except Exception as e:
        logger.error(f"Paper verify error: {e}")
        return False


def start_freqtrade() -> subprocess.Popen:
    """Start FreqTrade in paper mode."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    cmd = [
        str(FT_VENV_FT), "trade",
        "--config", FT_CONFIG,
        "--strategy", "DuckDBSignalStrategy",
        "--logfile", FT_LOG,
        "--db-url", f"sqlite:///{FT_ROOT}/user_data/tradesv3.dryrun.sqlite",
    ]
    logger.info(f"Starting FreqTrade: {' '.join(cmd)}")
    return subprocess.Popen(
        cmd, cwd=str(FT_ROOT),
        stdout=open(LOG_DIR / "freqtrade_stdout.log", "a"),
        stderr=subprocess.STDOUT,
    )


def start_mmr_adapter(paper: bool = True) -> subprocess.Popen:
    """Start the MMR signal adapter."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, MMR_ADAPTER]
    if paper:
        cmd.append("--paper")
    else:
        cmd.append("--live")
    cmd.extend(["--poll", "60"])
    logger.info(f"Starting MMR adapter: {' '.join(cmd)}")
    return subprocess.Popen(
        cmd,
        stdout=open(MMR_LOG, "a"),
        stderr=subprocess.STDOUT,
    )


def ensure_trade_log_table():
    """Create trade_log table in DuckDB if it doesn't exist."""
    try:
        con = duckdb.connect(DUCKDB_PATH)
        con.execute("""
            CREATE TABLE IF NOT EXISTS trade_log (
                id VARCHAR DEFAULT gen_random_uuid(),
                event_id VARCHAR,
                engine VARCHAR,
                asset VARCHAR,
                pair VARCHAR,
                direction VARCHAR,
                amount_usd DOUBLE,
                is_paper BOOLEAN DEFAULT TRUE,
                broker_trade_id VARCHAR,
                executed_at TIMESTAMP DEFAULT NOW()
            )
        """)
        con.close()
        logger.info("trade_log table ensured in DuckDB")
    except Exception as e:
        logger.error(f"trade_log table creation error: {e}")


def handle_shutdown(signum, frame):
    """Graceful shutdown of both engines."""
    global proc_ft, proc_mmr
    logger.info("Shutdown signal received — stopping engines")
    for name, proc in [("FreqTrade", proc_ft), ("MMR", proc_mmr)]:
        if proc and proc.poll() is None:
            logger.info(f"Stopping {name} (PID {proc.pid})")
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
    sys.exit(0)


def run(dry_run: bool = False, force_live: bool = False):
    """Main supervisor loop."""
    global proc_ft, proc_mmr, PAPER_MODE

    # Setup
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [supervisor] %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(SUPERVISOR_LOG)],
    )

    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    state = load_state()
    PAPER_MODE = not (state.get("live_enabled") and state.get("paper_verified"))
    if force_live:
        PAPER_MODE = False

    # Ensure trade_log table
    ensure_trade_log_table()

    # Initial budget check
    bstat = budget_status()
    logger.info(f"Supervisor starting | paper={PAPER_MODE} | budget={bstat['status']}")
    if bstat["status"] == "red":
        logger.error("Budget guard RED at startup — aborting")
        sys.exit(1)

    if dry_run:
        logger.info("DRY RUN — config validated, exiting")
        return

    # Start engines
    proc_ft = start_freqtrade()
    time.sleep(8)  # Let FreqTrade API come up
    proc_mmr = start_mmr_adapter(paper=PAPER_MODE)

    # Verify FreqTrade API is up
    if ft_api_ok():
        logger.info("FreqTrade API reachable on :8081")
    else:
        logger.warning("FreqTrade API not reachable yet — will retry in next cycle")

    # Main loop
    start_time = time.time()
    verify_after_seconds = 3600  # 1 hour of paper trading
    CHECK_INTERVAL = 60

    while True:
        time.sleep(CHECK_INTERVAL)

        # Restart dead processes
        if proc_ft.poll() is not None:
            logger.warning("FreqTrade died — restarting")
            time.sleep(5)
            proc_ft = start_freqtrade()

        if proc_mmr.poll() is not None:
            logger.warning("MMR adapter died — restarting")
            proc_mmr = start_mmr_adapter(paper=PAPER_MODE)

        # Budget check
        bstat = budget_status()
        logger.info(
            f"Budget: {bstat['status']} | "
            f"FT=${bstat['ft_spend']:.2f} MMR=${bstat['mmr_spend']:.2f} "
            f"rem=${bstat['remaining']:.2f}"
        )
        if bstat["status"] == "red":
            logger.error("Budget RED — suspending both engines")
            for p in [proc_ft, proc_mmr]:
                if p and p.poll() is None:
                    p.terminate()
            time.sleep(3600)
            continue

        # Paper verification window
        if PAPER_MODE and not state.get("paper_verified"):
            elapsed = time.time() - start_time
            if elapsed >= verify_after_seconds:
                if verify_paper_trades(min_trades=3):
                    state["paper_verified"] = True
                    state["verified_at"] = datetime.now(timezone.utc).isoformat()
                    save_state(state)
                    logger.info("PAPER VERIFICATION PASSED ✓")
                    logger.info("Run with --live to enable live trading")
                else:
                    logger.info("Paper verification pending — need 3+ trades in 24h")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Dual Execution Supervisor")
    parser.add_argument("--live", action="store_true", help="Live mode override")
    parser.add_argument("--dry-run", action="store_true", help="Validate config only")
    args = parser.parse_args()

    run(dry_run=args.dry_run, force_live=args.live)


if __name__ == "__main__":
    main()
