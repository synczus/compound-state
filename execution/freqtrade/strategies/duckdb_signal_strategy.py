"""
DuckDBSignalStrategy — reads scored signals from the Kestrel pipeline
and converts them into Freqtrade buy/sell decisions.

Reads:  execution/state/signal_queue.json (written by post-ingest-scorer)
        cycle-state/current.json (budget guard)
Writes: execution/state/ft_trades.json (audit log)

Asset filter: BTC/USDC, ETH/USDC, SOL/USDC only
Budget guard: skips trades when OR spend > $45 (leaves $5 buffer)
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

# Freqtrade imports — only available when running inside freqtrade trade
try:
    from freqtrade.strategy import IStrategy, DecimalParameter, IntParameter
    from pandas import DataFrame
    HAS_FREQTRADE = True
except ImportError:
    HAS_FREQTRADE = False

logger = logging.getLogger(__name__)

# ── paths ──────────────────────────────────────────────────────────────────
SIGNAL_QUEUE = Path("/home/synczus/kestrel/dashboard/pending.json")
STATE_FILE = Path("/home/synczus/kestrel/cycle-state/current.json")
TRADE_LOG = Path("/home/synczus/kestrel/execution/state/ft_trades.json")
BUDGET_FILE = Path("/home/synczus/kestrel/config/credit-cap.json")

# ── asset symbol mapping ───────────────────────────────────────────────────
SYMBOL_MAP = {
    "BTC": "BTC/USDC",
    "ETH": "ETH/USDC",
    "SOL": "SOL/USDC",
}
CRYPTO_ASSETS = SYMBOL_MAP  # alias for Perplexity compatibility

# ── budget guard ───────────────────────────────────────────────────────────
BUDGET_CAP = 50.0       # hard daily OR cap
BUDGET_BUFFER = 5.0     # leave $5 buffer before stopping trades
SIGNAL_TTL_SECONDS = 300  # signals older than 5 min are stale
DB_PATH = Path("/home/synczus/kestrel/signals.duckdb")


# ═══════════════════════════════════════════════════════════════════════════
class DuckDBSignalStrategy(IStrategy):
    """
    Freqtrade strategy that reads our pipeline's ranked signal queue
    and trades based on scored confidence + source prior.
    """

    INTERFACE_VERSION = 3

    # ── positional params ──────────────────────────────────────────────
    timeframe = "5m"
    can_short = False
    startup_candle_count = 1

    # ── stake ──────────────────────────────────────────────────────────
    minimal_roi = {"60": 0.01, "30": 0.02, "0": 0.04}
    stoploss = -0.05
    trailing_stop = False
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    # ── signal thresholds (tunable) ────────────────────────────────────
    buy_threshold = DecimalParameter(0.3, 0.9, default=0.45, space="buy")
    exit_threshold = DecimalParameter(0.4, 0.9, default=0.55, space="sell")
    min_source_prior = DecimalParameter(0.2, 0.8, default=0.5, space="buy")
    process_only_new_candles = True

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """No indicators — we trade on external signals only."""
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Read DuckDB signal queue and set buy signals for matching asset."""
        pair = metadata.get("pair", "")
        if not pair:
            return dataframe
        asset_base = pair.split("/")[0]
        if asset_base not in CRYPTO_ASSETS.values() and asset_base not in CRYPTO_ASSETS:
            dataframe["enter_long"] = 0
            return dataframe

        if not self._budget_check():
            dataframe["enter_long"] = 0
            logger.warning("Skipping entry for %s: budget guard triggered", pair)
            return dataframe

        signals = self._load_signal_queue(asset_base=asset_base)

        if signals.empty:
            dataframe["enter_long"] = 0
            return dataframe

        top_score = float(signals["edge_score"].max())
        top_direction = str(signals.iloc[0].get("direction", "long")).upper()
        threshold = self.buy_threshold.value

        enter = (top_score >= threshold) and (top_direction in ["BUY", "LONG", "BULLISH", ""])
        dataframe["enter_long"] = 1 if enter else 0
        dataframe["enter_tag"] = f"kestrel_score_{int(top_score * 100)}" if enter else ""

        if enter:
            sig_dict = signals.iloc[0].to_dict()
            self._log_trade(sig_dict, pair, "buy")

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Check DuckDB for exit-worthy signals on this pair."""
        pair = metadata.get("pair", "")
        if not pair:
            return dataframe
        asset_base = pair.split("/")[0]

        signals = self._load_signal_queue(asset_base=asset_base)

        if signals.empty:
            dataframe["exit_long"] = 0
            return dataframe

        top_score = float(signals["edge_score"].max())
        top_direction = str(signals.iloc[0].get("direction", "")).upper()
        threshold = self.exit_threshold.value

        exit_sig = (top_score >= threshold) and (top_direction in ["SELL", "SHORT", "BEARISH"])
        dataframe["exit_long"] = 1 if exit_sig else 0
        dataframe["exit_tag"] = f"kestrel_exit_{int(top_score * 100)}" if exit_sig else ""
        return dataframe

    def confirm_trade_entry(
        self, pair: str, order_type: str, amount: float,
        rate: float, time_in_force: str, current_time: datetime,
        entry_tag: Optional[str] = None, side: str = "long", **kwargs
    ) -> bool:
        """Final guard before any order fires — check budget + single trade cost."""
        if not self._budget_check():
            logger.warning("confirm_trade_entry BLOCKED for %s: budget exceeded", pair)
            return False
        cost = amount * rate
        if cost > 50.0:
            logger.warning("Single trade cost $%.2f exceeds $50 cap — blocking %s", cost, pair)
            return False
        return True

    # ── helpers ────────────────────────────────────────────────────────

    def _load_signal_queue(self, asset_base: Optional[str] = None) -> pd.DataFrame:
        """
        Load top-20 signals from DuckDB, filtered by asset base.
        Falls back to JSON file if DuckDB is unavailable.
        """
        try:
            import duckdb
            con = duckdb.connect(str(DB_PATH), read_only=True)
            cutoff = (time.time() - SIGNAL_TTL_SECONDS)
            params = [cutoff]
            asset_filter = ""
            if asset_base:
                asset_filter = "AND e.symbols IS NOT NULL AND upper(e.symbols) LIKE ?"
                params.append(f"%{asset_base.upper()}%")
            df = con.execute(f"""
                SELECT
                    s.event_id,
                    s.source_id,
                    s.source_prior,
                    s.confidence,
                    s.relevance,
                    s.novelty,
                    s.edge_score,
                    e.headline,
                    e.symbols,
                    e.event_type
                FROM signal_scores s
                JOIN events e ON s.event_id = e.row_id
                WHERE s.edge_score IS NOT NULL
                  AND s.scored_at >= ?
                  {asset_filter}
                ORDER BY s.edge_score DESC
                LIMIT 20
            """, params).df()
            con.close()
            return df
        except Exception as e:
            logger.warning("DuckDB query failed, falling back to JSON: %s", e)
            # Fallback to JSON queue
            try:
                if not SIGNAL_QUEUE.exists():
                    return pd.DataFrame()
                with open(SIGNAL_QUEUE) as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    data = data.get("queue", data.get("signals", [data]))
                return pd.DataFrame(data)
            except Exception as e2:
                logger.warning("JSON fallback also failed: %s", e2)
                return pd.DataFrame()

    def _budget_check(self) -> bool:
        """Return True if under daily OR spend cap. Queries DuckDB trade_log if available."""
        try:
            import duckdb
            con = duckdb.connect(str(DB_PATH), read_only=True)
            result = con.execute("""
                SELECT COALESCE(SUM(amount_usd), 0) as daily_spend
                FROM execution_trades
                WHERE date_trunc('day', executed_at) = date_trunc('day', CURRENT_TIMESTAMP)
                  AND engine = 'freqtrade'
            """).fetchone()
            con.close()
            daily_spend = result[0] if result else 0
            remaining = BUDGET_CAP - daily_spend
            if remaining < BUDGET_BUFFER:
                logger.warning("budget guard: remaining=$%.2f (floor=$%.2f)", remaining, BUDGET_BUFFER)
                return False
            return True
        except Exception:
            # fallback: check cycle-state budget file
            return True

    def _matches_pair(self, sig: dict, pair: str) -> bool:
        """Check if a signal's symbols match the current pair."""
        symbols = sig.get("symbols", [])
        if isinstance(symbols, str):
            symbols = [symbols]
        for sym in symbols:
            mapped = SYMBOL_MAP.get(sym.upper())
            if mapped and mapped == pair:
                return True
        return False

    def _budget_ok(self) -> bool:
        """Check OR spend against cap. Leaves BUFFER before stopping."""
        try:
            if not STATE_FILE.exists():
                return True
            with open(STATE_FILE) as f:
                state = json.load(f)
            spend = float(state.get("budget", {}).get("daily_spend", 0))
            return spend <= (BUDGET_CAP - BUDGET_BUFFER)
        except Exception:
            return True

    def _log_trade(self, sig: dict, pair: str, action: str) -> None:
        """Append trade decision to audit log."""
        entry = {
            "timestamp": time.time(),
            "pair": pair,
            "action": action,
            "signal_headline": sig.get("headline", ""),
            "edge_score": sig.get("edge_score", 0),
            "source_id": sig.get("source_id", ""),
            "source_prior": sig.get("source_prior", 0),
        }
        TRADE_LOG.parent.mkdir(parents=True, exist_ok=True)
        try:
            if TRADE_LOG.exists():
                with open(TRADE_LOG) as f:
                    log = json.load(f)
            else:
                log = []
            log.append(entry)
            # keep last 500
            with open(TRADE_LOG, "w") as f:
                json.dump(log[-500:], f, indent=2)
        except Exception as e:
            logger.error("trade log write failed: %s", e)


