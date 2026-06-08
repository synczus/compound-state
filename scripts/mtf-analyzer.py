#!/usr/bin/env python3
"""
Multi-Timeframe Analyzer v2 — Market Structure & Confluence
============================================================
Fetches OHLC at 30m, 1h, 4h, 1d timeframes via CoinGecko.
Analyzes trend direction, support/resistance, and generates a
confluence score for each tracked symbol.

Output: pulse/mtf-diagnosis.json (structured, queryable by dashboard)
"""
import json
import os
import time
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

KESTREL = Path(__file__).resolve().parent.parent
CACHE_DIR = KESTREL / "data" / "ohlc-cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = timedelta(minutes=15)
OUTPUT = KESTREL / "pulse" / "mtf-diagnosis.json"

# ── Configuration ────────────────────────────────────────────────────────────
TIMEFRAMES = {
    "30m": {"days": 2,  "period": 14, "cg_days": 2},   # CoinGecko: 30m candles at 2d
    "1h":  {"days": 7,  "period": 20, "cg_days": 7},
    "4h":  {"days": 14, "period": 20, "cg_days": 14},
    "1d":  {"days": 90, "period": 30, "cg_days": 90},
}
TF_WEIGHTS = {"30m": 0.05, "1h": 0.15, "4h": 0.35, "1d": 0.45}

COIN_MAP = {
    "BTC": "bitcoin", "BTC-USD": "bitcoin",
    "ETH": "ethereum", "ETH-USD": "ethereum",
    "SOL": "solana", "SOL-USD": "solana",
}


def cached_fetch(coin_id: str, days: int) -> list:
    """Fetch OHLC with disk cache. Cache hit avoids CoinGecko rate limit."""
    cache_file = CACHE_DIR / f"{coin_id}-{days}d.json"
    now = datetime.now()
    
    if cache_file.exists():
        cached = json.loads(cache_file.read_text())
        cache_time = datetime.fromisoformat(cached.get("_cached_at", "2000-01-01"))
        if now - cache_time < CACHE_TTL:
            return cached.get("data", [])
    
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/ohlc?vs_currency=usd&days={days}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Kestrel-MTF/2.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode())
        
        cache_file.write_text(json.dumps({
            "_cached_at": now.isoformat(),
            "coin_id": coin_id,
            "days": days,
            "data": data,
        }))
        time.sleep(1.0)  # Rate-limit: max 1 call per second to CoinGecko
        return data
    except Exception as e:
        if cache_file.exists():
            cached = json.loads(cache_file.read_text())
            print(f"[WARN] CoinGecko fetch failed for {coin_id} {days}d: {e} — using cached")
            return cached.get("data", [])
        return []


def compute_ema(prices: list, period: int) -> list:
    if len(prices) < period:
        return []
    mult = 2 / (period + 1)
    ema = [None] * (period - 1)
    ema.append(sum(prices[:period]) / period)
    for i in range(period, len(prices)):
        ema.append(prices[i] * mult + ema[-1] * (1 - mult))
    return [e for e in ema if e is not None]


def detect_trend(candles: list, period: int = 20) -> dict:
    if len(candles) < period:
        return {"direction": "neutral", "strength": 0, "ema_slope": 0}
    
    closes = [c[4] for c in candles]
    ema = compute_ema(closes, period)
    if len(ema) < 3:
        return {"direction": "neutral", "strength": 0}
    
    ema_recent = ema[-5:]
    slope = (ema_recent[-1] - ema_recent[0]) / ema_recent[0] * 100 if len(ema_recent) >= 2 else 0
    last_close = closes[-1]
    price_vs_ema = (last_close - ema[-1]) / ema[-1] * 100 if ema[-1] else 0
    
    # Higher highs / lower lows
    half = len(closes) // 2
    fh, sh = closes[:half], closes[half:]
    hh = max(sh) > max(fh) if len(fh) > 0 and len(sh) > 0 else False
    hl = min(sh) > min(fh) if len(fh) > 0 and len(sh) > 0 else False
    lh = max(sh) < max(fh) if len(fh) > 0 and len(sh) > 0 else False
    ll = min(sh) < min(fh) if len(fh) > 0 and len(sh) > 0 else False
    
    abs_slope = abs(slope)
    if slope > 0.05 and price_vs_ema > -0.5:
        direction = "bullish"
        strength = min(abs_slope * 5 + (0.3 if hh and hl else 0), 1.0)
    elif slope < -0.05 and price_vs_ema < 0.5:
        direction = "bearish"
        strength = min(abs_slope * 5 + (0.3 if lh and ll else 0), 1.0)
    else:
        direction = "neutral"
        strength = min(abs_slope * 3, 0.5)
    
    return {
        "direction": direction, "strength": round(strength, 2),
        "ema_slope": round(slope, 4), "price_vs_ema": round(price_vs_ema, 2),
    }


