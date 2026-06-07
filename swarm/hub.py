import asyncio
import logging
import os
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from .noise_gate import NoiseGate, RawInput, FilterResult
from .noise_telemetry import get_noise_gate_context
from .openrouter_client import call_specialist, is_available as or_available
from .hop_chains import HopChain, get_chain, run_mock_hop
from .mirofish import get_mirofish, MiroFish, CHEAP_MODEL_COST, PREMIUM_MODEL_COST

# Governance Strict: Asyncio / Dataclasses with __slots__ / Strict Typing / Standard Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("kestrel.hub")

@dataclass(slots=True)
class HopResult:
    model: str
    findings: str
    next_hop: Optional[str]
    status: str             # CONTINUE | TERMINATE_SHIP | TERMINATE_KILL
    reasoning: str
    leverage_score: int      # 1-10 (Vibe Director metric)

@dataclass(slots=True)
class GlobalState:
    context_hub: List[str] = field(default_factory=list)
    hop_history: List[HopResult] = field(default_factory=list)
    current_signal: Optional[str] = None
    
    def add_to_context(self, text: str):
        self.context_hub.append(text)
        # Keep context lean (last 100 entries for demo)
        if len(self.context_hub) > 100:
            self.context_hub.pop(0)

class HubController:
    """
    The Central Brain of AutoHOP v2.2.
    Manages the Pointer Flow and the Vibe Director quality gate.
    Accepts an optional hop chain name; defaults to the full AutoHOP chain.
    """
    
    def __init__(self, chain_name: str = "all"):
        self.state = GlobalState()
        self.gate = NoiseGate()
        self.chain: HopChain = get_chain(chain_name)
        
        # Build role_to_or from the chain's route_map
        self.role_to_or: Dict[str, Optional[str]] = self.chain.route_map.copy()
        self.or_to_hub: Dict[str, Optional[str]] = {
            # New SWARM-DNA v3.0 roles
            "hermes": "hermes",
            "codex": "codex",
            "perplexity": "perplexity",
            "gemini": "gemini",
            "claude": "claude",
            "grok": "grok",
            "openclaw": "openclaw",
            "squirrel": "squirrel",
            # Legacy aliases (old → new)
            "grounding": "perplexity",
            "architect": "gemini",
            "polish": "claude",
            "critic": "grok",
            "gate": "openclaw",
            "chatgpt": "claude",
            "hermes_desktop": "hermes",
            "none": None,
            "null": None,
        }
        self.max_hops = 14

    def _normalize_next_hop(self, next_hop: Optional[str]) -> Optional[str]:
        """
        Keep model output inside the hub's routing vocabulary.
        OpenRouter prompts use role names; the hub loop uses agent names.
        """
        if next_hop is None:
            return None
        route = str(next_hop).strip().lower()
        normalized = self.or_to_hub.get(route)
        if normalized is None and route not in {"none", "null"}:
            logger.warning("Invalid next_hop from specialist: %r; terminating route.", next_hop)
        return normalized

    async def _specialist_call(self, agent: str, signal: str) -> HopResult:
        """
        Primary call path: tries real OpenRouter, falls back to mock.
        """
        if or_available():
            or_role = self.role_to_or.get(agent)
            if or_role:
                logger.info("ROUTE %s -> OpenRouter (%s)", agent, or_role)
                result = await call_specialist(or_role, signal)
                return HopResult(
                    model=result.get("model", agent),
                    findings=result.get("findings", ""),
                    next_hop=self._normalize_next_hop(result.get("next_hop")),
                    status=result.get("status", "CONTINUE"),
                    reasoning=result.get("reasoning", ""),
                    leverage_score=result.get("leverage_score", 5),
                )
            else:
                logger.info("ROUTE %s -> local (no OR role mapped)", agent)

        logger.info("ROUTE %s -> mock fallback (key=%s)", agent, "SET" if or_available() else "UNSET")
        return await self._mock_specialist_call(agent, signal)

    async def _mock_specialist_call(self, model: str, signal: str) -> HopResult:
        """
        Simulates a specialist agent return using the current hop chain's
        mock definitions. Falls back to a safe TERMINATE_KILL for unknown agents.
        """
        return await run_mock_hop(self.chain, model, signal)

    async def process_signal(self, raw_input: RawInput):
        """
        The Recursive HOP Loop
        """
        # 1. Noise Gate (The Entry)
        filter_res = await self.gate.filter(raw_input)
        if filter_res.is_noise:
            logger.warning(f"SIGNAL REJECTED: {filter_res.reasoning}")
            return None
        
        noise_context = get_noise_gate_context()
        if noise_context:
            self.state.add_to_context(noise_context)
            self.state.current_signal = (
                "AGENT CONTEXT: recent Kestrel noise-gate decisions follow.\n"
                f"{noise_context}\n\n"
                "CURRENT SIGNAL:\n"
                f"{filter_res.promoted_content}"
            )
        else:
            self.state.current_signal = filter_res.promoted_content
        self.state.add_to_context(filter_res.promoted_content)
        
        # 2. MiroFish Budget Gate
        mf = get_mirofish()
        mf_score = await mf.score(
            input_id=filter_res.input_id,
            content=self.state.current_signal or filter_res.promoted_content or "",
        )
        
        # Log to ArchiveSquirrel
        mf.log_to_squirrel(
            mf_score,
            (self.state.current_signal or filter_res.promoted_content or "")[:300],
        )
        
        if mf_score.recommended_model == "reject":
            logger.warning(
                "MIROFISH REJECTED: score=%d/10 cost=$%.4f remaining=$%.4f reason=%s",
                mf_score.conviction_score, mf_score.estimated_cost,
                mf_score.budget_remaining, mf_score.reasoning,
            )
            mf.record_rejection()
            return None
        
        logger.info(
            "MIROFISH APPROVED: score=%d/10 route=%s cost=$%.4f remaining=$%.4f",
            mf_score.conviction_score, mf_score.recommended_model,
            mf_score.estimated_cost, mf_score.budget_remaining,
        )
        
        # 3. The Pointer Flow
        current_hop = self.chain.first_agent
        
        hop_count = 0
        while current_hop:
            hop_count += 1
            if hop_count > self.max_hops:
                logger.error("MAX HOPS EXCEEDED (%s). Terminating route.", self.max_hops)
                break

            result = await self._specialist_call(current_hop, self.state.current_signal)
            self.state.hop_history.append(result)
            
            # Record MiroFish spend for this hop
            cost = PREMIUM_MODEL_COST if current_hop in ("gemini", "claude", "grok") else CHEAP_MODEL_COST
            if mf_score.recommended_model == "cheap":
                cost = CHEAP_MODEL_COST
            mf.record_spend(mf_score.recommended_model, cost)

            if result.status == "TERMINATE_KILL":
                logger.error("KILL SWITCH TRIGGERED.")
                break

            if result.status == "TERMINATE_SHIP":
                logger.info("SHIP IT: Signal converted to material gain.")
                break

            current_hop = result.next_hop

        return self.state.hop_history

async def main():
    """Run both available hop chains to demonstrate the routing."""
    import sys
    chains_to_test = sys.argv[1:] if len(sys.argv) > 1 else ["markets", "devflow"]

    for chain_name in chains_to_test:
        hub = HubController(chain_name=chain_name)
        signal = RawInput(
            content="Unexpectedly, liquidity pool X is draining. Immediate hedge required.",
            source="OnChainBot",
            timestamp=datetime.now(timezone.utc)
        )
        print(f"\n{'='*60}")
        print(f"Chain: {chain_name} ({hub.chain.description})")
        print(f"First agent: {hub.chain.first_agent}")
        print(f"{'='*60}")
        logger.info("Starting AutoHOP Flow (chain=%s)...", chain_name)
        history = await hub.process_signal(signal)
        if history:
            for i, hop in enumerate(history):
                print(f"  Hop {i}: {hop.model:18s} | score={hop.leverage_score} | "
                      f"next={hop.next_hop or 'END':18s} | {hop.status}")
        else:
            print("  (no hop history — signal was rejected)")

if __name__ == "__main__":
    asyncio.run(main())
