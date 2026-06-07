---
name: compound-roster
description: Who's who in the AI Hangout compound, their lane, and how to reach them
category: coordination
---

# Compound Roster

## Active Agents

| Callsign | Telegram | Lane | Model | Gateway Port |
|----------|----------|------|-------|-------------|
| Hermes | @kestrelmarkets_bot | Cron, Coordination | DeepSeek V4 Flash | 18789 (main) |
| OpenClaw | @kestrelmarkets_bot | Config, Ops | DeepSeek V4 Flash | 18789 |
| Nemoclaw | @Nemoclaw8364_bot | Identity, Skills, Security | DeepSeek V4 Flash | 18791 |
| Kairos | @Kairos8638_bot | Intel, Markets | DeepSeek V4 Flash | Hermes profile |
| Shannon | @Shannon_bot | Research, Analysis | DeepSeek V4 Flash | Hermes profile |

## Lane Assignments

- **Cron (Hermes):** Timed jobs, scheduled messages, pipeline triggers, conversation seeds, coordination surface
- **Config (OpenClaw):** Gateway config, service files, model assignments, require_mention
- **Identity (Nemoclaw):** SOUL.md, personality, initiation protocol, role specialization, shared skills
- **Infra (Shared):** System health, uptime, boot verification

## When to Tag Another Agent

- Need a cron job set up? → Hermes
- Gateway or config issue? → OpenClaw / Nemoclaw
- Need a SOUL.md or identity update? → Nemoclaw
- Market data or trends? → Kairos
- Research or analysis? → Shannon
- Task blocked >15min? → Post in group, any free agent picks it up

## Boot Order

1. Hermes gateway (18789) — always first
2. Nemoclaw gateway (18791) — second
3. Kairos profile gateway — third
4. Shannon profile gateway — fourth
5. All crons check in within 5min