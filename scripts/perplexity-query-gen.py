#!/usr/bin/env python3
"""
Perplexity Query Generator — runs every 30 min via cron.

Reads:
  - master-todo.md (top priorities)
  - cycle-state/current.json (hop baton)
  - signals.duckdb (pipeline metrics)

Generates 5-8 diverse Perplexity JSON queries spanning:
  - Trading infra (FreqTrade, MMR, Striker)
  - Signal pipeline (new sources, scoring, dedup)
  - Data science (backtesting, anomaly detection)
  - Infra (systemd, monitoring, automation)
  - Strategy (signal types, correlation, edge)

Writes to:
  - kestrel/pulse/perplexity-queries.json (latest batch)
  - kestrel/pulse/perplexity-queries.log (incremental)

Usage:
  python3 perplexity-query-gen.py           # generate + post to group
  python3 perplexity-query-gen.py --dry-run  # generate only, no post
"""
import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import duckdb

logger = logging.getLogger(__name__)

HOME = Path.home()
KESTREL = HOME / "kestrel"
TODOFILE = KESTREL / "master-todo.md"
CYCLE_FILE = KESTREL / "cycle-state" / "current.json"
DUCKDB_PATH = str(KESTREL / "signals.duckdb")
OUTPUT_DIR = KESTREL / "pulse"
OUTPUT_FILE = OUTPUT_DIR / "perplexity-queries.json"
LOG_FILE = OUTPUT_DIR / "perplexity-queries.log"

# ── Query Templates (broad coverage) ─────────────────────────────────

def gen_trading_queries(state: dict) -> list[dict]:
    """FreqTrade, MMR, Striker queries."""
    return [
        {
            "hop": "perplexity-query",
            "round": "auto",
            "title": "freqtrade-strategy-optimization",
            "context": (
                "FreqTrade is running in dry_run with DuckDBSignalStrategy "
                "reading a DuckDB ranked queue of 4671 scored signals. "
                "Buy threshold=20 (edge>=0.20), sell=15 (edge<=0.15). "
                "Pairs: BTC/USDC, ETH/USDC, SOL/USDC. $1K wallet, $10/trade, 3 max."
            ),
            "query": (
                "How can I optimize FreqTrade entry/exit logic for a signal-based strategy "
                "that reads scored events from an external DuckDB? Specifically position sizing "
                "by edge score, cooldown between trades, and avoiding same-direction re-entry "
                "within N candles."
            ),
        },
        {
            "hop": "perplexity-query",
            "round": "auto",
            "title": "mmr-ibkr-integration",
            "context": (
                "Meta-Market-Runner (MMR) is installed at /home/synczus/mmr/ with IBKR paper "
                "trading ready. We inject DuckDB signals via external_signal_override() into "
                "ma_crossover.py. Need to go live. MMR has trader, strategy, and data services."
            ),
            "query": (
                "I have MMR (Make Me Rich) algorithmic trading platform installed with IBKR paper "
                "trading. Which config files need credentials filled? What's the full path from "
                "strategy signal to IBKR order execution in MMR? How to verify paper orders are "
                "actually hitting the IBKR paper account?"
            ),
        },
        {
            "hop": "perplexity-query",
            "round": "auto",
            "title": "striker-threshold-tuning",
            "context": (
                "Striker detects basis divergence on BTC/ETH/SOL via Coinbase WebSocket. "
                "Current threshold is 0.1%, producing 25K+ signals/day. Target is 0.3%. "
                "Only 1.6% of signals hit >=0.3%, only 0.3% hit >=0.5%."
            ),
            "query": (
                "Best practices for tuning basis divergence thresholds for crypto perp/spot pairs? "
                "At 0.1% threshold we get 25K daily signals, 98% noise. What's the optimal threshold "
                "for BTC/ETH/SOL that balances signal count vs accuracy? Any volatility-adjusted "
                "threshold approaches?"
            ),
        },
        {
            "hop": "perplexity-query",
            "round": "auto",
            "title": "backtesting-signals-vs-price",
            "context": (
                "We have 25K+ historical Striker signals and 4671 scored pipeline events in DuckDB. "
                "We need to backtest whether high-edge signals predict price movement on BTC/ETH/SOL. "
                "Edge scores range 0.0-0.384. 64 signals currently above buy threshold of 0.20."
            ),
            "query": (
                "DuckDB approach for backtesting scored signals against subsequent 5m/15m/1h "
                "candlestick price data? I have signal_scores table with event timing and edge_score. "
                "Need to compare buy-side signals against next candle return. SQL query patterns "
                "for AS OF JOIN or time-bucket matching between signal events and OHLCV data?"
            ),
        },
    ]


