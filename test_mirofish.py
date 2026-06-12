#!/usr/bin/env python3
"""Test MiroFish signal scoring and routing."""
import asyncio
import json
import sys
sys.path.insert(0, '/home/synczus/kestrel')
from swarm.mirofish import get_mirofish

async def test():
    mf = get_mirofish()
    mf.reset_daily()
    
    signals = [
        ('Breaking: ETH liquidity drain 40% on Uniswap v3. Hedge now.', 'liquidity drain'),
        ('maybe consider looking at the market some time', 'vague fluff'),
        ('Confirmed: BTC $60K support broken. Verified across 4 exchanges. Sell pressure.', 'high conviction'),
        ('lol moon soon', 'shitpost'),
        ('Alert: INJ breakout above $9.50 resistance. Volume surge 300%. Entry signal.', 'crypto setup'),
    ]
    
    for content, label in signals:
        score = await mf.score(f'test_{label}', content)
        icon = '+' if score.recommended_model != 'reject' else '-'
        print(f'{icon} [{label:16s}] conviction={score.conviction_score}/10 route={score.recommended_model:7s} ${score.estimated_cost:.4f} | {score.reasoning[:60]}')
        if score.recommended_model != 'reject':
            mf.record_spend(score.recommended_model, score.estimated_cost)
        else:
            mf.record_rejection()
    
    print(f'\nLedger: {json.dumps(mf.status(), indent=2)}')

asyncio.run(test())