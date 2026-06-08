"""
dual_supervisor.py — Orchestrates both execution lanes (Freqtrade + MMR)
with shared budget guard, asset-type routing, and audit logging.

Pipeline:
  1. Build signal adapter (query DuckDB → active_signals.json)
  2. Run Freqtrade lane (crypto: BTC/ETH/SOL via signal_to_freqtrade)
  3. Run MMR lane (equities/ETFs via signal_to_mmr)
  4. Check budget before each lane
  5. Log all decisions to execution/state/dual_audit.json

Run from cron every 5 minutes. Idempotent — each lane skips when budget is tight.
"""

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, Optional

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from execution.freqtrade.strategies.duckdb_signal_strategy import build_signal_adapter
from execution.signal_to_mmr import run as run_mmr

logger = logging.getLogger(__name__)

# ── paths ──────────────────────────────────────────────────────────────────
STATE_FILE = Path("/home/synczus/kestrel/cycle-state/current.json")
AUDIT_LOG = Path("/home/synczus/kestrel/execution/state/dual_audit.json")
BUDGET_FILE = Path("/home/synczus/kestrel/config/credit-cap.json")

BUDGET_CAP = 50.0
BUDGET_BUFFER = 5.0
DEGRADE_FLOOR = 5.0   # below this, only lead_indicator sources survive


# ═══════════════════════════════════════════════════════════════════════════
# State helpers
# ═══════════════════════════════════════════════════════════════════════════

def load_state() -> dict:
    try:
        if STATE_FILE.exists():
            with open(STATE_FILE) as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def check_budget(state: dict) -> Dict[str, object]:
    """Return budget status with degradation level."""
    spend = float(state.get("budget", {}).get("daily_spend", 0))
    remaining = BUDGET_CAP - spend

    if remaining <= 0:
        return {"ok": False, "remaining": remaining, "level": "exhausted"}
    elif remaining <= DEGRADE_FLOOR:
        return {"ok": True, "remaining": remaining, "level": "degraded"}
    elif remaining <= BUDGET_BUFFER:
        return {"ok": True, "remaining": remaining, "level": "tight"}
    else:
        return {"ok": True, "remaining": remaining, "level": "normal"}


def can_trade_lane(budget_status: Dict[str, object], lane: str) -> bool:
    """Check if a specific lane can trade based on budget level."""
    if budget_status["level"] == "exhausted":
        return False
    if budget_status["level"] == "degraded":
        # In degraded mode, only crypto lane runs (lower cost per trade)
        return lane == "crypto"
    return True


def log_audit(
    budget_status: Dict[str, object],
    crypto_signals: int,
    mmr_signals: int,
    errors: list,
) -> None:
    """Append execution cycle to audit log."""
    entry = {
        "timestamp": time.time(),
        "iso_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "budget_level": budget_status["level"],
        "budget_remaining": budget_status["remaining"],
        "crypto_signals": crypto_signals,
        "mmr_signals": mmr_signals,
        "errors": errors,
    }
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    try:
        if AUDIT_LOG.exists():
            with open(AUDIT_LOG) as f:
                log = json.load(f)
        else:
            log = []
        log.append(entry)
        with open(AUDIT_LOG, "w") as f:
            json.dump(log[-200:], f, indent=2)
    except Exception as e:
        logger.error("audit log write failed: %s", e)


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════

def run_cycle() -> Dict[str, object]:
    """
    Execute one full execution cycle.
    Returns summary dict.
    """
    state = load_state()
    budget_status = check_budget(state)
    errors = []

    # Stage 1: Build signal adapter (common for both lanes)
    try:
        active_signals = build_signal_adapter(
            db_path="/home/synczus/kestrel/signals.duckdb",
            output_path="/home/synczus/kestrel/execution/state/active_signals.json",
            max_signals=5,
        )
        crypto_signal_count = len(active_signals)
    except Exception as e:
        logger.error("signal adapter failed: %s", e)
        errors.append(f"signal_adapter: {e}")
        crypto_signal_count = 0

    # Stage 2: Freqtrade crypto lane
    if can_trade_lane(budget_status, "crypto") and crypto_signal_count > 0:
        logger.info("crypto lane: %d signals available", crypto_signal_count)
        # Freqtrade reads active_signals.json internally via DuckDBSignalStrategy
        # No direct call needed — the strategy picks them up on next candle
    else:
        reason = "budget" if not can_trade_lane(budget_status, "crypto") else "no_signals"
        logger.info("crypto lane skipped (%s)", reason)

    # Stage 3: MMR equities lane
    mmr_count = 0
    if can_trade_lane(budget_status, "mmr"):
        try:
            mmr_count = run_mmr(budget_check=True)
        except Exception as e:
            logger.error("MMR lane failed: %s", e)
            errors.append(f"mmr: {e}")

    # Stage 4: Audit
    log_audit(budget_status, crypto_signal_count, mmr_count, errors)

    summary = {
        "cycle_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "crypto_signals": crypto_signal_count,
        "mmr_signals_written": mmr_count,
        "budget_level": budget_status["level"],
        "budget_remaining": budget_status["remaining"],
        "errors": errors,
    }
    logger.info("cycle complete: %s", json.dumps(summary))
    return summary


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    result = run_cycle()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()