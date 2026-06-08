#!/usr/bin/env python3
"""
Trade Pipeline — Signal-to-Trade Transformer
==============================================
Reads raw Striker signals from kestrel_signals.db, enriches them with:
  - Entry price (live market price)
  - 3 Take-profit levels (ATR-scaled, 30%/30%/40% partial exits)
  - Stop loss
  - Risk/reward ratio
  - Composite edge score (z-score + confidence decay + cross-source agreement)

Writes to: data/trade_signals.json (live feed) 
           data/trade_signals.duckdb (historical) 
           pulse/trade-ready.json (daily ranked)
"""
import json
import math
import os
import sqlite3
import time
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

KESTREL = Path(__file__).resolve().parent.parent
SIGNALS_DB = KESTREL / "kestrel_signals.db"
OUTPUT_FEED = KESTREL / "data" / "trade_signals.json"
OUTPUT_PULSE = KESTREL / "pulse" / "trade-ready.json"

# ── TP/SL Multipliers (ATR-based) ────────────────────────────────────────────
TP_MULTS = (1.0, 1.8, 2.8)          # TP1, TP2, TP3 multipliers
SL_MULT = 1.0                         # Stop-loss multiplier
PARTIAL_WEIGHTS = (0.3, 0.3, 0.4)    # 30% @ TP1, 30% @ TP2, 40% @ TP3

# ── Scoring weights ──────────────────────────────────────────────────────────
Z_ALPHA = 0.35
CV_BETA = 0.30
AGREE_DELTA = 0.20
RR_ETA = 0.15
DECAY_LAMBDA = 0.02                   # per-second decay (50% @ ~35s)

# ── Source trust weights ─────────────────────────────────────────────────────
SOURCE_WEIGHTS = {
    "striker-crypto": 0.85,
    "whale-alert": 0.90,
    "cryptoquant": 0.88,
    "cointelegraph": 0.66,
    "disclosetv": 0.62,
    "coindesk": 0.60,
}

# ── Live Price Sources ───────────────────────────────────────────────────────
SYMBOL_MAP = {
    "BTC-USD": ("bitcoin", "btcusd"),
    "ETH-USD": ("ethereum", "ethusd"),
    "SOL-USD": ("solana", "solusd"),
    "BTC": ("bitcoin", "btcusd"),
    "ETH": ("ethereum", "ethusd"),
    "SOL": ("solana", "solusd"),
}