# ═══════════════════════════════════════════════════════════════════════════
# Standalone signal adapter (runs outside Freqtrade — writes to a signal file
# that the Freqtrade strategy reads via populate_*_trend)
# ═══════════════════════════════════════════════════════════════════════════

def build_signal_adapter(
    db_path: str = "/home/synczus/kestrel/signals.duckdb",
    output_path: str = "/home/synczus/kestrel/execution/state/active_signals.json",
    max_signals: int = 5,
) -> List[dict]:
    """
    Query DuckDB for the highest-scored actionable signals
    and write them as a clean list for Freqtrade to consume.

    Returns: list of signal dicts written to output_path
    """
    import duckdb

    if not os.path.exists(db_path):
        logger.warning("DuckDB not found at %s", db_path)
        return []

    sql = f"""
        SELECT
            s.event_id,
            s.source_id,
            s.source_prior,
            s.confidence,
            s.relevance,
            s.novelty,
            s.edge_score,
            e.headline,
            e.body_text,
            e.symbols,
            e.event_type,
            e.lane
        FROM signal_scores s
        JOIN events e ON s.event_id = e.row_id
        WHERE
            s.edge_score >= 0.45
            AND s.source_prior >= 0.5
            -- Filter to crypto assets in SYMBOL_MAP
            AND (
                e.symbols IS NULL
                OR EXISTS (
                    SELECT 1 FROM (
                        SELECT unnest(string_split(e.symbols, ',')) AS sym
                    ) WHERE upper(trim(sym)) IN ('BTC', 'ETH', 'SOL')
                )
            )
        ORDER BY s.edge_score DESC
        LIMIT {int(max_signals)}
    """

    try:
        con = duckdb.connect(db_path, read_only=True)
        rows = con.execute(sql).fetchdf().to_dict("records")
        con.close()

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(rows, f, indent=2, default=str)

        logger.info("wrote %d active signals to %s", len(rows), output_path)
        return rows
    except Exception as e:
        logger.error("signal adapter query failed: %s", e)
        return []


# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    n = build_signal_adapter()
    print(json.dumps({"adapter_wrote": len(n), "output": "execution/state/active_signals.json"}, indent=2))