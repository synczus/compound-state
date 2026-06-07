"""
MiroFish — Budget-Aware Signal Gate for AutoHOP.

Sits between Noise Gate and OpenRouter calls.
Scores signals for cost-to-conviction ratio and gates LLM routing.
Only high-conviction signals with remaining budget hit expensive models.

Governance: Asyncio / Dataclasses with __slots__ / Strict Typing / Standard Logging
"""

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone, date
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("kestrel.mirofish")

# ---------------------------------------------------------------------------
# Budget config from env
# ---------------------------------------------------------------------------
DAILY_BUDGET = float(os.getenv("MIROFISH_DAILY_BUDGET", "5.0"))          # $5/day default
CHEAP_MODEL_COST = float(os.getenv("MIROFISH_CHEAP_COST", "0.0003"))     # ~$0.0003 per cheap call
PREMIUM_MODEL_COST = float(os.getenv("MIROFISH_PREMIUM_COST", "0.002"))  # ~$0.002 per premium call
MIN_CONVICTION_TO_ROUTE = int(os.getenv("MIROFISH_MIN_CONVICTION", "5")) # Min 1-10 score to route to premium

LEDGER_PATH = Path(os.getenv("MIROFISH_LEDGER_PATH", 
    str(Path.home() / "kestrel" / "swarm" / "mirofish_ledger.json")))

SQUIRREL_INBOX = Path(os.getenv("MIROFISH_SQUIRREL_INBOX",
    str(Path.home() / "archivesquirrel" / "inbox")))


@dataclass(slots=True)
class SignalScore:
    """Result of MiroFish scoring on a signal."""
    input_id: str
    conviction_score: int        # 1-10
    estimated_cost: float        # USD estimated cost to process
    recommended_model: str       # 'reject', 'cheap', or 'premium'
    reasoning: str
    budget_remaining: float
    timestamp: str


@dataclass(slots=True)
class DailyLedger:
    """Tracks spend per day."""
    date_str: str
    total_spend: float = 0.0
    signals_accepted: int = 0
    signals_rejected: int = 0
    cheap_calls: int = 0
    premium_calls: int = 0

    def remaining(self) -> float:
        return max(0.0, DAILY_BUDGET - self.total_spend)

    def can_route(self, cost: float) -> bool:
        return self.remaining() >= cost

    def to_dict(self) -> dict:
        return {
            "date": self.date_str,
            "total_spend": round(self.total_spend, 4),
            "signals_accepted": self.signals_accepted,
            "signals_rejected": self.signals_rejected,
            "cheap_calls": self.cheap_calls,
            "premium_calls": self.premium_calls,
            "remaining": round(self.remaining(), 4),
        }


