"""
Multi-Timeframe Analyzer for Kestrel Striker Signals

Fetches OHLCV candles from Coinbase REST API for multiple timeframes,
computes basic technical analysis (trend, support/resistance, volatility),
and produces a structured MTF report.

Timeframes analyzed:
- 15min: short-term momentum
- 1h: intraday structure  
- 4h: medium-term trend
- 1d: daily bias
- 1w: macro context

Usage:
    from scoring.mtf_analyzer import analyze_mtf
    report = analyze_mtf("BTC-USD")
    print(report["verdict"])  # "bullish", "bearish", "neutral"
"""
import json
import logging
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("mtf_analyzer")

COINBASE_API = "https://api.exchange.coinbase.com"

# Coinbase granularity constants (in seconds)
GRANULARITY = {
    "15m": 900,      # 15 min candles
    "1h": 3600,      # 1 hour
    "6h": 21600,     # 6 hour (closest to 4h that Coinbase supports)
    "1d": 86400,     # 1 day
    "1w": 86400,     # 1 week (use daily candles, aggregate in analysis)
}

# How many candles to fetch per timeframe
CANDLE_COUNT = {
    "15m": 48,   # 12 hours
    "1h": 48,    # 48 hours
    "6h": 28,    # 7 days
    "1d": 30,    # 30 days
    "1w": 84,    # 12 weeks of daily candles (for weekly aggregation)
}

# EMA periods
EMA_PERIODS = {
    "15m": [9, 21, 50],
    "1h": [9, 21, 50],
    "4h": [9, 21, 50],
    "1d": [9, 21, 50, 200],
    "1w": [9, 21, 50],
}


def fetch_candles(symbol: str, granularity: int, count: int) -> list:
    """
    Fetch OHLCV candles from Coinbase Advanced Trade REST API.
    Returns list of [timestamp, open, high, low, close, volume] arrays.
    """
    end = int(time.time())
    start = end - (granularity * count * 2)  # 2x buffer to ensure enough data
    url = f"{COINBASE_API}/products/{symbol}/candles?granularity={granularity}&start={start}&end={end}"
    
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "KestrelStriker/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            if not data:
                logger.debug("fetch_candles %s %ds: empty response", symbol, granularity)
                return []
            # Coinbase returns [timestamp, low, high, open, close, volume]
            # Convert to [timestamp, open, high, low, close, volume]
            candles = []
            for c in data:
                if len(c) >= 6:
                    candles.append([c[0], c[3], c[2], c[1], c[4], c[5]])
            candles.sort(key=lambda x: x[0])
            logger.debug("fetch_candles %s %ds: %d candles", symbol, granularity, len(candles))
            return candles
    except urllib.error.HTTPError as e:
        if e.code == 429:
            logger.warning("fetch_candles %s %ds: rate limited, retrying...", symbol, granularity)
            time.sleep(2)
            return fetch_candles(symbol, granularity, count)
        logger.warning("fetch_candles %s %ds: HTTP %d", symbol, granularity, e.code)
        return []
    except (urllib.error.URLError, json.JSONDecodeError, OSError) as e:
        logger.warning("fetch_candles %s %ds: %s", symbol, granularity, e)
        return []


def compute_ema(prices: list, period: int) -> Optional[float]:
    """Compute exponential moving average for the last `period` prices."""
    if len(prices) < period:
        return None
    k = 2.0 / (period + 1)
    ema = sum(prices[:period]) / period
    for p in prices[period:]:
        ema = p * k + ema * (1 - k)
    return ema


def compute_rsi(prices: list, period: int = 14) -> Optional[float]:
    """Compute RSI for the last `period` prices."""
    if len(prices) < period + 1:
        return None
    gains = []
    losses = []
    for i in range(len(prices) - period, len(prices)):
        delta = prices[i] - prices[i - 1]
        if delta > 0:
            gains.append(delta)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(delta))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def analyze_timeframe(symbol: str, tf_name: str, candles: list, is_weekly: bool = False) -> dict:
    """
    Analyze a single timeframe and return structured assessment.
    
    Returns dict with: trend, strength (0-100), key_levels, ema_values, rsi
    
    For weekly analysis (is_weekly=True), aggregate daily candles into weekly OHLC.
    """
    if len(candles) < 10:
        return {"tf": tf_name, "error": "insufficient_data", "strength": 50, "trend": "neutral"}
    
    if is_weekly and len(candles) >= 7:
        # Aggregate daily candles into weekly
        weekly = []
        for i in range(0, len(candles), 7):
            week = candles[i:i+7]
            if len(week) >= 2:
                weekly_open = week[0][1]  # First candle's open
                weekly_high = max(c[2] for c in week)
                weekly_low = min(c[3] for c in week)
                weekly_close = week[-1][4]  # Last candle's close
                weekly_vol = sum(c[5] for c in week)
                weekly.append([week[0][0], weekly_open, weekly_high, weekly_low, weekly_close, weekly_vol])
        if len(weekly) >= 4:
            candles = weekly
        else:
            return {"tf": tf_name, "error": "insufficient_data_weekly", "strength": 50, "trend": "neutral"}
    
    closes = [c[4] for c in candles]
    highs = [c[2] for c in candles]
    lows = [c[3] for c in candles]
    current_price = closes[-1]
    
    # Trend direction: compare current close to SMA(20)
    sma20 = sum(closes[-20:]) / min(20, len(closes))
    trend = "bullish" if current_price > sma20 else "bearish"
    
    # Trend strength: how far from SMA (as %)
    trend_deviation = abs((current_price - sma20) / sma20 * 100)
    strength = min(100, trend_deviation * 20 + 50)
    
    # EMAs
    ema_values = {}
    for period in EMA_PERIODS.get(tf_name, [9, 21]):
        ema = compute_ema(closes, period)
        if ema:
            ema_values[f"ema_{period}"] = round(ema, 2)
    
    # RSI
    rsi = compute_rsi(closes, 14)
    rsi_signal = "neutral"
    if rsi is not None:
        if rsi > 70:
            rsi_signal = "overbought"
        elif rsi < 30:
            rsi_signal = "oversold"
    
    # Key levels: recent support (lowest 10% of range) and resistance (highest 10%)
    recent_range = max(highs[-20:]) - min(lows[-20:])
    support = round(min(lows[-20:]) + recent_range * 0.1, 2)
    resistance = round(max(highs[-20:]) - recent_range * 0.1, 2)
    
    # Volatility
    atr = sum([(h - l) for h, l in zip(highs[-14:], lows[-14:])]) / min(14, len(highs))
    atr_pct = round(atr / current_price * 100, 2) if current_price else 0
    
    # Check for EMA alignment (all EMAs pointing same direction = strong trend)
    ema_aligned = None
    if len(ema_values) >= 2:
        sorted_emas = sorted(ema_values.values())
        ema_aligned = trend == "bullish" and sorted_emas == list(ema_values.values())
    
    return {
        "tf": tf_name,
        "price": round(current_price, 2),
        "trend": trend,
        "strength": round(strength, 1),
        "rsi": round(rsi, 1) if rsi is not None else None,
        "rsi_signal": rsi_signal,
        "sma20": round(sma20, 2),
        "ema_values": ema_values,
        "ema_aligned": ema_aligned,
        "support": support,
        "resistance": resistance,
        "atr_pct": atr_pct,
        "candles_analyzed": min(len(candles), CANDLE_COUNT.get(tf_name, 30)),
    }