def fetch_live_prices() -> dict:
    """Get current prices from CoinGecko + OHLC for ATR calc."""
    prices = {}
    try:
        ids = ",".join(v[0] for v in SYMBOL_MAP.values())
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd"
        req = urllib.request.Request(url, headers={"User-Agent": "Kestrel/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode())
        for sym, (cg_id, _) in SYMBOL_MAP.items():
            if data.get(cg_id, {}).get("usd"):
                prices[sym] = data[cg_id]["usd"]
    except Exception as e:
        print(f"[WARN] live price fetch: {e}")
    return prices

def fetch_ohlc(coin_id: str, days: int = 1) -> list:
    """Fetch OHLC candles for ATR calculation."""
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/ohlc?vs_currency=usd&days={days}"
        req = urllib.request.Request(url, headers={"User-Agent": "Kestrel/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode())
        return data  # [[timestamp, open, high, low, close], ...]
    except:
        return []

def compute_atr(ohlc: list, period: int = 14) -> float:
    """Compute ATR from OHLC data. Returns ATR as percentage of current price."""
    if len(ohlc) < period + 1:
        return 0.5  # fallback 0.5%
    
    trs = []
    for i in range(1, len(ohlc)):
        high = ohlc[i][2]
        low = ohlc[i][3]
        prev_close = ohlc[i-1][4]
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        trs.append(tr)
    
    atr = sum(trs[-period:]) / period
    current_price = ohlc[-1][4]
    if current_price == 0:
        return 0.5
    return atr / current_price * 100  # ATR as %

def compute_edge(signal: dict, atr_pct: float, recent_signals: list) -> float:
    """Compute composite edge score (0-100)."""
    price = signal.get("price", 0) or signal.get("entry_price", 0)
    move_pct = abs(signal.get("move_pct", 0) or 0.1)
    confidence = signal.get("confidence", 0) or 0.1
    age_seconds = signal.get("_age_seconds", 0)
    direction = signal.get("direction", "long")
    
    # (A) Z-score of move vs volatility
    if atr_pct > 0:
        z_raw = move_pct / atr_pct
    else:
        z_raw = 1.0
    sz = math.tanh(z_raw / 1.5)  # bounded [0,1)
    
    # (B) Confidence-velocity decay
    staleness = math.exp(-DECAY_LAMBDA * age_seconds) if age_seconds > 0 else 1.0
    scv = confidence * staleness
    
    # (C) Cross-source agreement
    same_count = sum(1 for s in recent_signals 
                     if s.get("direction") == direction 
                     and s.get("symbol") == signal.get("symbol"))
    total_count = max(len(recent_signals), 1)
    agreement = same_count / total_count
    sagree = 1 + max(0, agreement - 0.5)
    
    # (D) Risk/reward ratio
    # Expected reward from partial profit taking
    exp_reward = sum(w * m for w, m in zip(PARTIAL_WEIGHTS, TP_MULTS))
    rr = exp_reward / SL_MULT if SL_MULT > 0 else 1.0
    
    # Composite
    edge = 100 * (
        Z_ALPHA * sz +
        CV_BETA * scv +
        AGREE_DELTA * (sagree - 1) +
        RR_ETA * (min(rr, 3.0) - 1) / 2.0  # normalize RR benefit
    )
    
    return min(100, max(0, round(edge, 1)))


def enrich_signal(sig: dict, live_prices: dict, atr_map: dict) -> dict | None:
    """Enrich a raw signal into a trade-ready signal."""
    symbol = sig.get("symbol", "")
    direction = sig.get("direction", "long")
    
    # New schema: use entry_price (Striker v2). Old schema fallback: price
    entry = sig.get("entry_price", 0) or sig.get("price", 0)
    
    # Striker may already have computed TP/SL (new schema)
    striker_tp = sig.get("take_profit", 0)
    striker_sl = sig.get("stop_loss", 0)
    striker_atr = sig.get("atr_pct", None)
    
    # Use live price if available and more recent
    live_price = live_prices.get(symbol, entry)
    if live_price > 0 and abs(live_price - entry) / max(entry, 1) < 0.05:  # within 5%
        entry = live_price
    
    # Use Striker's ATR if available, else compute from OHLC
    if striker_atr and striker_atr > 0:
        atr_pct = striker_atr
    else:
        atr_pct = atr_map.get(symbol, 0.5)
    
    atr_dollars = entry * atr_pct / 100
    
    if entry <= 0 or atr_dollars <= 0:
        return None
    
    # If Striker already provided TP/SL, use them; otherwise compute
    if striker_tp and striker_sl and striker_tp > 0 and striker_sl > 0:
        tp_1 = round(striker_tp, 2)
        # Compute TP2/TP3 from ATR based on TP1's distance
        tp_dist = abs(tp_1 - entry)
        tp_2 = round(entry + 1.8 * (tp_1 - entry) if direction in ("long", "up") else entry - 1.8 * (entry - tp_1), 2)
        tp_3 = round(entry + 2.8 * (tp_1 - entry) if direction in ("long", "up") else entry - 2.8 * (entry - tp_1), 2)
        sl = round(striker_sl, 2)
    else:
        # Compute from scratch
        if direction in ("long", "up"):
            tp_1 = round(entry + TP_MULTS[0] * atr_dollars, 2)
            tp_2 = round(entry + TP_MULTS[1] * atr_dollars, 2)
            tp_3 = round(entry + TP_MULTS[2] * atr_dollars, 2)
            sl = round(entry - SL_MULT * atr_dollars, 2)
        else:
            tp_1 = round(entry - TP_MULTS[0] * atr_dollars, 2)
            tp_2 = round(entry - TP_MULTS[1] * atr_dollars, 2)
            tp_3 = round(entry - TP_MULTS[2] * atr_dollars, 2)
            sl = round(entry + SL_MULT * atr_dollars, 2)
    
    # Risk/reward
    risk_pct = abs(entry - sl) / entry * 100
    expected_reward = sum(w * abs(entry - tp) for w, tp in zip(PARTIAL_WEIGHTS, [tp_1, tp_2, tp_3]))
    avg_entry = entry
    rr_ratio = round(expected_reward / (abs(entry - sl) + 0.01), 2)
    
    # Partial targets
    partial_targets = [
        {"level": tp_1, "weight_pct": 30, "profit_pct": round(abs(tp_1 - entry) / entry * 100, 2)},
        {"level": tp_2, "weight_pct": 30, "profit_pct": round(abs(tp_2 - entry) / entry * 100, 2)},
        {"level": tp_3, "weight_pct": 40, "profit_pct": round(abs(tp_3 - entry) / entry * 100, 2)},
    ]
    
    return {
        "symbol": symbol,
        "direction": direction.upper(),
        "entry_price": entry,
        "stop_loss": sl,
        "take_profit_1": tp_1,
        "take_profit_2": tp_2,
        "take_profit_3": tp_3,
        "partial_targets": partial_targets,
        "atr_pct": round(atr_pct, 2),
        "risk_pct": round(risk_pct, 2),
        "expected_return_pct": round(sum(w * abs(tp["profit_pct"]) for w, tp in zip(PARTIAL_WEIGHTS, partial_targets)), 2),
        "risk_reward_ratio": rr_ratio,
        "confidence": sig.get("confidence", 0),
        "move_pct": sig.get("move_pct", 0),
        "source": sig.get("source", "striker"),
        "timestamp": sig.get("timestamp", datetime.now(timezone.utc).isoformat()),
        "signal_id": sig.get("id", ""),
    }


def get_recent_signals(window_minutes: int = 10) -> list[dict]:
    """Get recent raw signals from Striker DB."""
    signals = []
    if not SIGNALS_DB.exists():
        return signals
    
    try:
        conn = sqlite3.connect(str(SIGNALS_DB))
        conn.row_factory = sqlite3.Row
        now = datetime.now(timezone.utc)
        cutoff = (now - timedelta(minutes=window_minutes)).isoformat()
        
        rows = conn.execute("""
            SELECT id, timestamp, symbol, entry_price, direction, confidence, move_pct, volume, 
                   take_profit, stop_loss, atr_pct
            FROM signals
            WHERE timestamp >= ?
            ORDER BY confidence DESC
            LIMIT 200
        """, (cutoff,)).fetchall()
        
        for r in rows:
            sig = dict(r)
            ts = sig.get("timestamp", "")
            try:
                ts_parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                sig["_age_seconds"] = (now - ts_parsed).total_seconds()
            except:
                sig["_age_seconds"] = 0
            signals.append(sig)
        conn.close()
    except Exception as e:
        print(f"[WARN] DB read: {e}")
    
    return signals


def run_pipeline():
    """Main pipeline execution."""
    print("═══ Trade Pipeline ═══")
    print(f"Time: {datetime.now(timezone.utc).isoformat()}")
    
    # 1. Fetch live prices and OHLC data
    live_prices = fetch_live_prices()
    print(f"Live prices: {json.dumps(live_prices, indent=2)}")
    
    atr_map = {}
    for sym, (cg_id, _) in SYMBOL_MAP.items():
        ohlc = fetch_ohlc(cg_id, days=1)
        atr_pct = compute_atr(ohlc)
        atr_map[sym] = atr_pct
        print(f"  {sym}: ATR={atr_pct:.2f}%")
    
    # 2. Get recent signals
    signals = get_recent_signals()
    print(f"Recent signals: {len(signals)}")
    
    # Filter to signals with actual symbols and confidence
    valid = [s for s in signals if s.get("symbol") and s.get("confidence", 0) > 0.01]
    print(f"  Valid signals: {len(valid)}")
    
    # 3. Enrich each signal
    trade_signals = []
    for sig in valid:
        enriched = enrich_signal(sig, live_prices, atr_map)
        if enriched:
            # Compute composite edge score
            edge = compute_edge(sig, atr_map.get(sig["symbol"], 0.5), valid)
            enriched["edge_score"] = edge
            
            # Decision band
            if edge >= 70:
                enriched["rating"] = "HIGH"
            elif edge >= 55:
                enriched["rating"] = "TRADABLE"
            elif edge >= 35:
                enriched["rating"] = "WATCH"
            else:
                enriched["rating"] = "IGNORE"
            
            trade_signals.append(enriched)
    
    # 4. Sort by edge score
    trade_signals.sort(key=lambda x: x.get("edge_score", 0), reverse=True)
    
    # 5. Write outputs
    now = datetime.now(timezone.utc).isoformat()
    output = {
        "generated_at": now,
        "total_raw_signals": len(signals),
        "total_trade_signals": len(trade_signals),
        "live_prices": live_prices,
        "atr_summary": atr_map,
        "signals": trade_signals,
    }
    
    KESTREL / "data" / "trade_signals.json"
    OUTPUT_FEED.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FEED.write_text(json.dumps(output, indent=2))
    
    # Pulse output (compact, just the actionable ones)
    actionable = [s for s in trade_signals if s.get("rating") in ("HIGH", "TRADABLE")]
    pulse = {
        "generated_at": now,
        "count": len(actionable),
        "top_signals": actionable[:10],
    }
    OUTPUT_PULSE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PULSE.write_text(json.dumps(pulse, indent=2))
    
    print(f"\n Done. {len(trade_signals)} trade signals → {len(actionable)} actionable")
    print(f"  Feed: {OUTPUT_FEED}")
    print(f"  Pulse: {OUTPUT_PULSE}")
    
    return output


if __name__ == "__main__":
    run_pipeline()