#!/usr/bin/env python3
"""Dual Execution Supervisor — launches FreqTrade + striker_bridge, monitors budget & health"""
import json, logging, os, signal, subprocess, sys, time
from datetime import datetime
from pathlib import Path
import duckdb

logger = logging.getLogger(__name__)
HOME = Path.home()
DUCKDB_PATH = str(HOME / "kestrel/data/striker.duckdb")
FT_VENV_FT = str(HOME / "freqtrade/.venv/bin/freqtrade")
FT_CONFIG = str(HOME / "freqtrade/user_data/config.json")
BRIDGE_SCRIPT = str(HOME / "kestrel/scripts/trading/striker_bridge.py")
STATE_FILE = str(HOME / "kestrel/.supervisor_state.json")
LOG_DIR = HOME / "kestrel/logs"

proc_ft = proc_bridge = None

def load_state():
    if Path(STATE_FILE).exists():
        with open(STATE_FILE) as f: return json.load(f)
    return {"paper_verified": False, "live_enabled": False, "verified_at": None}

def budget_status():
    try:
        con = duckdb.connect(DUCKDB_PATH, read_only=True)
        spent = con.execute("SELECT COALESCE(SUM(amount_usd), 0) FROM trade_log WHERE date_trunc('day', executed_at) = date_trunc('day', NOW())").fetchone()[0]
        con.close()
        remaining = 50.0 - spent
        status = "red" if remaining < 5.0 else "yellow" if remaining < 25.0 else "green"
        return {"status": status, "spent": spent, "remaining": remaining}
    except Exception as e:
        logger.error(f"Budget error: {e}"); return {"status": "red", "spent": 0, "remaining": 0}

def verify_paper_trades(min_trades=3):
    try:
        con = duckdb.connect(DUCKDB_PATH, read_only=True)
        count = con.execute("SELECT COUNT(*) FROM trade_log WHERE is_paper = TRUE AND executed_at >= NOW() - INTERVAL '24 hours'").fetchone()[0]
        con.close(); return count >= min_trades
    except Exception as e:
        logger.error(f"verify error: {e}"); return False

def start_freqtrade():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    cmd = [FT_VENV_FT, "trade", "--config", FT_CONFIG, "--strategy", "striker_basis",
           "--strategy-path", str(HOME / "freqtrade/user_data/strategies"),
           "--logfile", str(LOG_DIR / "freqtrade.log"),
           "--db-url", f"sqlite:///{HOME}/freqtrade/user_data/tradesv3.sqlite"]
    return subprocess.Popen(cmd, cwd=str(HOME / "freqtrade"), stdout=open(LOG_DIR / "freqtrade_stdout.log", "a"), stderr=subprocess.STDOUT)

def start_bridge():
    return subprocess.Popen([sys.executable, BRIDGE_SCRIPT], stdout=open(LOG_DIR / "bridge.log", "a"), stderr=subprocess.STDOUT)

def shutdown(signum, frame):
    for p in [proc_ft, proc_bridge]:
        if p and p.poll() is None:
            p.terminate()
            try: p.wait(timeout=10)
            except: p.kill()
    sys.exit(0)

def run():
    global proc_ft, proc_bridge
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [supervisor] %(message)s",
                        handlers=[logging.StreamHandler(), logging.FileHandler(LOG_DIR / "supervisor.log")])
    signal.signal(signal.SIGTERM, shutdown); signal.signal(signal.SIGINT, shutdown)
    state = load_state()
    if state.get("live_enabled") and state.get("paper_verified"):
        logger.warning("LIVE MODE ENABLED")
    else:
        with open(FT_CONFIG) as f:
            cfg = json.load(f)
        cfg["dry_run"] = True
        with open(FT_CONFIG, "w") as f:
            json.dump(cfg, f, indent=2)
    bstat = budget_status()
    if bstat["status"] == "red":
        logger.error("Budget RED at startup — aborting"); sys.exit(1)
    proc_ft = start_freqtrade(); time.sleep(5)
    proc_bridge = start_bridge()
    start_time = time.time()
    while True:
        time.sleep(60)
        if proc_ft.poll() is not None:
            time.sleep(10); proc_ft = start_freqtrade()
        if proc_bridge.poll() is not None:
            proc_bridge = start_bridge()
        bstat = budget_status()
        if bstat["status"] == "red":
            for p in [proc_ft, proc_bridge]:
                if p and p.poll() is None: p.terminate()
            time.sleep(3600); continue
        if not state.get("paper_verified") and (time.time() - start_time) >= 3600:
            if verify_paper_trades():
                state["paper_verified"] = True
                state["verified_at"] = datetime.utcnow().isoformat()
                with open(STATE_FILE, "w") as f: json.dump(state, f, indent=2)

if __name__ == "__main__":
    run()
