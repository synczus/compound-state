#!/usr/bin/env python3
"""
Multi-Timeframe Analyzer — Market Structure & Confluence
========================================================
For a given symbol, fetches OHLC data at Daily, 4h, 1h, 15min timeframes,
analyzes trend, support/resistance, and generates a structured diagnosis.

Used by: trade-pipeline.py (called per-symbol when a high-confidence signal appears)
Output: structured MTF diagnosis with trend alignment score
"""
import json
import math
import urllib.request
from datetime import datetime, timezone
from typing import Optional

# ── Timeframe Configuration ──────────────────────────────────────────────────
TIMEFRAMES = {
    "15m": {"days": 2,  "period": 20},
    "1h":  {"days": 7,  "period": 20},
    "4h":  {"days": 14, "period": 20},
    "1d":  {"days": 90, "period": 30},
}

# ── Weight for confluence scoring ────────────────────────────────────────────
TF_WEIGHTS = {"15m": 0.10, "1h": 0.20, "4h": 0.30, "1d": 0.40}

COIN_MAP = {
    "BTC": "bitcoin", "BTC-USD": "bitcoin",
    "ETH": "ethereum", "ETH-USD": "ethereum",
    "SOL": "solana", "SOL-USD": "solana",
}

MONTH_BIN_MS = 28 * 24 * 60 * 60 * 1000  # 28 days in ms for CoinGecko


def fetch_binned_ohlc(coin_id: str, days: int) -> list:
    """Fetch OHLC data from CoinGecko. Falls back to larger bins when needed."""
    bins = {1: "1", 2: "1", 7: "1", 14: "1", 30: "1", 90: "2"}  # 1=hourly, 2=daily
    param = bins.get(days, "1")
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/ohlc?vs_currency=usd&days={days}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Kestrel-MTF/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode())
            return data  # [[timestamp_ms, open, high, low, close], ...]
    except Exception as e:
        return []


def compute_ema(prices: list, period: int) -> list:
    """Compute EMA for a price series."""
    if len(prices) < period:
        return [None] * len(prices)
    multiplier = 2 / (period + 1)
    ema = [None] * (period - 1)
    ema.append(sum(prices[:period]) / period)
    for i in range(period, len(prices)):
        ema.append(prices[i] * multiplier + ema[-1] * (1 - multiplier))
    return ema


def detect_trend(candles: list, period: int = 20) -> dict:
    """Analyze trend direction and strength from OHLC data."""
    if len(candles) < period:
        return {"direction": "neutral", "strength": 0, "ema_slope": 0}
    
    closes = [c[4] for c in candles]
    ema = compute_ema(closes, period)
    recent_ema = [e for e in ema if e is not None]
    
    if len(recent_ema) < period // 2:
        return {"direction": "neutral", "strength": 0}
    
    # EMAs typically lag; use the last few values to gauge slope
    lookback = min(5, len(recent_ema))
    if lookback < 2:
        return {"direction": "neutral", "strength": 0}
    
    ema_recent = recent_ema[-lookback:]
    slope = (ema_recent[-1] - ema_recent[0]) / ema_recent[0] * 100
    
    # Price position relative to EMA
    last_close = closes[-1]
    ema_last = recent_ema[-1]
    price_vs_ema = (last_close - ema_last) / ema_last * 100 if ema_last else 0
    
    # Higher highs / higher lows check
    recent_closes = closes[-min(period, len(closes)):]
    half = len(recent_closes) // 2
    first_half = recent_closes[:half]
    second_half = recent_closes[half:]
    
    if len(first_half) > 1 and len(second_half) > 1:
        higher_high = max(second_half) > max(first_half)
        higher_low = min(second_half) > min(first_half)
        lower_high = max(second_half) < max(first_half)
        lower_low = min(second_half) < min(first_half)
    else:
        higher_high = higher_low = lower_high = lower_low = False
    
    # Direction decision
    if slope > 0.1 and price_vs_ema > -0.5:
        direction = "bullish"
        strength = min(abs(slope) * 5 + (0.3 if (higher_high and higher_low) else 0), 1.0)
    elif slope < -0.1 and price_vs_ema < 0.5:
        direction = "bearish"
        strength = min(abs(slope) * 5 + (0.3 if (lower_high and lower_low) else 0), 1.0)
    else:
        direction = "neutral"
        strength = min(abs(slope) * 3, 0.5)
    
    return {
        "direction": direction,
        "strength": round(strength, 2),
        "ema_slope": round(slope, 4),
        "price_vs_ema": round(price_vs_ema, 2),
        "highest_high": max(c[-2] for c in candles[-period:]),
        "lowest_low": min(c[-3] for c in candles[-period:]),
    }


