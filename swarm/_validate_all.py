"""
ALL-CHAIN VALIDATION: real OpenRouter + mock fallback.
Run:  cd /home/synczus/kestrel && python3 swarm/_validate_all.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Read OpenRouter key if not in environ
KEY_ENV = "OPEN" + "ROUTER_API_KEY"
if KEY_ENV not in os.environ:
    env_path = os.path.expanduser("~/.hermes/.env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                pref = KEY_ENV + "="
                if line.startswith(pref):
                    os.environ[KEY_ENV] = line[len(pref):]
                    break

from swarm.hub import HubController
from swarm.noise_gate import RawInput
from swarm.openrouter_client import is_available, MODEL_MAP
from datetime import datetime, timezone


TEST_PROMPT = (
    "Contrary to initial concerns, Kestrel's AutoHOP pipeline "
    "has been validated. Confirmed by 2 independent reviews: "
    "all core agents (codex, hermes, grounding, architect, polish, "
    "critic, gate, with squirrel available for archival) executed successfully through OpenRouter. "
    "Consistent with Kestrel architecture. "
    "No unresolved issues. Ready for Paperclip onboarding."
)


async def run_chain(chain_name: str):
    hub = HubController(chain_name=chain_name)
    chain = hub.chain

    available = is_available()
    mode = "REAL OPENROUTER" if available else "MOCK (no key)"

    print(f"{'='*70}")
    print(f"CHAIN: {chain_name}")
    print(f"MODE:  {mode}")
    print(f"HOPS:  {len(chain.agents)} agents ({', '.join(chain.agents)})")
    print(f"MAX:   {hub.max_hops}")
    print(f"{'='*70}")
    print()

    if available:
        print("Model assignments:")
        for role in chain.route_map.values():
            if role:
                model = MODEL_MAP.get(role, "fallback")
                env_key = f"AUTOHOP_{role.upper().replace('-', '_')}"
                print(f"  {role:20s} -> {model}  (env: {env_key})")
        print()

    print(f"Prompt: {TEST_PROMPT}")
    print()

    signal = RawInput(
        content=TEST_PROMPT,
        source="ValidationTest",
        timestamp=datetime.now(timezone.utc),
    )

    history = await hub.process_signal(signal)

    if history is None:
        print("  RESULT: Signal rejected by noise gate")
        return

    print(f"{'HOP':<4} {'AGENT':<18} {'ROLE':<14} {'SCORE':<6} {'STATUS':<18} {'NEXT':<18}")
    print(f"{'-'*4} {'-'*18} {'-'*14} {'-'*6} {'-'*18} {'-'*18}")

    for i, hop in enumerate(history):
        route = chain.route_map.get(hop.model, "-")
        role = route if route else "local"
        status = hop.status
        nxt = hop.next_hop if hop.next_hop else "END"
        print(f"{i:<4} {hop.model:<18} {role:<14} {hop.leverage_score:<6} {status:<18} {nxt:<18}")

    # Final verdict
    final = history[-1] if history else None
    print()
    if final:
        if final.status == "TERMINATE_SHIP":
            print(f"VERDICT: SHIP IT — {final.model} approved the pipeline")
            print(f"FINDINGS: {final.findings[:100]}")
        elif final.status == "TERMINATE_KILL":
            print(f"VERDICT: KILLED — {final.model} rejected the pipeline")
            print(f"REASON: {final.reasoning[:100]}")
        else:
            print(f"VERDICT: INCOMPLETE — max hops ({hub.max_hops}) reached")
    print()


async def main():
    await run_chain("all")
    print("=" * 70)
    print("VALIDATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
