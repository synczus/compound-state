"""
execution/state/README.md — Execution Layer State Files

This directory holds all runtime state for the dual execution layer
(Freqtrade + MMR), shared between cron-driven adapters and strategy files.

## Files

### active_signals.json
Written by:  build_signal_adapter() in duckdb_signal_strategy.py
Written by:  dual_supervisor.py (Stage 1)
Read by:     DuckDBSignalStrategy._load_signal_queue() in Freqtrade
             signal_to_mmr.run() for MMR lane
Format:      Array of signal dicts from DuckDB signal_scores table,
             filtered to edge_score >= 0.45 and source_prior >= 0.5
             Limited to top 5 signals.

### mmr_signals.json
Written by:  signal_to_mmr.run()
Read by:     MMR external_signal listener (TBD — injection point not confirmed)
Format:      {"signals": [...], "updated_at": timestamp}
             Each signal: {symbol, direction, strength, source, reason, edge_score, source_id, timestamp}

### ft_trades.json
Written by:  DuckDBSignalStrategy._log_trade()
Format:      Array of trade audit entries with timestamp, pair, action,
             signal_headline, edge_score, source_id, source_prior
             Kept at max 500 entries.

### mmr_trades.json
Written by:  signal_to_mmr.run()
Format:      Array of MMR trade audit entries with timestamp, count, symbols
             Kept at max 200 entries.

### dual_audit.json
Written by:  dual_supervisor.py log_audit()
Format:      Array of execution cycle summaries with budget_level,
             budget_remaining, crypto_signals, mmr_signals, errors
             Kept at max 200 entries.

## Lifecycle

dual_supervisor.py (cron every 5min):
  1. Loads cycle-state/current.json → budget status
  2. Queries DuckDB → active_signals.json
  3. Freqtrade reads active_signals.json on its next candle
  4. signal_to_mmr.py reads active_signals.json → mmr_signals.json
  5. All actions logged to dual_audit.json

## Budget Guard Thresholds

$50.00 — Daily OR cap
$45.00 — Trade stop line (leaves $5 buffer for non-trade LLM calls)
$ 5.00 — Degradation floor — only crypto lane runs below this
$ 0.00 — Exhausted — no trades execute

## Asset Routing

Crypto (Freqtrade / Coinbase):
  BTC/USDC, ETH/USDC, SOL/USDC
  Source: Striker price signals, Whale Alert, Cointelegraph

Equities/ETFs (MMR / IBKR):
  SPY, QQQ, IWM, GLD, SLV, TLT, SHY, DXY
  Source: Disclose.tv geopolitical, macro signals, Cointelegraph macro
"""