def gen_pipeline_queries(state: dict) -> list[dict]:
    """Signal pipeline, sources, scoring queries."""
    return [
        {
            "hop": "perplexity-query",
            "round": "auto",
            "title": "cryptoquant-source-integration",
            "context": (
                "CryptoQuant is our highest remaining signal source at 0.89 baseline confidence. "
                "It provides on-chain exchange reserve data, netflow data, and stablecoin flows. "
                "Needs API key from user. Perplexity already designed the DuckDB schema additions."
            ),
            "query": (
                "What are the most actionable CryptoQuant API endpoints for a crypto signal pipeline? "
                "Exchange netflow, reserve risk, estimated leverage ratio — which have the strongest "
                "correlation with 1h/4h price movements on BTC? Best polling frequency?"
            ),
        },
        {
            "hop": "perplexity-query",
            "round": "auto",
            "title": "scoring-engine-enhancements",
            "context": (
                "Our scoring engine uses: source_prior * confidence * asset_relevance * novelty * "
                "recency_weight * cross_source_boost * fp_penalty * tier_mult * bluechip_mult. "
                "4671 scores computed. Edge range 0.0-0.384. Whale Alert signals dominate at 0.384. "
                "Source_feedback table exists but empty (no trade outcomes yet)."
            ),
            "query": (
                "Enhancements for a multi-factor signal scoring engine on DuckDB? Current edge_score "
                "formula uses 9 factors including time decay (30/120/720min half-lives) and "
                "cross-source agreement boost (+15% per agreeing source). What factors am I missing? "
                "Specifically: volatility normalization, regime detection (bull/bear/sideways), "
                "and volume-weighted confidence."
            ),
        },
    ]


def gen_infra_queries(state: dict) -> list[dict]:
    """System, monitoring, automation queries."""
    return [
        {
            "hop": "perplexity-query",
            "round": "auto",
            "title": "systemd-monitoring-dashboard",
            "context": (
                "Running 5 systemd user timers (watchdog 1m, score 15m, rss-all 4h, "
                "compound-pulse 30m, tldr daily noon). All jobs flock-guarded. User-level "
                "linger not enabled yet (sudo loginctl enable-linger synczus needed for "
                "reboot survival). Freshness watchdog checks log mtimes every 60s."
            ),
            "query": (
                "Best open-source system monitoring stack for a single Ubuntu server running "
                "Docker-free Python services? Specifically want: service health dashboard "
                "(systemd timer status, last-run timestamps, failure alerts), DuckDB metrics "
                "dashboard (event counts, scoring runs, trade_log), and a terminal UI that "
                "can show all this at a glance. Prefer Prometheus+node_exporter or something "
                "lighter? MMR budget is minimal — free tier preferred."
            ),
        },
        {
            "hop": "perplexity-query",
            "round": "auto",
            "title": "openrouter-cost-optimization",
            "context": (
                "Daily OpenRouter spend is ~$50.08 with a local $50 meter cap. No hard limit "
                "on the API key (limit: null). Two always-on agents (OpenClaw, Kairos). "
                "One disabled (Shannon). Kairos on require_mention mode. Sub-agents used "
                "aggressively for batch work. Seeking to reduce cost without reducing output."
            ),
            "query": (
                "Strategies to reduce OpenRouter API costs when running multi-agent systems? "
                "Current burn ~$50/day with 2 always-on agents. Already using require_mention "
                "for secondary agents, sub-agents with fresh context (~97% cheaper than "
                "in-session analysis). What are the next levers: model fallback chains, "
                "prompt compression, context window pruning, token budgets per agent?"
            ),
        },
    ]


