# Decision: Deprecate Striker as Signal Engine

**Date:** 2026-06-07
**Source:** Grok inversion hop-2026-06-07-striker-failure-inversion-ibkr
**Status:** Accepted

## Decision
Striker is a deprecated prototype. It will NOT be evolved or hardened. 
Replace it with a clean IBKR-native Signal Layer.

## Rationale
- Striker is a narrow Coinbase WebSocket threshold detector (>0.5%)
- Kairos + WolfWatch exist to compensate for Striker's fragility
- IBKR offers solid crypto data via WebSocket/API with stable connections
- Porting Striker to IBKR recreates the same failure modes
- Better to design a proper abstraction layer than keep adding supervision

## What Happens to Current Striker
- Striker coinbase WS connection can keep running as a data source (not a decision engine)
- Striker signal writing to DB/event-bus stops once Signal Layer exists
- Striker health monitoring in Kairos stops when Signal Layer supervises itself

## Owner
Nemoclaw: prototype Signal Layer design
Kairos: audit design + ops implications
