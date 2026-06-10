"""
Market Striker Scoring Engine

Scores incoming trade signals from Striker (and TradingView webhooks)
using a weighted scoring model. Buckets: ignore, watch, trade.

Based on Chase's spec: 40/25/20/10/5 weighted scorecard
with optional LLM intervention in gray zone (35-50).

Usage:
    from scoring.scoring_engine import score_signal, SCORE_BUCKETS
    
    result = score_signal({
        "symbol": "BTC-USD",
        "direction": "long",
        "entry_price": 100000,
        "take_profit": 102000,
        "stop_loss": 99700,
        "confidence": 0.75,
        "move_pct": 1.2,
        "atr_pct": 0.8,
        "volume": 150.5
    })
    print(result["action"])  # "trade", "watch", or "ignore"
"""

import json
import time
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger("scoring_engine")

RULES_PATH = Path(__file__).parent / "rules_config.json"


def load_rules() -> dict:
    """Load scoring rules from config."""
    with open(RULES_PATH) as f:
        return json.load(f)


RULES = load_rules()


def score_signal(signal: dict) -> dict:
    """
    Score a signal using the weighted model.
    
    Args:
        signal: Dict with keys: symbol, direction, entry_price, take_profit,
                stop_loss, confidence, move_pct, atr_pct, volume (optional)
    
    Returns:
        Dict with: symbol, direction, score, action, breakdown, timestamp
    """
    rules = load_rules()
    weights = rules["weight_buckets"]
    breakdown = {}
    total = 0.0

    # 1. Trend & Regime (40 pts)
    trend_score = _score_trend_regime(signal, weights["trend_regime"])
    breakdown["trend_regime"] = trend_score
    total += trend_score["score"]

    # 2. Volume & Liquidity (25 pts)
    vol_score = _score_volume_liquidity(signal, weights["volume_liquidity"])
    breakdown["volume_liquidity"] = vol_score
    total += vol_score["score"]

    # 3. Setup Quality (20 pts)
    setup_score = _score_setup_quality(signal, weights["setup_quality"])
    breakdown["setup_quality"] = setup_score
    total += setup_score["score"]

    # 4. Timeframe Alignment (10 pts)
    tf_score = _score_timeframe_alignment(signal, weights["timeframe_alignment"])
    breakdown["timeframe_alignment"] = tf_score
    total += tf_score["score"]

    # 5. Recency (5 pts)
    recency_score = _score_recency(signal, weights["recency"])
    breakdown["recency"] = recency_score
    total += recency_score["score"]

    # Clamp
    total = max(0, min(100, total))

    # Determine action bucket
    buckets = rules["score_buckets"]
    action = "ignore"
    for bucket_name, bucket in sorted(buckets.items(), key=lambda x: x[1]["min"], reverse=True):
        if bucket["min"] <= total <= bucket["max"]:
            action = bucket_name
            break

    result = {
        "symbol": signal.get("symbol", "UNKNOWN"),
        "direction": signal.get("direction", "unknown"),
        "score": round(total, 1),
        "action": action,
        "breakdown": breakdown,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "needs_llm": rules.get("llm_intervention", {}).get("enabled", False)
                    and rules["llm_intervention"]["apply_when_score_between"][0] <= total
                    <= rules["llm_intervention"]["apply_when_score_between"][1],
    }

    if result["needs_llm"]:
        result["llm_hint"] = (
            f"Score {total}/100 is in gray zone. "
            f"Run LLM prompt: {rules['llm_intervention']['prompt_template']}"
        )

    return result


def _score_trend_regime(signal: dict, weights: dict) -> dict:
    """Score trend alignment and regime stability."""
    score = 0.0
    max_pts = weights["max"]
    direction = signal.get("direction", "long")
    move_pct = abs(signal.get("move_pct", 0))
    atr_pct = signal.get("atr_pct", 0.5)
    confidence = signal.get("confidence", 0.5)

    # Higher confidence = more weight
    det = {}
    
    # Trend direction match (15 pts)
    # Stronger move in trend direction = higher trend score
    trend_dir = min(15, (move_pct / max(atr_pct, 0.1)) * 5)
    det["trend_direction_match"] = round(min(15, trend_dir), 1)
    score += det["trend_direction_match"]

    # Regime stability (10 pts)
    # Lower ATR = more stable regime = higher score
    regime = max(0, 10 - (atr_pct * 5))
    det["regime_stability"] = round(min(10, regime), 1)
    score += det["regime_stability"]

    # Higher timeframe confluence (10 pts)
    # Placeholder — actual implementation needs HTF data
    det["higher_tf_confluence"] = round(confidence * 10, 1)
    score += det["higher_tf_confluence"]

    # Momentum divergence (5 pts)
    det["momentum_divergence"] = round(min(5, move_pct * 2), 1)
    score += det["momentum_divergence"]

    return {"score": round(min(max_pts, score), 1), "max": max_pts, "details": det}