def gen_creative_queries(state: dict) -> list[dict]:
    """Creative/exploratory queries outside the main focus areas."""
    return [
        {
            "hop": "perplexity-query",
            "round": "auto",
            "title": "cross-market-signal-correlation",
            "context": (
                "Our pipeline tracks 14 sources from crypto (Striker, Whale Alert, DefiLlama, "
                "a16z, CoinDesk, etc.) across 4671 scored events. Edge scores range 0.0-0.384. "
                "We haven't explored traditional markets (equities, forex, bonds, commodities) "
                "as signal sources or cross-asset correlations."
            ),
            "query": (
                "Which free/open APIs or RSS feeds provide meaningful cross-asset signal data? "
                "Specifically looking for: (1) equity/crypto correlation indicators, (2) USD "
                "index / DXY signals, (3) bond yield signals (10Y/2Y spread), (4) VIX or "
                "volatility signals, (5) gold/commodity signals that correlate with crypto. "
                "Want APIs with no auth or free tier API keys."
            ),
        },
        {
            "hop": "perplexity-query",
            "round": "auto",
            "title": "anomaly-detection-signal-pipeline",
            "context": (
                "4671 scored events across 14 sources in DuckDB. Whale Alert (0.384 avg edge) "
                "dominates the ranked queue. Telegram channels (0.047-0.161) form the tail. "
                "We need an anomalous event detector that flags when signal patterns shift "
                "abruptly — e.g., a sudden spike in bearish signals, or a source going quiet."
            ),
            "query": (
                "Lightweight anomaly detection on a DuckDB signal_scores table? I have 4671 "
                "rows with edge_score, source_id, asset_symbol, event_type, and timestamp. "
                "I want SQL queries or minimal Python that detects: (1) sudden source silence, "
                "(2) abrupt shift in bullish/bearish ratio, (3) edge_score distribution change. "
                "No ML — just statistical methods (z-score, rolling z-score, CUSUM)."
            ),
        },
    ]


def read_todo(state: dict) -> str:
    """Extract top priorities from master-todo.md."""
    try:
        text = TODOFILE.read_text()
        # Extract all - [ ] lines (unchecked)
        items = re.findall(r'- \[ \] (.*)', text)
        # Extract P0/P1 items
        priorities = [i for i in items if any(tag in i for tag in ['P0', 'P1', 'HIGH', 'URGENT'])]
        if not priorities:
            priorities = items[:5]
        return "\n".join(f"- {i}" for i in priorities[:5]) if priorities else "(empty)"
    except Exception as e:
        return f"(read error: {e})"


