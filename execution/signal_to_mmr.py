"""
signal_to_mmr.py — Bridge between Kestrel signal pipeline and MMR (Meta-Market-Runner).

Reads:  execution/state/active_signals.json (written by build_signal_adapter)
        cycle-state/current.json (budget guard)
Writes: execution/state/mmr_signals.json → MMR's external_signal injection point

Asset filter: equities/ETFs only (opposite of Freqtrade's crypto lane)
MMR injection: writes to a format MMR's signal listener consumes
"""

import json
import logging
import time
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

# ── paths ──────────────────────────────────────────────────────────────────
ACTIVE_SIGNALS = Path("/home/synczus/kestrel/execution/state/active_signals.json")
STATE_FILE = Path("/home/synczus/kestrel/cycle-state/current.json")
MMR_OUTPUT = Path("/home/synczus/kestrel/execution/state/mmr_signals.json")
MMR_TRADE_LOG = Path("/home/synczus/kestrel/execution/state/mmr_trades.json")

# ── budget guard ───────────────────────────────────────────────────────────
BUDGET_CAP = 50.0
BUDGET_BUFFER = 5.0

# ── symbol mappings for MMR (equities/ETFs) ───────────────────────────────
# Drawn from Disclose.tv geopolitical signals + macro sources
# MMR uses yfinance tickers
MACRO_TICKERS = {
    "SPY": "SPY",    # S&P 500
    "QQQ": "QQQ",    # Nasdaq
    "IWM": "IWM",    # Russell 2000
    "GLD": "GLD",    # Gold
    "SLV": "SLV",    # Silver
    "TLT": "TLT",    # Long-term Treasuries
    "SHY": "SHY",    # Short-term Treasuries
    "DXY": "DX-Y.NYB",  # USD Index
}

# Keywords in signal headlines → ticker mapping
TICKER_KEYWORDS = {
    "S&P": "SPY",
    "nasdaq": "QQQ",
    "russell": "IWM",
    "gold": "GLD",
    "silver": "SLV",
    "treasury": "TLT",
    "treasuries": "TLT",
    "yield": "TLT",
    "dollar": "DXY",
    "usd": "DXY",
    "inflation": "GLD",
    "recession": "QQQ",
    "fed": "TLT",
    "federal reserve": "TLT",
    "jobs": "IWM",
    "employment": "IWM",
    "gdp": "SPY",
}


def budget_ok() -> bool:
    """Check if we're within OR budget to trade."""
    try:
        if not STATE_FILE.exists():
            return True
        with open(STATE_FILE) as f:
            state = json.load(f)
        spend = float(state.get("budget", {}).get("daily_spend", 0))
        return spend <= (BUDGET_CAP - BUDGET_BUFFER)
    except Exception:
        return True


def resolve_tickers(signal: dict) -> List[str]:
    """
    Map a signal's headline/symbols to MMR tickers.
    Uses keyword matching on headline text.
    """
    headline = (signal.get("headline", "") or "").lower()
    body = (signal.get("body_text", "") or "").lower()
    text = f"{headline} {body}"
    symbols = signal.get("symbols", [])

    # Already has explicit symbols
    if isinstance(symbols, str):
        symbols = [symbols]
    tickers = []
    for sym in symbols:
        sym_upper = sym.strip().upper()
        if sym_upper in MACRO_TICKERS:
            tickers.append(MACRO_TICKERS[sym_upper])

    # No direct ticker match — try keyword inference
    if not tickers:
        for keyword, ticker in TICKER_KEYWORDS.items():
            if keyword in text:
                tickers.append(ticker)

    return list(set(tickers))


def build_mmr_signal(signal: dict) -> Optional[dict]:
    """
    Convert a Kestrel signal into MMR-compatible trade signal format.
    MMR's expected format (from code inspection):
    {
        "symbol": "SPY",
        "direction": "long|short",
        "strength": 0.0-1.0,
        "source": "kestrel_pipeline",
        "reason": "headline",
        "timestamp": iso_timestamp
    }
    """
    tickers = resolve_tickers(signal)
    if not tickers:
        return None

    edge = float(signal.get("edge_score", 0))

    # Direction heuristic: positive edge_score = long, negative = short
    # Most pipeline signals are news-based — direction is "watch" or "long" by default
    direction = "long"
    if edge < 0:
        direction = "short"

    # Strength: clamp edge_score to 0-1 range
    strength = max(0.0, min(1.0, abs(edge)))

    return {
        "symbol": tickers[0],  # MMR processes one signal at a time
        "direction": direction,
        "strength": strength,
        "source": "kestrel_pipeline",
        "reason": signal.get("headline", ""),
        "edge_score": edge,
        "source_id": signal.get("source_id", ""),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def run(budget_check: bool = True) -> int:
    """
    Main: read active signals → convert to MMR format → write output.
    Returns number of MMR signals written.
    """
    if budget_check and not budget_ok():
        logger.info("budget guard active — skipping MMR signal injection")
        return 0

    if not ACTIVE_SIGNALS.exists():
        logger.info("no active signals found")
        return 0

    with open(ACTIVE_SIGNALS) as f:
        signals = json.load(f)

    mmr_signals = []
    for sig in signals:
        mmr_sig = build_mmr_signal(sig)
        if mmr_sig:
            mmr_signals.append(mmr_sig)

    if not mmr_signals:
        logger.info("no MMR-compatible signals found in queue")
        return 0

    MMR_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(MMR_OUTPUT, "w") as f:
        json.dump({"signals": mmr_signals, "updated_at": time.time()}, f, indent=2)

    # Log to trade audit
    if MMR_TRADE_LOG.exists():
        with open(MMR_TRADE_LOG) as f:
            trade_log = json.load(f)
    else:
        trade_log = []
    trade_log.append({
        "timestamp": time.time(),
        "count": len(mmr_signals),
        "symbols": [s["symbol"] for s in mmr_signals],
    })
    with open(MMR_TRADE_LOG, "w") as f:
        json.dump(trade_log[-200:], f, indent=2)

    logger.info("wrote %d MMR signals to %s", len(mmr_signals), MMR_OUTPUT)
    return len(mmr_signals)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    n = run()
    print(json.dumps({"mmr_signals_written": n}, indent=2))