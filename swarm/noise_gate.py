import asyncio
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Set
from datetime import datetime, timezone
from .noise_telemetry import record_noise_gate_decision

# Governance Strict: Asyncio / Dataclasses with __slots__ / Strict Typing / Standard Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("kestrel.noise_gate")

@dataclass(slots=True)
class RawInput:
    content: str
    source: str
    timestamp: datetime
    metadata: dict = field(default_factory=dict)

@dataclass(slots=True)
class FilterResult:
    input_id: str
    leverage_score: int
    is_noise: bool
    reasoning: str
    promoted_content: Optional[str] = None

class NoiseGate:
    """
    Sovereign Filter for Kestrel Markets.
    Prevents high-entropy garbage from poisoning the Hub.
    """
    
    def __init__(
        self, 
        temporal_decay_limit: int = 60, # Minutes
        min_leverage_threshold: int = 3
    ):
        self.temporal_decay_limit = temporal_decay_limit
        self.min_leverage_threshold = min_leverage_threshold
        # Terms that trigger immediate 'Semantic Fluff' penalties
        self.fluff_terms: Set[str] = {
            "it is important to consider",
            "generally speaking",
            "potential for growth",
            "in the current climate",
            "it is worth noting",
            "going to the moon",
            "to the moon"
        }

    def _check_temporal_decay(self, timestamp: datetime) -> bool:
        now = datetime.now(timezone.utc)
        delta = (now - timestamp).total_seconds() / 60
        return delta > self.temporal_decay_limit

    def _calculate_leverage(self, content: str) -> tuple[int, List[str]]:
        score = 0
        reasons = []
        
        # 1. Semantic Fluff Penalty
        content_lower = content.lower()
        fluff_count = sum(1 for term in self.fluff_terms if term in content_lower)
        score -= (fluff_count * 2)
        if fluff_count > 0:
            reasons.append(f"Semantic fluff detected ({fluff_count} terms)")

        # 2. Asymmetry / Contrarian Signal (Heuristic: Look for contradicting keywords)
        contradict_terms = {"however", "contrary to", "despite", "overlooked", "unexpectedly"}
        if any(term in content_lower for term in contradict_terms):
            score += 4
            reasons.append("Asymmetry/Contrarian signal detected")

        # 3. Direct Actionability (Heuristic: Look for triggers)
        action_terms = {"hedge", "liquidate", "buy", "sell", "entry", "exit", "drain", "surge"}
        if any(term in content_lower for term in action_terms):
            score += 5
            reasons.append("Direct actionability detected")

        # 4. Engineering Structural Shift Detection (Commit signals)
        struct_terms = {"refactor", "breaking", "rewrite", "overhaul", "migration", "migrate"}
        if any(term in content_lower for term in struct_terms):
            score += 4
            reasons.append("Structural shift (engineering refactor/rewrite)")

        # 5. Security / Vulnerability detection (per SPRINT: "fix" alone is too broad/noisy)
        # Require "fix" + explicit vuln/crash context, or standalone high-signal vuln terms.
        vuln_terms = {"security", "vulnerability", "cve", "exploit", "crash", "vulnerab"}
        has_vuln = any(term in content_lower for term in vuln_terms)
        has_fix = "fix" in content_lower or "fixed" in content_lower
        has_critical_context = any(t in content_lower for t in ["security", "vulnerab", "cve", "exploit", "crash", "auth", "rce", "overflow", "injection"])
        if has_vuln or (has_fix and has_critical_context):
            score += 5
            reasons.append("Security/vulnerability signal")

        # 6. Dependency / Ecosystem shift
        dep_terms = {"version update", "upgrade", "deprecat", "bump", "api change", "llama.cpp"}
        if any(term in content_lower for term in dep_terms):
            score += 3
            reasons.append("Dependency/ecosystem shift")

        # 7. Convergence (Heuristic: Look for evidence markers)
        evidence_terms = {"confirmed by", "across sources", "consistent with", "verified"}
        if any(term in content_lower for term in evidence_terms):
            score += 3
            reasons.append("Convergence detected")

        return score, reasons

    async def filter(self, raw_input: RawInput) -> FilterResult:
        """
        The Gatekeeper Loop: Scrubs input and assigns leverage score.
        """
        input_id = f"{raw_input.source}_{raw_input.timestamp.timestamp()}"
        
        # Immediate Purge: Temporal Decay
        if self._check_temporal_decay(raw_input.timestamp):
            record_noise_gate_decision(
                input_id=input_id,
                source=raw_input.source,
                content=raw_input.content,
                score=0,
                threshold=self.min_leverage_threshold,
                is_noise=True,
                reasoning="Temporal decay exceeded limit",
                metadata=raw_input.metadata,
            )
            return FilterResult(
                input_id=input_id,
                leverage_score=0,
                is_noise=True,
                reasoning="Temporal decay exceeded limit"
            )

        score, reasons = self._calculate_leverage(raw_input.content)
        is_noise = score < self.min_leverage_threshold
        
        reasoning = "; ".join(reasons) if reasons else "No significant markers found"
        
        if is_noise:
            logger.info(f"PURGE: {input_id} | Score: {score} | Reason: {reasoning}")
        else:
            logger.info(f"PROMOTE: {input_id} | Score: {score} | Reason: {reasoning}")

        record_noise_gate_decision(
            input_id=input_id,
            source=raw_input.source,
            content=raw_input.content,
            score=score,
            threshold=self.min_leverage_threshold,
            is_noise=is_noise,
            reasoning=reasoning,
            metadata=raw_input.metadata,
        )

        return FilterResult(
            input_id=input_id,
            leverage_score=score,
            is_noise=is_noise,
            reasoning=reasoning,
            promoted_content=raw_input.content if not is_noise else None
        )

async def main():
    gate = NoiseGate()
    
    test_inputs = [
        RawInput(
            content="The market is generally speaking in a state of potential for growth. It is important to consider the risks.",
            source="GenericBlog",
            timestamp=datetime.now(timezone.utc)
        ),
        RawInput(
            content="Unexpectedly, liquidity pool X is draining rapidly. Immediate hedge required.",
            source="OnChainBot",
            timestamp=datetime.now(timezone.utc)
        ),
        RawInput(
            content="Confirmed by three sources: The protocol update is delayed. Contrary to consensus, this is a buy signal.",
            source="InsiderFeed",
            timestamp=datetime.now(timezone.utc)
        ),
        RawInput(
            content="Old news from last week.",
            source="Archive",
            timestamp=datetime.now(timezone.utc).replace(day=1) # Force decay
        )
    ]

    for inp in test_inputs:
        res = await gate.filter(inp)
        print(f"Source: {inp.source} | Noise: {res.is_noise} | Score: {res.leverage_score} | Reason: {res.reasoning}")

if __name__ == "__main__":
    asyncio.run(main())