def find_support_resistance(candles: list, period: int = 50) -> dict:
    """Identify key support and resistance levels."""
    if len(candles) < 10:
        return {"support": 0, "resistance": 0, "levels": []}
    
    highs = [c[2] for c in candles[-period:]]
    lows = [c[3] for c in candles[-period:]]
    closes = [c[4] for c in candles[-period:]]
    
    last_close = closes[-1]
    
    # Find swing highs (local maxima)
    swing_highs = []
    for i in range(2, len(highs) - 2):
        if highs[i] >= highs[i-1] and highs[i] >= highs[i-2] and \
           highs[i] >= highs[i+1] and highs[i] >= highs[i+2]:
            swing_highs.append(highs[i])
    
    # Find swing lows (local minima)
    swing_lows = []
    for i in range(2, len(lows) - 2):
        if lows[i] <= lows[i-1] and lows[i] <= lows[i-2] and \
           lows[i] <= lows[i+1] and lows[i] <= lows[i+2]:
            swing_lows.append(lows[i])
    
    # Cluster nearby levels
    def cluster(levels, threshold_pct=0.5):
        if not levels:
            return []
        levels = sorted(set(levels))
        clusters = []
        current = [levels[0]]
        for l in levels[1:]:
            if abs(l - current[-1]) / current[-1] * 100 <= threshold_pct:
                current.append(l)
            else:
                clusters.append(round(sum(current) / len(current), 2))
                current = [l]
        if current:
            clusters.append(round(sum(current) / len(current), 2))
        return clusters
    
    resistance_levels = cluster(swing_highs)[-5:] if swing_highs else []
    support_levels = cluster(swing_lows)[:5] if swing_lows else []
    
    # Find nearest levels
    nearest_resistance = min((l for l in resistance_levels if l > last_close), default=0)
    nearest_support = max((l for l in support_levels if l < last_close), default=0)
    
    # Current range
    atr = (max(highs[-14:]) - min(lows[-14:])) / last_close * 100 if len(highs) >= 14 else 0
    
    return {
        "support": nearest_support,
        "resistance": nearest_resistance,
        "support_levels": support_levels,
        "resistance_levels": resistance_levels,
        "atr_pct": round(atr, 2),
    }


def diagnose_timeframe(candles: list, label: str) -> dict:
    """Full diagnosis for a single timeframe."""
    trend = detect_trend(candles)
    sr = find_support_resistance(candles)
    
    last_candle = candles[-1] if candles else None
    current_price = last_candle[4] if last_candle else 0
    
    return {
        "timeframe": label,
        "current_price": current_price,
        "candles_analyzed": len(candles),
        "trend": trend,
        "support_resistance": sr,
    }


def compute_confluence(tf_results: dict, signal_direction: str) -> float:
    """Score how well the signal direction aligns with higher TF trends. 0-100."""
    score = 0
    total_weight = 0
    
    for tf_name, result in tf_results.items():
        weight = TF_WEIGHTS.get(tf_name, 0.1)
        direction = result["trend"]["direction"]
        strength = result["trend"]["strength"]
        
        # Aligned?
        sig_up = signal_direction.lower() in ("long", "up", "buy")
        tf_up = direction == "bullish"
        
        if (sig_up and tf_up) or (not sig_up and direction == "bearish"):
            alignment = 1.0
        elif direction == "neutral":
            alignment = 0.5
        else:
            alignment = 0.0
        
        contribution = alignment * strength * weight * 100
        score += contribution
        total_weight += weight * strength if strength > 0 else weight * 0.3
    
    if total_weight > 0:
        score = score / total_weight
    else:
        score = 50  # neutral default
    
    return min(100, max(0, round(score, 1)))


def full_mtf_analysis(symbol: str, signal_direction: str = "long") -> dict:
    """
    Full multi-timeframe analysis for a symbol.
    Returns structured diagnosis with trend alignment score.
    """
    coin_id = COIN_MAP.get(symbol)
    if not coin_id:
        return {"error": f"Unknown symbol: {symbol}"}
    
    tf_results = {}
    all_ok = True
    
    for tf_name, cfg in TIMEFRAMES.items():
        candles = fetch_binned_ohlc(coin_id, cfg["days"])
        
        # If we got less than expected, try a longer period
        if len(candles) < 10:
            tf_results[tf_name] = {
                "timeframe": tf_name,
                "current_price": 0,
                "candles_analyzed": len(candles),
                "trend": {"direction": "neutral", "strength": 0, "ema_slope": 0},
                "support_resistance": {"support": 0, "resistance": 0, "atr_pct": 0},
                "error": "insufficient data"
            }
            all_ok = False
            continue
        
        result = diagnose_timeframe(candles, tf_name)
        tf_results[tf_name] = result
    
    if not tf_results:
        return {"error": "No timeframe data available"}
    
    # Compute confluence score
    confluence = compute_confluence(tf_results, signal_direction)
    
    # Build composite diagnosis
    current_price = 0
    latest_tf = list(tf_results.keys())[-1] if tf_results else None
    if latest_tf and tf_results[latest_tf].get("current_price"):
        current_price = tf_results[latest_tf]["current_price"]
    
    # Check overall market regime
    higher_tf = tf_results.get("1d", {}).get("trend", {}).get("direction", "neutral")
    mid_tf = tf_results.get("4h", {}).get("trend", {}).get("direction", "neutral")
    lower_tf = tf_results.get("1h", {}).get("trend", {}).get("direction", "neutral")
    
    return {
        "symbol": symbol,
        "current_price": current_price,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "timeframes": tf_results,
        "confluence": {
            "score": confluence,
            "rating": "HIGH" if confluence >= 70 else ("MODERATE" if confluence >= 40 else "LOW"),
            "signal_direction": signal_direction.upper(),
            "higher_tf_trend": higher_tf,
            "mid_tf_trend": mid_tf,
            "lower_tf_trend": lower_tf,
        },
        "regime": {
            "primary": higher_tf,
            "secondary": mid_tf,
            "description": f"{higher_tf.upper()} primary trend, {mid_tf.upper()} on 4h, {lower_tf.upper()} on 1h",
        },
        "nearest_levels": {
            key: {k: v for k, v in tf_results[key].get("support_resistance", {}).items() 
                  if k in ("support", "resistance")}
            for key in tf_results
        },
    }


if __name__ == "__main__":
    import sys
    symbol = sys.argv[1] if len(sys.argv) > 1 else "BTC-USD"
    direction = sys.argv[2] if len(sys.argv) > 2 else "long"
    result = full_mtf_analysis(symbol, direction)
    print(json.dumps(result, indent=2))