class MiroFish:
    """
    Budget-aware signal gate for AutoHOP.

    Scoring dimensions:
    1. Signal freshness (recent data = higher score)
    2. Actionability (clear buy/sell/hedge triggers)
    3. Leverage potential (asymmetry, contrarian signals)
    4. Data richness (multiple sources, confirmed)
    5. Cost efficiency (cheap model can handle this?)
    """

    def __init__(self):
        self._ledger: Optional[DailyLedger] = None
        self._ensure_dirs()
        self._load_ledger()

    def _ensure_dirs(self):
        """Ensure squirrel inbox exists."""
        SQUIRREL_INBOX.mkdir(parents=True, exist_ok=True)

    def _load_ledger(self):
        """Load or initialize today's ledger."""
        today = date.today().isoformat()
        if LEDGER_PATH.exists():
            try:
                data = json.loads(LEDGER_PATH.read_text())
                if data.get("date") == today:
                    self._ledger = DailyLedger(
                        date_str=data["date"],
                        total_spend=data.get("total_spend", 0.0),
                        signals_accepted=data.get("signals_accepted", 0),
                        signals_rejected=data.get("signals_rejected", 0),
                        cheap_calls=data.get("cheap_calls", 0),
                        premium_calls=data.get("premium_calls", 0),
                    )
                    return
            except (json.JSONDecodeError, KeyError):
                pass
        
        self._ledger = DailyLedger(date_str=today)

    def _save_ledger(self):
        """Persist ledger to disk."""
        if self._ledger:
            LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
            LEDGER_PATH.write_text(json.dumps(self._ledger.to_dict(), indent=2))

    def _score_conviction(self, content: str) -> Tuple[int, str]:
        """
        Score signal conviction 1-10.

        1-3: Low conviction — reject (waste of budget)
        4-6: Medium conviction — route to cheap model only
        7-8: High conviction — premium model worth it
        9-10: Critical — route to premium regardless
        """
        score = 0
        reasons = []
        content_lower = content.lower()

        # Freshness markers (recent data = more valuable)
        freshness_terms = {"just in", "breaking", "new", "flash", "alert", "now", "urgent"}
        if any(t in content_lower for t in freshness_terms):
            score += 2
            reasons.append("fresh")

        # Actionability — trade-specific triggers (weighted higher for crypto/stocks)
        action_terms = {
            "buy": 2, "sell": 2, "hedge": 3, "liquidate": 3,
            "entry": 2, "exit": 2, "drain": 3, "surge": 2,
            "crash": 3, "pump": 2, "support": 2, "resistance": 2,
            "breakout": 2, "break": 1, "stop": 1,
        }
        action_score = 0
        for term, weight in action_terms.items():
            if term in content_lower:
                action_score += weight
        score += min(action_score, 5)
        if action_score > 0:
            reasons.append(f"actionable ({action_score}pts)")

        # Price data present (hard numbers)
        has_price = "$" in content
        has_percent = "%" in content
        has_number = any(c.isdigit() for c in content)
        data_score = 0
        if has_price:
            data_score += 2
        if has_percent:
            data_score += 2
        if has_number:
            data_score += 1
        if data_score > 0:
            score += data_score
            reasons.append(f"hard data ({data_score}pts)")

        # Leverage / asymmetry
        asymmetry_terms = {"unexpectedly", "contrary", "overlooked", "despite", "however",
                          "divergence", "diverging", "inversion"}
        if any(t in content_lower for t in asymmetry_terms):
            score += 2
            reasons.append("asymmetric")

        # Convergence (multiple sources)
        confirm_terms = {"confirmed", "verified", "across", "multiple", "consistent", "sources"}
        confirm_count = sum(1 for t in confirm_terms if t in content_lower)
        if confirm_count >= 2:
            score += 2
            reasons.append("convergence")
        elif confirm_count == 1:
            score += 1
            reasons.append("source cited")

        # Volume / magnitude markers
        magnitude_terms = {"thousand", "million", "billion", "40%", "50%", "huge", "massive", "x100"}
        if any(t in content_lower for t in magnitude_terms):
            score += 1
            reasons.append("magnitude")

        # Penalty for vagueness (reduces score floor)
        vague_terms = {"maybe", "could", "might", "possibly", "consider", "thinking about",
                       "generally", "perhaps", "somewhat", "kinda", "sort of"}
        vague_count = sum(1 for t in vague_terms if t in content_lower)
        if vague_count > 0:
            score = max(score - (vague_count * 2), 0)
            reasons.append(f"vague (-{vague_count * 2})")

        # Length penalty — very short signals are low conviction
        word_count = len(content.split())
        if word_count < 5:
            score = max(score - 1, 0)
            reasons.append("too short (-1)")

        return min(score, 10), "; ".join(reasons) if reasons else "no strong markers"

    def _estimate_model_cost(self, conviction: int) -> Tuple[str, float]:
        """
        Decide which model tier and estimate cost.
        """
        if conviction <= 3:
            return "reject", 0.0
        elif conviction <= 6:
            return "cheap", CHEAP_MODEL_COST
        elif conviction <= 8:
            return "premium", PREMIUM_MODEL_COST
        else:
            return "premium", PREMIUM_MODEL_COST  # Critical signal, spend what it takes

    async def score(self, input_id: str, content: str) -> SignalScore:
        """
        Score a signal and determine if it should be routed.

        Returns a SignalScore with recommended model tier.
        """
        if self._ledger is None:
            self._load_ledger()

        conviction, reasoning = self._score_conviction(content)
        model_tier, cost = self._estimate_model_cost(conviction)
        remaining = self._ledger.remaining() if self._ledger else 0.0

        # Reject if budget too low for even cheap model
        if not self._ledger.can_route(CHEAP_MODEL_COST) and conviction < MIN_CONVICTION_TO_ROUTE:
            return SignalScore(
                input_id=input_id,
                conviction_score=conviction,
                estimated_cost=cost,
                recommended_model="reject",
                reasoning=f"Budget exhausted (${remaining:.4f} remaining) + low conviction ({conviction})",
                budget_remaining=remaining,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        # Reject if conviction too low and premium
        if model_tier == "premium" and conviction < MIN_CONVICTION_TO_ROUTE:
            return SignalScore(
                input_id=input_id,
                conviction_score=conviction,
                estimated_cost=cost,
                recommended_model="reject",
                reasoning=f"Conviction ({conviction}) below MIN_CONVICTION_TO_ROUTE ({MIN_CONVICTION_TO_ROUTE})",
                budget_remaining=remaining,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        # Premium but not enough budget — downgrade to cheap
        if model_tier == "premium" and not self._ledger.can_route(PREMIUM_MODEL_COST):
            if self._ledger.can_route(CHEAP_MODEL_COST):
                model_tier = "cheap"
                cost = CHEAP_MODEL_COST
                reasoning += "; premium budget exceeded, downgraded to cheap"
            else:
                return SignalScore(
                    input_id=input_id,
                    conviction_score=conviction,
                    estimated_cost=cost,
                    recommended_model="reject",
                    reasoning=f"All budget tiers exhausted (${remaining:.4f} remaining)",
                    budget_remaining=remaining,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )

        return SignalScore(
            input_id=input_id,
            conviction_score=conviction,
            estimated_cost=cost,
            recommended_model=model_tier,
            reasoning=reasoning,
            budget_remaining=remaining if self._ledger else 0.0,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def record_spend(self, model_tier: str, cost: float):
        """Record a completed LLM call cost."""
        if self._ledger is None:
            return
        self._ledger.total_spend += cost
        self._ledger.signals_accepted += 1
        if model_tier == "cheap":
            self._ledger.cheap_calls += 1
        else:
            self._ledger.premium_calls += 1
        self._save_ledger()
        logger.info(
            "MIROFISH: spent $%.4f (%s) | today=$%.4f/$%.2f | cheap=%d premium=%d",
            cost, model_tier, self._ledger.total_spend, DAILY_BUDGET,
            self._ledger.cheap_calls, self._ledger.premium_calls,
        )

    def record_rejection(self):
        """Record a rejected signal."""
        if self._ledger:
            self._ledger.signals_rejected += 1
            self._save_ledger()

    def log_to_squirrel(self, score: SignalScore, content_preview: str):
        """Write a structured note to ArchiveSquirrel inbox."""
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        entry = f"""---
id: mf_{ts}
type: trading
title: "MiroFish gate decision — {score.recommended_model}"
tags: [mirofish, budget-gate, {score.recommended_model}]
source: kestrel
project: kestrel
created: {datetime.now(timezone.utc).isoformat()}
author: hermes
status: active
---

**MiroFish Gate Decision**

| Field | Value |
|---|---|
| Input ID | {score.input_id} |
| Conviction | {score.conviction_score}/10 |
| Recommended | {score.recommended_model} |
| Est. Cost | ${score.estimated_cost:.4f} |
| Budget Remaining | ${score.budget_remaining:.4f} |
| Reasoning | {score.reasoning} |

**Content preview:**
```
{content_preview[:500]}
```
"""
        path = SQUIRREL_INBOX / f"mirofish_{ts}.md"
        path.write_text(entry)

    def status(self) -> dict:
        """Return current status dict."""
        if self._ledger:
            return self._ledger.to_dict()
        return {"date": "unknown", "total_spend": 0, "remaining": DAILY_BUDGET}

    def reset_daily(self):
        """Force reset today's ledger (for testing / manual override)."""
        self._ledger = DailyLedger(date_str=date.today().isoformat())
        self._save_ledger()


# ---------------------------------------------------------------------------
# Singleton for import
# ---------------------------------------------------------------------------
_instance: Optional[MiroFish] = None


def get_mirofish() -> MiroFish:
    global _instance
    if _instance is None:
        _instance = MiroFish()
    return _instance


def is_gate_active() -> bool:
    """Returns True if MiroFish gate is installed and has budget."""
    mf = get_mirofish()
    if mf._ledger:
        return mf._ledger.remaining() > CHEAP_MODEL_COST
    return False


async def main():
    """CLI test — score sample signals and show routing decisions."""
    mf = get_mirofish()
    
    test_signals = [
        ("pos-001", "Breaking: BTC liquidity pool unexpectedly draining 40%. Immediate hedge required."),
        ("pos-002", "Maybe consider looking into the market at some point. Could be interesting."),
        ("pos-003", "Confirmed by three sources: Protocol upgrade delayed 2 weeks. Contrary to consensus, buy signal."),
        ("pos-004", "Just in: ETH $1,558 support broke. Verified across 4 exchanges. Sell pressure mounting."),
    ]
    
    print(f"{'='*60}")
    print(f"MiroFish Gate — Daily Budget: ${DAILY_BUDGET}")
    print(f"{'='*60}")
    
    for input_id, content in test_signals:
        score = await mf.score(input_id, content)
        print(f"\n  [{score.recommended_model.upper():7s}] {input_id}")
        print(f"  Conviction: {score.conviction_score}/10 | Est: ${score.estimated_cost:.4f}")
        print(f"  Reason: {score.reasoning}")
        print(f"  Budget remaining: ${score.budget_remaining:.4f}")
        
        if score.recommended_model != "reject":
            mf.record_spend(score.recommended_model, score.estimated_cost)
        else:
            mf.record_rejection()
        
        mf.log_to_squirrel(score, content)
    
    print(f"\n{'='*60}")
    print(f"Final ledger: {json.dumps(mf.status(), indent=2)}")


if __name__ == "__main__":
    asyncio.run(main())
