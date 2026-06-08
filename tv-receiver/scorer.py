"""
Scoring Engine — 100-point weighted signal scorecard.
Rules-first, AI-second. Only calls LLM for gray-zone signals.
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger("tv-scorer")

CONFIG_PATH = Path(__file__).resolve().parent / "config.json"


class ScoringEngine:
    """
    Scores a TradingView alert payload against a weighted 100-point card.
    Buckets: trend/regime (40), volume/liquidity (25), setup quality (20),
             timeframe alignment (10), freshness (5).
    """

    def __init__(self, config_path: Path = CONFIG_PATH):
        with open(config_path) as f:
            self.cfg = json.load(f)
        self.buckets = self.cfg["scoring"]["buckets"]
        self.thresholds = self.cfg["thresholds"]

    # ── Public API ────────────────────────────────────────────────────

    def score(self, payload: dict) -> dict:
        """
        Accept a TradingView webhook payload, return scored result.
        """
        try:
            signal = self._normalize(payload)
        except ValueError as e:
            return {"error": str(e), "bucket": "ignore", "score": 0}

        scores = {}
        debug = {}

        # Each bucket scores independently
        scores["trend_regime"] = self._score_trend_regime(signal, debug)
        scores["volume_liquidity"] = self._score_volume_liquidity(signal, debug)
        scores["setup_quality"] = self._score_setup_quality(signal, debug)
        scores["timeframe_alignment"] = self._score_timeframe_alignment(signal, debug)
        scores["freshness"] = self._score_freshness(signal, debug)

        total = round(sum(scores.values()), 1)
        bucket = self._bucket(total)
        llm_needed = self._needs_llm(total)

        return {
            "score": total,
            "bucket": bucket,
            "breakdown": scores,
            "debug": debug,
            "llm_intervention_needed": llm_needed,
            "signal": signal,
            "scored_at": datetime.now(timezone.utc).isoformat(),
        }

    # ── Normalization ─────────────────────────────────────────────────

    def _normalize(self, payload: dict) -> dict:
        """Extract and validate required fields from any TradingView format."""
        symbol = payload.get("symbol") or payload.get("ticker") or ""
        price = payload.get("price") or payload.get("close") or 0
        direction = payload.get("direction") or payload.get("action") or "neutral"
        volume = payload.get("volume") or 0

        # Trend/regime fields
        trend = payload.get("trend") or payload.get("trend_alignment") or 0
        volatility = payload.get("volatility") or payload.get("volatility_regime") or "normal"
        htf = payload.get("htf_confluence") or payload.get("higher_timeframe") or 0
        sr = payload.get("support_resistance") or payload.get("sr_proximity") or 0

        # Volume fields
        vol_expansion = payload.get("volume_expansion") or payload.get("vol_expansion") or 0
        liquidity = payload.get("liquidity") or 0
        spread = payload.get("spread") or payload.get("spread_quality") or 0

        # Setup fields
        pattern = payload.get("pattern_clarity") or payload.get("pattern") or 0
        entry = payload.get("entry_precision") or payload.get("entry_quality") or 0
        rr = payload.get("risk_reward") or payload.get("rr") or 0

        # Timeframe
        mtf = payload.get("mtf_agreement") or payload.get("timeframe_alignment") or 0
        etf = payload.get("entry_timeframe_strength") or payload.get("tf_strength") or 0

        # Freshness
        age = payload.get("signal_age") or payload.get("age_seconds") or 0
        confirmations = payload.get("confirmations") or payload.get("confirmation_count") or 0

        if not symbol or not price:
            raise ValueError("Missing required fields: symbol and/or price")

        return {
            "symbol": str(symbol).upper(),
            "price": float(price),
            "direction": str(direction).lower(),
            "volume": float(volume),
            "trend": float(trend),
            "volatility": self._parse_volatility(volatility),
            "htf_confluence": float(htf),
            "sr_proximity": float(sr),
            "volume_expansion": float(vol_expansion),
            "liquidity": float(liquidity),
            "spread_quality": float(spread),
            "pattern_clarity": float(pattern),
            "entry_precision": float(entry),
            "risk_reward": float(rr),
            "mtf_agreement": float(mtf),
            "entry_timeframe_strength": float(etf),
            "signal_age_seconds": float(age),
            "confirmation_count": int(confirmations),
        }

    @staticmethod
    def _parse_volatility(v: Any) -> float:
        """Convert volatility string/float to 0-1 scale."""
        if isinstance(v, str):
            mapping = {"low": 0.3, "normal": 0.5, "high": 0.7, "extreme": 0.9, "elevated": 0.7}
            return mapping.get(v.lower(), 0.5)
        return min(max(float(v), 0), 1)

    # ── Scoring Functions ─────────────────────────────────────────────

    def _score_trend_regime(self, s: dict, debug: dict) -> float:
        """40 points: trend alignment, volatility regime, HTF confluence, S/R."""
        w = self.buckets["trend_regime"]["fields"]
        total = s["trend"] * w["trend_alignment"] * 2  # 0-30
        total += s["volatility"] * 0.6 * w["volatility_regime"]  # 0-10
        total += s["htf_confluence"] * w["htf_confluence"]  # 0-10
        total += s["sr_proximity"] * 0.4 * w["support_resistance"]  # 0-5
        raw = min(total, 40)
        debug["trend_regime"] = {
            "raw": round(raw, 2),
            "max": 40,
            "factors": {
                "trend": round(s["trend"], 2),
                "volatility": round(s["volatility"], 2),
                "htf": round(s["htf_confluence"], 2),
                "sr": round(s["sr_proximity"], 2),
            },
        }
        return raw

    def _score_volume_liquidity(self, s: dict, debug: dict) -> float:
        """25 points: volume expansion, liquidity depth, spread quality."""
        w = self.buckets["volume_liquidity"]["fields"]
        total = s["volume_expansion"] * w["volume_expansion"]  # 0-12
        total += s["liquidity"] * w["liquidity_depth"]  # 0-8
        total += s["spread_quality"] * 0.6 * w["spread_quality"]  # 0-5
        raw = min(total, 25)
        debug["volume_liquidity"] = {
            "raw": round(raw, 2),
            "max": 25,
            "factors": {
                "volume_expansion": round(s["volume_expansion"], 2),
                "liquidity": round(s["liquidity"], 2),
                "spread": round(s["spread_quality"], 2),
            },
        }
        return raw

    def _score_setup_quality(self, s: dict, debug: dict) -> float:
        """20 points: pattern clarity, entry precision, risk/reward."""
        w = self.buckets["setup_quality"]["fields"]
        total = s["pattern_clarity"] * w["pattern_clarity"]  # 0-8
        total += s["entry_precision"] * w["entry_precision"]  # 0-7
        total += s["risk_reward"] * w["risk_reward"]  # 0-5
        raw = min(total, 20)
        debug["setup_quality"] = {
            "raw": round(raw, 2),
            "max": 20,
            "factors": {
                "pattern_clarity": round(s["pattern_clarity"], 2),
                "entry_precision": round(s["entry_precision"], 2),
                "risk_reward": round(s["risk_reward"], 2),
            },
        }
        return raw

    def _score_timeframe_alignment(self, s: dict, debug: dict) -> float:
        """10 points: MTF agreement, entry timeframe strength."""
        w = self.buckets["timeframe_alignment"]["fields"]
        total = s["mtf_agreement"] * w["mtf_agreement"]  # 0-6
        total += s["entry_timeframe_strength"] * w["entry_timeframe_strength"]  # 0-4
        raw = min(total, 10)
        debug["timeframe_alignment"] = {
            "raw": round(raw, 2),
            "max": 10,
            "factors": {
                "mtf_agreement": round(s["mtf_agreement"], 2),
                "entry_tf_strength": round(s["entry_timeframe_strength"], 2),
            },
        }
        return raw

    def _score_freshness(self, s: dict, debug: dict) -> float:
        """5 points: signal age, confirmation count."""
        w = self.buckets["freshness"]["fields"]
        age_penalty = max(0, 1 - (s["signal_age_seconds"] / 300))
        conf_bonus = min(1, s["confirmation_count"] / 3) * w["confirmation_count"]
        total = age_penalty * w["signal_age"] + conf_bonus
        raw = min(total, 5)
        debug["freshness"] = {
            "raw": round(raw, 2),
            "max": 5,
            "factors": {
                "age_seconds": s["signal_age_seconds"],
                "age_penalty": round(age_penalty, 2),
                "confirmation_count": s["confirmation_count"],
                "conf_bonus": round(conf_bonus, 2),
            },
        }
        return raw

    # ── Classification ────────────────────────────────────────────────

    def _bucket(self, score: float) -> str:
        if score >= self.thresholds["trade"]:
            return "trade"
        elif score >= self.thresholds["watch"]:
            return "watch"
        return "ignore"

    def _needs_llm(self, score: float) -> bool:
        llm = self.cfg.get("llm_intervention", {})
        if not llm.get("enabled", False):
            return False
        return llm["score_floor"] <= score <= llm["score_ceiling"]
