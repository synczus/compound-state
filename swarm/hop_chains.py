"""
AutoHOP Hop Chain definitions.
Each HopChain defines an ordered pipeline of agents, their roles,
and default pointer flow for mock/fallback mode.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass(slots=True)
class HopResult:
    """Local copy of HopResult to avoid circular import with hub.py."""
    model: str
    findings: str
    next_hop: Optional[str]
    status: str
    reasoning: str
    leverage_score: int


@dataclass(slots=True)
class HopChain:
    """A named pipeline of agents with their routing configuration."""

    name: str
    description: str
    first_agent: str
    agents: List[str]

    # For each agent, whether it routes through OpenRouter (True),
    # local execution (False), or a special handler (str command)
    route_map: Dict[str, Optional[str]]

    # Default mock flow: agent_name -> next_agent_name (or None for terminal)
    mock_flow: Dict[str, Optional[str]]

    # Per-agent mock response templates
    mock_findings: Dict[str, str] = field(default_factory=dict)
    mock_scores: Dict[str, int] = field(default_factory=dict)

    def get_mock_next(self, agent: str) -> Optional[str]:
        return self.mock_flow.get(agent)


# ---------------------------------------------------------------------------
# Markets chain: financial signal pipeline
# ---------------------------------------------------------------------------

MARKETS_CHAIN = HopChain(
    name="markets",
    description="Financial signal pipeline using the new agent lineup",
    first_agent="hermes",
    agents=["hermes", "codex", "perplexity", "gemini", "claude", "grok", "openclaw", "squirrel"],
    route_map={
        "hermes": "hermes",
        "codex": "codex",
        "perplexity": "perplexity",
        "gemini": "gemini",
        "claude": "claude",
        "grok": "grok",
        "openclaw": "openclaw",
        "squirrel": "squirrel",
    },
    mock_flow={
        "hermes": "codex",
        "codex": "perplexity",
        "perplexity": "gemini",
        "gemini": "claude",
        "claude": "grok",
        "grok": "openclaw",
        "openclaw": None,
        "squirrel": None,
    },
    mock_findings={
        "hermes": "HERMES: Systems audit complete. Hidden constraints exposed.",
        "codex": "CODEX: Execution plan built. Failure modes identified.",
        "perplexity": "PERPLEXITY: Facts verified. Assumptions grounded.",
        "gemini": "GEMINI: Architecture synthesized. Structure coherent.",
        "claude": "CLAUDE: Deliverable refined. Clarity achieved.",
        "grok": "GROK: Adversarial review complete. Edge cases attacked.",
        "openclaw": "OPENCLAW: Gate approved. Pipeline output sufficient.",
        "squirrel": "SQUIRREL: Durable signal archived. Chain complete.",
    },
    mock_scores={
        "hermes": 9,
        "codex": 7,
        "perplexity": 8,
        "gemini": 9,
        "claude": 9,
        "grok": 9,
        "openclaw": 10,
        "squirrel": 10,
    },
)

# ---------------------------------------------------------------------------
# Dev flow chain
# ---------------------------------------------------------------------------

DEVFLOW_CHAIN = HopChain(
    name="devflow",
    description="Development pipeline: Hermes audits, Codex executes, Perplexity verifies, Gemini architects, Claude polishes, Grok attacks, OpenClaw gates",
    first_agent="hermes",
    agents=["hermes", "codex", "perplexity", "gemini", "claude", "grok", "openclaw", "squirrel"],
    route_map={
        "hermes": "hermes",
        "codex": "codex",
        "perplexity": "perplexity",
        "gemini": "gemini",
        "claude": "claude",
        "grok": "grok",
        "openclaw": "openclaw",
        "squirrel": "squirrel",
    },
    mock_flow={
        "hermes": "codex",
        "codex": "perplexity",
        "perplexity": "gemini",
        "gemini": "claude",
        "claude": "grok",
        "grok": "openclaw",
        "openclaw": None,
        "squirrel": None,
    },
    mock_findings={
        "hermes": "HERMES: Systems audit complete. Hidden constraints exposed.",
        "codex": "CODEX: Initial decomposition complete. Real goal and failure modes framed.",
        "perplexity": "PERPLEXITY: Facts and assumptions checked.",
        "gemini": "GEMINI: Structure is coherent and executable.",
        "claude": "CLAUDE: Deliverable compressed and formatted.",
        "grok": "GROK: Edge cases attacked. No major structural failure found.",
        "openclaw": "OPENCLAW: Gate approved. Output sufficient.",
        "squirrel": "SQUIRREL: Durable signal archived. Chain complete.",
    },
    mock_scores={
        "hermes": 8,
        "codex": 7,
        "perplexity": 8,
        "gemini": 9,
        "claude": 9,
        "grok": 9,
        "openclaw": 10,
        "squirrel": 10,
    },
)

# ---------------------------------------------------------------------------
# All-OpenRouter chain
# ---------------------------------------------------------------------------

ALL_OPENROUTER_CHAIN = HopChain(
    name="all",
    description="Full AutoHOP pipeline: Hermes -> Codex -> Perplexity -> Gemini -> Claude -> Grok -> OpenClaw, with OpenClaw -> Squirrel only when archiving is needed",
    first_agent="hermes",
    agents=["hermes", "codex", "perplexity", "gemini", "claude", "grok", "openclaw", "squirrel"],
    route_map={
        "hermes": "hermes",
        "codex": "codex",
        "perplexity": "perplexity",
        "gemini": "gemini",
        "claude": "claude",
        "grok": "grok",
        "openclaw": "openclaw",
        "squirrel": "squirrel",
    },
    mock_flow={
        "hermes": "codex",
        "codex": "perplexity",
        "perplexity": "gemini",
        "gemini": "claude",
        "claude": "grok",
        "grok": "openclaw",
        "openclaw": None,
        "squirrel": None,
    },
    mock_findings={
        "hermes": "HERMES: Systems audit complete. Hidden constraints exposed.",
        "codex": "CODEX: Initial decomposition complete. Real goal and failure modes framed.",
        "perplexity": "PERPLEXITY: Facts and assumptions checked.",
        "gemini": "GEMINI: Structure is coherent and executable.",
        "claude": "CLAUDE: Deliverable compressed and formatted.",
        "grok": "GROK: Edge cases attacked. No major structural failure found.",
        "openclaw": "OPENCLAW: Gate approved. Output sufficient.",
        "squirrel": "SQUIRREL: Durable signal archived. Chain complete.",
    },
    mock_scores={
        "hermes": 8,
        "codex": 7,
        "perplexity": 8,
        "gemini": 9,
        "claude": 9,
        "grok": 9,
        "openclaw": 10,
        "squirrel": 10,
    },
)


# ---------------------------------------------------------------------------
# Archive chain: squirrel-based document archival pipeline
# ---------------------------------------------------------------------------

ARCHIVE_CHAIN = HopChain(
    name="archive",
    description="Archive path: Hermes -> Codex -> Perplexity -> Gemini -> Claude -> Grok -> OpenClaw -> Squirrel",
    first_agent="hermes",
    agents=["hermes", "codex", "perplexity", "gemini", "claude", "grok", "openclaw", "squirrel"],
    route_map={
        "hermes": "hermes",
        "codex": "codex",
        "perplexity": "perplexity",
        "gemini": "gemini",
        "claude": "claude",
        "grok": "grok",
        "openclaw": "openclaw",
        "squirrel": "squirrel",
    },
    mock_flow={
        "hermes": "codex",
        "codex": "perplexity",
        "perplexity": "gemini",
        "gemini": "claude",
        "claude": "grok",
        "grok": "openclaw",
        "openclaw": "squirrel",
        "squirrel": None,
    },
    mock_findings={
        "hermes": "HERMES: Systems audit confirms archival value.",
        "codex": "CODEX: Archive candidate decomposed and normalized.",
        "perplexity": "PERPLEXITY: Source facts and evidence checked.",
        "gemini": "GEMINI: Metadata structure selected.",
        "claude": "CLAUDE: Archive record compressed and formatted.",
        "grok": "GROK: Archive risks and duplicate concerns checked.",
        "openclaw": "OPENCLAW: Archival needed. Routing to ArchiveSquirrel.",
        "squirrel": "SQUIRREL: Durable signal archived. Chain complete.",
    },
    mock_scores={
        "hermes": 8,
        "codex": 8,
        "perplexity": 8,
        "gemini": 9,
        "claude": 9,
        "grok": 9,
        "openclaw": 10,
        "squirrel": 10,
    },
)


# Registry of all available hop chains
CHAINS: Dict[str, HopChain] = {
    "markets": MARKETS_CHAIN,
    "devflow": DEVFLOW_CHAIN,
    "all": ALL_OPENROUTER_CHAIN,
    "archive": ARCHIVE_CHAIN,
}


def get_chain(name: str = "markets") -> HopChain:
    """Get a hop chain by name. Defaults to 'markets'."""
    chain = CHAINS.get(name)
    if chain is None:
        raise ValueError(f"Unknown hop chain: {name}. Available: {list(CHAINS.keys())}")
    return chain


async def run_mock_hop(
    chain: HopChain,
    agent: str,
    signal: str,
) -> HopResult:
    """Generate a mock HopResult for an agent in a given chain."""
    import asyncio
    await asyncio.sleep(0.1)

    findings_template = chain.mock_findings.get(
        agent,
        f"{agent.upper()}: Processed {signal[:40]}..."
    )
    findings = findings_template.replace("{signal}", signal)

    next_agent = chain.mock_flow.get(agent)
    score = chain.mock_scores.get(agent, 7)

    return HopResult(
        model=agent,
        findings=findings,
        next_hop=next_agent,
        status="TERMINATE_SHIP" if next_agent is None else "CONTINUE",
        reasoning=f"Mock: {agent} completed its hop.",
        leverage_score=score,
    )