# Normalized Tick Schema — Canonical Format

All venues (IBKR, Bybit, Coinbase) map to this schema. One format for backtesting, signals, execution.

## Canonical Tick
```json
{
  "venue": "ibkr|bybit|coinbase",
  "symbol": "AAPL|BTC-USD",
  "ts": "2026-06-07T22:00:00Z",
  "type": "trade|quote|book",
  "price": 150.25,
  "size": 100,
  "side": "buy|sell",
  "volume_24h": 12500000
}
```

## IBKR Translation
- `price` → market price
- `size` → contract multiplier × qty
- `volume_24h` → from reqHistoricalData

## Crypto Translation
- `price` → last price
- `size` → base currency amount
- `volume_24h` → exchange-reported 24h vol

## Schema Registry
`/kestrel/engines/ibkr/schemas/canonical_v1.json`