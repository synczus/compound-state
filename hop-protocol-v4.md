# Hop Protocol v4 — Condensed Reference

**Chain:** Kairos scouts → Nemoclaw builds → Kairos audits → Hermes deploys → Done

## Handoff Packet (every hop must include)

1. What was built
2. Assumptions made
3. Unknowns that matter
4. Evidence / sources
5. Inversion — what could make this wrong
6. Blockers
7. Spawned sub-agents

## Rules

- Every hop inverts the previous (no pass-throughs)
- Sub-agent spawning is standard, not special
- Don't wait for tags — read and respond
- Handoff includes assumptions or it's incomplete
- Stuck = state blocker and pass back, don't stall

## Agent Lanes

| Kairos | Nemoclaw | Hermes |
|---|---|---|
| Scouts findings | Builds code/docs | Deploys services |
| Spawns deep-dives | Spawns parallel builds | Spawns verifiers |

## Cost

- All hops on DeepSeek V4 Flash (~$6/day total)
- Sub-agents same model, same key
- No thought-drop waste
- Productive burn only; silence is free