def swing_levels(prices: list, look_for: str = "highs") -> list:
    """Find swing highs (local maxima) or swing lows (local minima)."""
    levels = []
    n = len(prices)
    if n < 5:
        return levels
    for i in range(2, n - 2):
        if look_for == "highs":
            if prices[i] >= prices[i-1] and prices[i] >= prices[i-2] and \
               prices[i] >= prices[i+1] and prices[i] >= prices[i+2]:
                levels.append(prices[i])
        else:
            if prices[i] <= prices[i-1] and prices[i] <= prices[i-2] and \
               prices[i] <= prices[i+1] and prices[i] <= prices[i+2]:
                levels.append(prices[i])
    return levels


def cluster_levels(levels: list, threshold_pct: float = 0.5) -> list:
    if not levels:
        return []
    levels = sorted(set(levels))
    clusters, cur = [], [levels[0]]
    for l in levels[1:]:
        if abs(l - cur[-1]) / cur[-1] * 100 <= threshold_pct:
            cur.append(l)
        else:
            clusters.append(round(sum(cur) / len(cur), 2))
            cur = [l]
    if cur:
        clusters.append(round(sum(cur) / len(cur), 2))
    return clusters


def find_sr(candles: list, period: int = 50) -> dict:
    if len(candles) < 10:
        return {"support": 0, "resistance": 0, "atr_pct": 0}
    
    highs = [c[2] for c in candles[-period:]]
    lows = [c[3] for c in candles[-period:]]
    close = candles[-1][4]
    
    res_levels = cluster_levels(swing_levels(highs, "highs"))[-5:]
    sup_levels = cluster_levels(swing_levels(lows, "lows"))[:5]
    
    nearest_res = min((l for l in res_levels if l > close), default=0)
    nearest_sup = max((l for l in sup_levels if l < close), default=0)
    atr = (max(highs[-14:]) - min(lows[-14:])) / close * 100 if len(highs) >= 14 else 0
    
    return {"support": nearest_sup, "resistance": nearest_res,
            "support_levels": sup_levels, "resistance_levels": res_levels,
            "atr_pct": round(atr, 2)}


def analyze_symbol(symbol: str) -> dict:
    """Full multi-timeframe analysis for one symbol."""
    coin_id = COIN_MAP.get(symbol)
    if not coin_id:
        return {"symbol": symbol, "error": "unknown symbol"}
    
    tf_results = {}
    for name, cfg in TIMEFRAMES.items():
        candles = cached_fetch(coin_id, cfg["cg_days"])
        if len(candles) < 10:
            tf_results[name] = {"timeframe": name, "error": "insufficient data",
                                "candles": len(candles)}
            continue
        
        trend = detect_trend(candles, cfg["period"])
        sr = find_sr(candles, min(cfg["period"] * 2, 50))
        tf_results[name] = {
            "timeframe": name,
            "close": candles[-1][4],
            "candles": len(candles),
            "trend": trend,
            "support_resistance": sr,
        }
    
    if not tf_results:
        return {"symbol": symbol, "error": "no data"}
    
    # Confluence scoring
    score, tw = 0, 0
    sig_up = True  # default: analyze for long bias
    for name, r in tf_results.items():
        if r.get("error"):
            continue
        w = TF_WEIGHTS.get(name, 0.1)
        d, s = r["trend"]["direction"], r["trend"]["strength"]
        align = 1.0 if (sig_up and d == "bullish") or (not sig_up and d == "bearish") else (0.5 if d == "neutral" else 0.0)
        score += align * s * w * 100
        tw += w * (s if s > 0 else 0.3)
    
    confluence = round(score / tw, 1) if tw > 0 else 50
    confluence = min(100, max(0, confluence))
    
    return {
        "symbol": symbol,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "current_price": max((r.get("close", 0) for r in tf_results.values() if not r.get("error")), default=0),
        "timeframes": tf_results,
        "confluence": {
            "score": confluence,
            "rating": "HIGH" if confluence >= 70 else ("MODERATE" if confluence >= 40 else "LOW"),
        },
    }


def run():
    symbols = ["BTC-USD", "ETH-USD", "SOL-USD"]
    results = {}
    for sym in symbols:
        print(f"  Analyzing {sym}...")
        results[sym] = analyze_symbol(sym)
    
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "symbols": results,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(output, indent=2))
    print(f"\n  Written to {OUTPUT}")


if __name__ == "__main__":
    run()