# Skill: pipeline-signal

Monitor and verify the Kestrel signal pipeline. Check noise gate decisions, promote/demote ratios, and flag anomalies.

## Requirements

- Read access to `/home/synczus/kestrel/memory-bank/knowledge/noise-gate-context.md`
- Read access to `/home/synczus/kestrel/memory-bank/knowledge/noise-gate-events.jsonl`
- Read access to `/home/synczus/kestrel/agent-pulses/`

## Implementation

1. Read the noise gate context file
2. Extract the PROMOTE/PURGE ratio
3. Check the events JSONL for the last 10 decisions
4. Compare with the previous reading (if one exists in memory)
5. Post a health check to the group if the ratio drops below 1:3

## Anomaly Flags

- PURGE rate > 75% in last 10 signals → likely gate too aggressive
- PROMOTE rate > 90% → gate too permissive
- No new events in >1 hour → pipeline stalled
- Empty context file → HUB_INTAKE refresh may be broken

## Cron Integration

Can run as a cron check every 15 minutes. Output only when anomalies are found (silent on healthy).

## Verification

- Run manually: read the noise gate context and check the ratio
- Confirm the ratio is reasonable for normal operation