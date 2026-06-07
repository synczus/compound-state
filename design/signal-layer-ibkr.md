# IBKR-native Signal Layer — Design Brief

**Status:** Proposed (from Grok inversion hop-2026-06-07-striker-failure-inversion-ibkr)
**Owner:** Nemoclaw (build) → Kairos (audit)
**Replaces:** Striker threshold detector (deprecated)

## Core Requirements
1. **IBKR as primary data source** — WebSocket/API for crypto (BTC, ETH, SOL)
2. **Clean abstraction** — SignalSource → SignalProcessor → SignalBus so downstream doesn't know source
3. **Multiple detection methods** — not just raw threshold. Include volume profile, order flow, time-of-day
4. **Minimal state** — stateless where possible so no heavy supervision needed
5. **Single failure domain** — no reconciliation between two data sources

## Architecture (proposed)
- `SignalSource(provider)` — wraps IBKR WS, normalizes to common tick format
- `SignalDetector(method)` — applies one detection method (threshold, volume, etc.)
- `SignalBus` — emits signals downstream, abstracted from source
- `SignalSupervisor` — lightweight health check (is the WS alive? is IBKR connected?)

## What's Different from Striker
- IBKR handles auth/reconnect natively (no custom WS wrangling)
- Detection methods are pluggable (add new ones without rewriting pipeline)
- Supervision is lightweight because IBKR connection is stable
- No Coinbase dependency at all

## Open Questions (for Kairos audit)
1. IBKR crypto data latency vs Coinbase direct? Is it fast enough for HFT?
2. Should we keep Coinbase WS as a fallback on the SignalBus level?
3. Symbol mapping: IBKR uses different symbols for crypto (they go through Paxos/Zero Hash)
