"""Test the archive hop chain."""
import asyncio, sys
sys.path.insert(0, '/home/synczus/kestrel')
from swarm.hub import HubController
from swarm.noise_gate import RawInput
from datetime import datetime, timezone

async def main():
    hub = HubController(chain_name='archive')
    print(f'Chain: {hub.chain.name}')
    print(f'First: {hub.chain.first_agent}')
    print(f'Agents: {hub.chain.agents}')
    print()

    signal = RawInput(
        content='Contrary to reports, confirmed by 2 sources: document needs archival.',
        source='Test',
        timestamp=datetime.now(timezone.utc),
    )
    history = await hub.process_signal(signal)
    if history:
        for i, h in enumerate(history):
            print(f'  Hop {i}: {h.model:12s} score={h.leverage_score} next={h.next_hop or "END":12s} {h.status}')

asyncio.run(main())