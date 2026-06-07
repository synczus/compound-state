# Self-Correcting Compound State Design

**Status:** Design Proposal | **Owner:** Hermes | **Priority:** P2

## Problem

compound-state.json shows stale information (e.g. Striker "offline" for 3 hours
even though the alert pipeline works). Awareness refreshes and agent context
carry yesterday's status into today's decisions. No mechanism to correct
stale state without a human noticing and asking.

## Design

### Live State Probe

Add a cron that runs every 5 minutes (silent) to:
1. Check systemctl status for each agent's service
2. Verify WolfWatch receiver responds on :18790
3. Check Striker health file is fresh (<120s old)
4. Check each cron heartbeat is fresh (<30min old)
5. Write verified state to cycle-state/current.json

### State Diff & Correction

After the probe, compare with compound-state.json:
- If probe says "online" but state says "offline" → auto-correct
- Append a correction note: `"corrected_at": "2026-06-07T06:00:00Z"`
- Post a 1-line event to event-bus.md: "State auto-corrected: Striker online"

### Agent Context Injection

Each agent reads cycle-state/current.json at session start:
- Gets verified state, not stale compound-state.json
- If the probe hasn't run in >10min → agents know the probe itself is stale

### Files to Touch

- `/home/synczus/kestrel/cycle-state/current.json` — live verified state
- `/home/synczus/kestrel/scripts/state-probe.sh` — the probe script
- `/home/synczus/kestrel/event-bus.md` — correction log
- symlink: `cycle-state/current.json` → `compound-state.json` (one source of truth)

## Success Criteria

- compound-state.json automatically corrects within 5 minutes of any state change
- Agents never read stale status
- Probe failure is itself monitored (see meta-monitoring design)