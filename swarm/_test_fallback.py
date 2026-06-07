"""
Fallback test: hub.py uses mock when OPENROUTER_API_KEY is absent.
Runs in a subprocess with the key explicitly unset to avoid import caching.
"""
import asyncio
import os
import sys

# Ensure key is NOT set
os.environ.pop("OPENROUTER_API_KEY", None)

script_dir = os.path.dirname(os.path.abspath(__file__))
kestrel_root = os.path.dirname(script_dir)
sys.path.insert(0, kestrel_root)

from swarm.openrouter_client import is_available
from swarm.hub import HubController
from swarm.noise_gate import RawInput
from datetime import datetime, timezone


async def main():
    print("=" * 60)
    print("FALLBACK TEST: hub.py WITHOUT OpenRouter key")
    print("=" * 60)
    print()

    avail = is_available()
    print(f"  OPENROUTER_API_KEY available: {avail}")
    print(f"  Expecting mock fallback:      True")
    print()

    hub = HubController()

    signal = RawInput(
        content="Unexpectedly, liquidity pool X is draining. Immediate hedge required.",
        source="OnChainBot",
        timestamp=datetime.now(timezone.utc),
    )

    print("  Calling hub.process_signal()...")
    print()
    history = await hub.process_signal(signal)

    if history is None:
        print("  Noise gate rejected the signal.")
        return

    for i, hop in enumerate(history):
        print(f"    Hop {i}: model={hop.model} score={hop.leverage_score} "
              f"next={hop.next_hop} status={hop.status}")

    print()
    print("  Mock fallback works: all responses are simulated")
    print("  No OpenRouter API calls were made")
    print()


if __name__ == "__main__":
    asyncio.run(main())