def read_pipeline_state() -> dict:
    """Gather current pipeline metrics for context."""
    state = {
        "time": datetime.now(timezone.utc).isoformat(),
        "todos": read_todo(state={}),
        "ft_running": False,
        "ft_api": False,
        "mmr_adapter_running": False,
    }
    # Check FreqTrade API
    try:
        import requests
        r = requests.get("http://127.0.0.1:8081/api/v1/ping", timeout=3)
        state["ft_api"] = r.status_code == 200 and r.json().get("status") == "pong"
    except Exception:
        pass
    # Check processes
    import subprocess
    try:
        out = subprocess.check_output(["ps", "aux"], text=True)
        state["ft_running"] = "freqtrade" in out.lower() and "DuckDB" in out
        state["mmr_adapter_running"] = "signal_to_mmr" in out
    except Exception:
        pass
    # DuckDB metrics
    try:
        con = duckdb.connect(DUCKDB_PATH, read_only=True)
        state["total_scored"] = con.execute("SELECT COUNT(*) FROM signal_scores").fetchone()[0]
        state["total_signals"] = con.execute("SELECT COUNT(*) FROM signals").fetchone()[0]
        state["top_sources"] = [
            dict(r) for r in
            con.execute("""
                SELECT source_id, COUNT(*) as count, ROUND(AVG(edge_score), 4) as avg_edge
                FROM signal_scores
                GROUP BY source_id
                ORDER BY avg_edge DESC
                LIMIT 5
            """).fetchdf().to_dict(orient="records")
        ]
        try:
            state["trade_log_count"] = con.execute("SELECT COUNT(*) FROM trade_log").fetchone()[0]
        except Exception:
            state["trade_log_count"] = 0
        con.close()
    except Exception as e:
        logger.warning(f"DuckDB read failed: {e}")
    return state


def build_queries(state: dict) -> list[dict]:
    """Generate diverse Perplexity queries across all domains."""
    queries = []
    # Trading
    queries.extend(gen_trading_queries(state))
    # Pipeline
    queries.extend(gen_pipeline_queries(state))
    # Infra
    queries.extend(gen_infra_queries(state))
    # Creative
    queries.extend(gen_creative_queries(state))
    # Shuffle for variety (seed by timestamp-hash to avoid always same order)
    import random
    rng = random.Random(int(time.time()) // 1800)  # new order every 30 min
    rng.shuffle(queries)
    return queries


def format_for_group(queries: list[dict], state: dict) -> str:
    """Format the output for Telegram group posting (no markdown tables)."""
    lines = []
    lines.append(f"🧠 Perplexity Queries — {datetime.now().strftime('%H:%M ET')}")
    lines.append("")
    lines.append(f"Pipeline: {state.get('total_scored', '?')} scored, "
                 f"{state.get('total_signals', '?')} raw signals")
    lines.append(f"FreqTrade: {'🟢' if state.get('ft_api') else '🔴'}  "
                 f"MMR: {'🟢' if state.get('mmr_adapter_running') else '🔴'}  "
                 f"Trades: {state.get('trade_log_count', 0)}")
    if state.get("top_sources"):
        top = state["top_sources"][0]
        lines.append(f"Top source: {top['source_id']} (avg edge {top['avg_edge']})")
    lines.append("")
    lines.append("To-dos:")
    lines.append(f"{state.get('todos', '(empty)')}")
    lines.append("")
    # Show first 4 queries
    for q in queries[:4]:
        title = q["title"].replace("-", " ").title()
        lines.append(f"🔥 {title}")
        lines.append(f"  {q['query'][:200]}...")
        lines.append("")
    lines.append(f"Full JSON with all {len(queries)} queries → kestrel/pulse/perplexity-queries.json")
    lines.append("")
    lines.append("Copy the JSON file or ask me to post it.")
    return "\n".join(lines)


def save(queries: list[dict], state: dict):
    """Save queries to output file."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": state["time"],
        "state": {k: v for k, v in state.items() if k != "time"},
        "queries": queries,
    }
    OUTPUT_FILE.write_text(json.dumps(payload, indent=2, default=str))
    # Append to log
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps({"ts": state["time"], "count": len(queries)}) + "\n")
    logger.info(f"Saved {len(queries)} queries to {OUTPUT_FILE}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Perplexity Query Generator")
    parser.add_argument("--dry-run", action="store_true", help="Generate only, don't post")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [perplexity-qgen] %(message)s",
    )

    state = read_pipeline_state()
    queries = build_queries(state)
    save(queries, state)

    msg = format_for_group(queries, state)
    print(msg)
    print()
    print(json.dumps({"generated_at": state["time"], "count": len(queries)}))


if __name__ == "__main__":
    main()
