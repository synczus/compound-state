# Nemoclaw Cost Pulse — 2026-06-10T18:25Z

**Source:** cron (cost-tracker-every-6h)

## Findings
- ❌ **cost-tracker.sh missing** — script at expected path doesn't exist. heartbeat written with warning status.
- 💰 **OpenRouter: $6.46 remaining** ($251.54 used of $258 total) — critical. At ~$6/day burn, ~24h of runway left.
- 🟡 **AgentMemory REST API down** (circuit closed) — inter-agent signals broken.
- ⚪ **Striker:** 0 signals this session, connected ~48h. Total lifetime: 138,861.
- ⚪ **Wolfwatch:** inactive (since last briefing).

## Action
- Pulse written to track missing script and low budget.
