"""
Multi-Timezone Framework — fetches OHLCV from Coinbase across timeframes,
computes trend, volatility regime, and support/resistance proximity.
Plugged into the TV receiver as the context layer between Striker and execution.
"""
import json
import logging
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

log = logging.getLogger("mtf")

COINBASE_CANDLES = "https://api.exchange.coinbase.com/products/{symbol}/candles"

# Granularity in seconds: 3600=1h, 21600=6h, 86400=1d
TIMEFRAMES = {
    "1h": {"granularity": 3600, "candles": 48, "ema_period": 12},
    "4h": {"granularity": 21600, "candles": 30, "ema_period": 9},
    "1d": {"granularity": 86400, "candles": 20, "ema_period": 9},
}

CACHE_PATH = Path(__file__).resolve().parent / "mtf_cache.json"
CACHE_TTL = 120  # seconds — don't re-fetch within 2min per symbol


def _load_cache() -> dict:
    if CACHE_PATH.exists():
        try:
            return json.loads(CACHE_PATH.read_text())
        except Exception:
            return {}
    return {}


def _save_cache(cache: dict):
    CACHE_PATH.write_text(json.dumps(cache, indent=2))


def _fetch_candles(symbol: str, granularity: int, limit: int = 50) -> Optional[list]:
    """Fetch OHLCV candles from Coinbase REST API."""
    url = COINBASE_CANDLES.format(symbol=symbol)
    params = f"?granularity={granularity}"
    full_url = url + params

    try:
        req = urllib.request.Request(full_url, headers={"User-Agent": "kestrel-mtf/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        # Coinbase returns [[time, low, high, open, close, volume], ...]
        # Sort ascending by time
        if not data or not isinstance(data, list):
            return None
        data.sort(key=lambda x: x[0])
        return data[-limit:]  # last N candles
    except Exception as e:
        log.warning("Coinbase fetch failed %s g=%d: %s", symbol, granularity, e)
        return None


def _ema(values: list[float], period: int) -> float:
    """Simple EMA calculation over last `period` values."""
    if len(values) < period:
        period = len(values)
    if period == 0:
        return values[-1] if values else 0
    k = 2 / (period + 1)
    ema = sum(values[:period]) / period
    for v in values[period:]:
        ema = v * k + ema * (1 - k)
    return ema


def analyze_timeframe(symbol: str, tf_name: str, tf_config: dict) -> dict:
    """
    Fetch candles for one timeframe and compute:
    - Trend: 0-1 (0=strong downtrend, 1=strong uptrend)
    - Volatility: 0-1 (normalized ATR over period)
    - S/R proximity: 0-1 (how close current price is to recent high/low)
    """
    cache = _load_cache()
    cache_key = f"{symbol}_{tf_name}"
    now = time.time()

    # Check cache
    cached = cache.get(cache_key)
    if cached and (now - cached.get("fetched_at", 0)) < CACHE_TTL:
        return cached["analysis"]

    candles = _fetch_candles(symbol, tf_config["granularity"], tf_config["candles"] + 5)
    if not candles or len(candles) < tf_config["ema_period"] + 2:
        return {"timeframe": tf_name, "error": "insufficient data", "trend": 0.5, "volatility": 0.5, "sr_proximity": 0.5}

    closes = [c[4] for c in candles]
    highs = [c[2] for c in candles]
    lows = [c[1] for c in candles]
    current_price = closes[-1]

    # ── Trend via EMA slope ────────────────────────────────────────────
    ema_val = _ema(closes, tf_config["ema_period"])
    ema_prev = _ema(closes[:-1], tf_config["ema_period"])
    ema_slope = (ema_val - ema_prev) / (ema_prev or 1)

    # Normalize slope to 0-1: -0.02 to +0.02 maps to 0-1
    trend = min(max(ema_slope * 50 + 0.5, 0), 1)

    # ── Volatility via ATR ──────────────────────────────────────────────
    tr_values = []
    for i in range(1, len(candles)):
        hl = highs[i] - lows[i]
        hc = abs(highs[i] - closes[i - 1])
        lc = abs(lows[i] - closes[i - 1])
        tr_values.append(max(hl, hc, lc))

    if tr_values:
        atr = sum(tr_values) / len(tr_values)
        volatility = min(atr / (current_price or 1) * 100, 1)
    else:
        volatility = 0.5

    # ── S/R Proximity ──────────────────────────────────────────────────
    period_high = max(highs[-20:]) if len(highs) >= 20 else max(highs)
    period_low = min(lows[-20:]) if len(lows) >= 20 else min(lows)
    price_range = period_high - period_low
    if price_range > 0:
        # How close to the high (1=at high, 0=at low)
        sr_proximity = (current_price - period_low) / price_range
        sr_proximity = min(max(sr_proximity, 0), 1)
    else:
        sr_proximity = 0.5

    # Trend direction string
    if trend > 0.65:
        direction = "uptrend"
    elif trend < 0.35:
        direction = "downtrend"
    else:
        direction = "ranging"

    analysis = {
        "timeframe": tf_name,
        "trend": round(trend, 3),
        "trend_direction": direction,
        "volatility": round(volatility, 3),
        "sr_proximity": round(sr_proximity, 3),
        "current_price": current_price,
        "period_high": period_high,
        "period_low": period_low,
        "atr_pct": round(volatility, 4),
        "candle_count": len(candles),
    }

    # Cache it
    cache[cache_key] = {"fetched_at": now, "analysis": analysis}
    _save_cache(cache)

    return analysis


def multi_timeframe(symbol: str) -> dict:
    """
    Run MTF analysis across all defined timeframes.
    Returns a composite picture:
      - `timeframes`: per-tf breakdown
      - `composite_trend`: weighted average (daily > 4h > 1h)
      - `regime`: bullish, bearish, mixed, ranging
      - `htf_confluence`: 0-1, how aligned timeframes are
    """
    results = {}
    for tf_name, tf_config in TIMEFRAMES.items():
        results[tf_name] = analyze_timeframe(symbol, tf_name, tf_config)

    # Weighted composite (daily=0.5, 4h=0.3, 1h=0.2)
    weights = {"1d": 0.5, "4h": 0.3, "1h": 0.2}
    composite = 0
    total_weight = 0
    directions = []

    for tf_name, weight in weights.items():
        tf = results.get(tf_name, {})
        if "error" not in tf:
            composite += tf.get("trend", 0.5) * weight
            total_weight += weight
            directions.append(tf.get("trend_direction", "ranging"))

    if total_weight > 0:
        composite /= total_weight
    else:
        composite = 0.5

    # Confluence: how aligned are the timeframes?
    trend_values = [results[tf].get("trend", 0.5) for tf in TIMEFRAMES if "error" not in results.get(tf, {})]
    if trend_values:
        spread = max(trend_values) - min(trend_values)
        htf_confluence = min(max(1 - spread * 2, 0), 1)
    else:
        htf_confluence = 0.5

    # Regime
    bullish = sum(1 for d in directions if d == "uptrend")
    bearish = sum(1 for d in directions if d == "downtrend")
    if bullish >= 2 and bearish == 0:
        regime = "bullish"
    elif bearish >= 2 and bullish == 0:
        regime = "bearish"
    elif bullish >= 1 and bearish >= 1:
        regime = "mixed"
    else:
        regime = "ranging"

    return {
        "symbol": symbol,
        "regime": regime,
        "composite_trend": round(composite, 3),
        "htf_confluence": round(htf_confluence, 3),
        "timeframes": results,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }


def enrich_scoring_payload(payload: dict) -> dict:
    """
    Take a raw TradingView payload, fetch MTF data for the symbol,
    and inject MTF-derived fields so the scoring engine uses real data.
    """
    symbol = payload.get("symbol") or payload.get("ticker") or ""
    if not symbol:
        return payload

    mtf = multi_timeframe(symbol)
    enriched = dict(payload)

    # Inject MTF context into fields the scoring engine reads
    if "error" not in mtf:
        # Trend alignment
        enriched["trend_alignment"] = mtf["composite_trend"]
        # HTF confluence
        enriched["htf_confluence"] = mtf["htf_confluence"]
        # Volatility regime
        avg_vol = sum(
            mtf["timeframes"].get(tf, {}).get("volatility", 0.5)
            for tf in TIMEFRAMES
            if "error" not in mtf["timeframes"].get(tf, {})
        ) / 3
        if avg_vol > 0.4:
            enriched["volatility_regime"] = "elevated" if avg_vol > 0.6 else "high"
        elif avg_vol < 0.15:
            enriched["volatility_regime"] = "low"
        else:
            enriched["volatility_regime"] = "normal"
        enriched["volatility"] = avg_vol

        # S/R proximity from daily
        daily = mtf["timeframes"].get("1d", {})
        if "error" not in daily:
            enriched["sr_proximity"] = daily.get("sr_proximity", 0.5)

        # Timeframe alignment
        enriched["mtf_agreement"] = mtf["htf_confluence"]

        # Add full MTF context for downstream
        enriched["_mtf"] = mtf

    return enriched