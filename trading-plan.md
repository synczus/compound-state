# Trading Integration — Compound-to-Exchange API Plan
## Stage 0 Intake — Coinbase Advanced Trade

### The Loop
```
Striker (data) → signal detected → Compound evaluates → API order placed → Striker watches result → HLM banked
```

### What Exists
- Striker: Coinbase WS ticker connected, subscribed to BTC-USD/ETH-USD/SOL-USD
- Core config: env-based, extensible with API key/secret fields
- Telegram alerts: signals/telegram.py (httpx, untested)

### What's Needed for Trading
1. Coinbase API credentials (API key + secret with trade permission) — needs user setup
2. Order execution module — add to core/ or signals/
3. Signal → order mapping (threshold, position size, stop loss)
4. Paper mode toggle for testing without real money
5. Trade journal DB table

### Cost Reality
- $50 account → ~$0.30-0.50 per round trip on Advanced Trade
- 3-month sandbox: realistic to lose $15-25 in fees, gain signal experience
- Position sizing: $10-20 per trade to minimize fee impact

### Recommended Path
1. User creates Coinbase API key with trade permission
2. Build paper trading mode first (validate against Striker signals without real money)
3. Live with $50 after paper mode proves the loop
4. Let run 3 months, review signal quality vs. fees vs. P&L