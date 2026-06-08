# Project Hephaestus — IBKR Engine

## Status: Scaffolding
Striker stays running in shadow mode until Hephaestus proves >50% fewer false signals.

## Directory Layout
```
engines/ibkr/
├── README.md             ← This file
├── gateway.sh            ← systemd unit definition (infrastructure, not agent)
├── tick_schema.md        ← Normalized canonical schema
├── event_bus.py          ← Structured event publisher
└── verify.sh             ← Shadow mode comparison script
```

## First 3 Build Steps
1. **gateway.sh** — systemd unit for IBKR TWS/IB Gateway auto-restart
2. **tick_schema.md** — canonical tick format (IBKR + crypto normalized)
3. **event_bus.py** — structured publisher, WolfWatch consumer

## Design Principles
- IBKR gateway = infrastructure, not agent
- Normalized schema = one format for backtesting, signals, execution
- Stateless event bus = no single process owns truth
- Striker shadows until proven inferior