def _score_volume_liquidity(signal: dict, weights: dict) -> dict:
    """Score volume confirmation and liquidity."""
    score = 0.0
    max_pts = weights["max"]
    volume = signal.get("volume", 0)
    det = {}

    # Volume spike ratio (15 pts)
    # Higher volume = more reliable signal
    if volume and volume > 0:
        vol_score = min(15, (volume / 100) * 3)
    else:
        vol_score = 7.5  # neutral if no volume data
    det["volume_spike_ratio"] = round(min(15, vol_score), 1)
    score += det["volume_spike_ratio"]

    # Liquidity depth (5 pts) — default mid if no data
    det["liquidity_depth"] = 3.0
    score += 3.0

    # Slippage risk (5 pts) — inverse of ATR
    atr = signal.get("atr_pct", 0.5)
    slippage = max(0, 5 - (atr * 3))
    det["slippage_risk"] = round(min(5, slippage), 1)
    score += det["slippage_risk"]

    return {"score": round(min(max_pts, score), 1), "max": max_pts, "details": det}


def _score_setup_quality(signal: dict, weights: dict) -> dict:
    """Score the technical setup quality."""
    score = 0.0
    max_pts = weights["max"]
    confidence = signal.get("confidence", 0)
    move_pct = abs(signal.get("move_pct", 0))
    det = {}

    # Signal freshness window (8 pts)
    det["signal_freshness_window"] = round(min(8, confidence * 8), 1)
    score += det["signal_freshness_window"]

    # Pattern clarity (7 pts) — stronger move = clearer signal
    clarity = min(7, abs(move_pct) * 5)
    det["pattern_clarity"] = round(clarity, 1)
    score += clarity

    # Entry price accuracy (5 pts)
    det["entry_price_accuracy"] = round(confidence * 5, 1)
    score += confidence * 5

    return {"score": round(min(max_pts, score), 1), "max": max_pts, "details": det}


def _score_timeframe_alignment(signal: dict, weights: dict) -> dict:
    """Score multi-timeframe alignment."""
    score = 0.0
    max_pts = weights["max"]
    det = {}

    # Weekly/daily alignment (5 pts) — placeholder needs HTF data
    det["weekly_daily_alignment"] = 3.0
    score += 3.0

    # Hourly confirmation (5 pts) — base on move_pct as proxy
    move = abs(signal.get("move_pct", 0))
    hourly = min(5, move * 3)
    det["hourly_confirmation"] = round(hourly, 1)
    score += hourly

    return {"score": round(min(max_pts, score), 1), "max": max_pts, "details": det}


def _score_recency(signal: dict, weights: dict) -> dict:
    """Score recency with decay. New signals get full points."""
    score = 0.0
    max_pts = weights["max"]
    det = {}

    # Full recency bonus — signals are fresh by definition from Striker
    det["last_5min_multiplier"] = weights["sub_weights"]["last_5min_multiplier"]
    score += det["last_5min_multiplier"]

    # No decay yet (signal just arrived)
    det["decay_half_life_minutes"] = weights["sub_weights"]["decay_half_life_minutes"]
    score += det["decay_half_life_minutes"]

    return {"score": round(min(max_pts, score), 1), "max": max_pts, "details": det}


# ── Batch Scoring ──────────────────────────────────────────────────────────

def score_batch(signals: list[dict]) -> list[dict]:
    """Score multiple signals. Returns scored results sorted by score desc."""
    results = [score_signal(s) for s in signals]
    results.sort(key=lambda r: r["score"], reverse=True)
    return results


# ── CLI Test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Test with a sample signal
    test = {
        "symbol": "BTC-USD",
        "direction": "long",
        "entry_price": 100000.00,
        "take_profit": 102500.00,
        "stop_loss": 99700.00,
        "confidence": 0.85,
        "move_pct": 1.5,
        "atr_pct": 0.8,
        "volume": 250.0,
    }
    result = score_signal(test)
    print(json.dumps(result, indent=2))