def aggregate_verdict(tf_results: dict) -> dict:
    """
    Combine all timeframe analyses into a single verdict.
    
    Weighting:
      15m: 10% (noise filter)
      1h:  20% (short-term)
      4h:  25% (medium-term)
      1d:  30% (daily bias)
      1w:  15% (macro context)
    """
    weights = {"15m": 0.10, "1h": 0.20, "6h": 0.25, "1d": 0.30, "1w": 0.15}
    
    bullish_score = 0
    bearish_score = 0
    total_weight = 0
    active_tfs = []
    
    for tf_name, result in tf_results.items():
        if "error" in result:
            continue
        weight = weights.get(tf_name, 0)
        total_weight += weight
        
        direction = result.get("trend", "neutral")
        strength = result.get("strength", 50) / 100.0
        
        if direction == "bullish":
            bullish_score += weight * strength
        elif direction == "bearish":
            bearish_score += weight * strength
        
        rsi_signal = result.get("rsi_signal", "neutral")
        if rsi_signal == "overbought" and direction == "bullish":
            bearish_score += weight * 0.3  # Overbought is a caution flag
        if rsi_signal == "oversold" and direction == "bearish":
            bullish_score += weight * 0.3  # Oversold is a caution flag
        
        active_tfs.append(tf_name)
    
    if total_weight == 0:
        return {"verdict": "neutral", "confidence": 50, "detail": "no_data"}
    
    bullish_score = round(bullish_score / total_weight * 100, 1)
    bearish_score = round(bearish_score / total_weight * 100, 1)
    
    if bullish_score > bearish_score + 10:
        verdict = "bullish"
        confidence = bullish_score
    elif bearish_score > bullish_score + 10:
        verdict = "bearish"
        confidence = bearish_score
    else:
        verdict = "neutral"
        confidence = max(bullish_score, bearish_score)
    
    return {
        "verdict": verdict,
        "confidence": round(min(100, confidence * 1.2), 1),  # Scale confidence up
        "bullish_score": bullish_score,
        "bearish_score": bearish_score,
        "active_timeframes": active_tfs,
    }


# ── Main Analyzer Entry Point ──────────────────────────────────────────────

def analyze_mtf(symbol: str, direction: Optional[str] = None) -> dict:
    """
    Analyze a symbol across all configured timeframes.
    
    Args:
        symbol: e.g. "BTC-USD"
        direction: Optional trade direction for context ("long" or "short")
    
    Returns:
        Dict with per-tf breakdown + aggregated verdict
    """
    tf_results = {}
    
    for tf_name in ["15m", "1h", "6h", "1d", "1w"]:
        granularity = GRANULARITY[tf_name]
        count = CANDLE_COUNT[tf_name]
        candles = fetch_candles(symbol, granularity, count)
        is_weekly = (tf_name == "1w")
        analysis = analyze_timeframe(symbol, tf_name, candles, is_weekly=is_weekly)
        tf_results[tf_name] = analysis
        
        if "error" not in analysis:
            logger.info("MTF %s %s: %s (strength=%.1f, RSI=%s)",
                        symbol, tf_name, analysis["trend"], analysis.get("strength", 50), analysis.get("rsi", "N/A"))
    
    verdict = aggregate_verdict(tf_results)
    
    # Direction vs verdict match
    direction_match = None
    if direction and verdict.get("verdict") in ("bullish", "bearish"):
        direction_match = (direction == verdict["verdict"])
    
    report = {
        "symbol": symbol,
        "direction": direction,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "timeframes": tf_results,
        "verdict": verdict,
        "direction_match": direction_match,
    }
    
    return report


# ── CLI Test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    symbol = sys.argv[1] if len(sys.argv) > 1 else "BTC-USD"
    direction = sys.argv[2] if len(sys.argv) > 2 else None
    
    print(f"MTF Analysis for {symbol}...")
    report = analyze_mtf(symbol, direction)
    print(json.dumps(report, indent=2, default=str))