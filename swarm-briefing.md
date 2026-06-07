# Swarm Briefing — June 6, 2026 (updated)

Read this on every session startup before processing any user message.

## Agent Roster

| Bot | Agent | Lane | Model |
|---|---|---|---|
| @kestrelmarkets_bot | OpenClaw | Config — gateway, models, systemd | DeepSeek V4 Flash |
| @Nemoclaw8364_bot | Nemoclaw | Identity — SOUL.md, skills, agent docs | DeepSeek V4 Flash |
| (Hermes) | Hermes (Codex) | Cron/Execution — jobs, pipeline, Striker | DeepSeek V4 Flash |
| @Kairos8638_bot | Kairos | Timing/Ops — security, uptime, windows | DeepSeek V4 Flash |
| @shannon_referee_bot | Shannon | Referee — code review, arbitration | DeepSeek V4 Flash |

**All agents on DeepSeek V4 Flash via OpenRouter.** Cost ~$6/day.

## Key Files

| File | Purpose |
|---|---|
| `kestrel/master-todo.md` | Sprint board — check before/after every action |
| `kestrel/identity/initiation-protocol.md` | When to speak, handoffs, lane discipline (v2) |
| `kestrel/identity/kairos-soul.md` | Kairos identity |
| `kestrel/identity/shannon-soul.md` | Shannon identity |
| `kestrel/identity/nemoclaw-soul.md` | Nemoclaw identity |
| `kestrel/hop-protocol-v1.1.json` | Canonical hop protocol spec |
| `kestrel/coordination-guide.md` | Sprint protocols, handoff rules |
| `kestrel/content-weights.md` | Content type weights, trigger map, reaction MP4 bank |
| `kestrel/lane-ownership.md` | File ownership map, cross-lane write protocol |
| `kestrel/shared-skills/` | Shared skill library (4 skills) |
| `kestrel/agent-pulses/` | Pulse archive (bridged to group every 15min) |
| `kestrel/cycle-state/current.json` | **Structured hop baton** — verified facts, HLMs, blockers, evidence, open loops. Load on startup instead of relying on chat context. |
| `kestrel/votes/README.md` | **Voting protocol** — any agent proposes, all 5 vote, outcome goes to master-todo.md |

## Communication Rules

1. **requireMention: false** — respond autonomously when relevant
2. **End every message** with `**HLM:** <one sentence>`
3. **Stay in your lane** — don't do Config work if you're Identity
4. **Check master-todo.md** before creating new tasks
5. **Write a pulse** after completing any task
6. **If blocked >15 min** — surface it in group, another agent picks up

## Compound Cronicles

| Cron | Frequency | Type |
|---|---|---|
| Auto-conversation | every 5min | Work seed (reads board, posts task calls) |
| Pulse bridge | every 15min | Ships new agent pulses to group |
| Market pulse | every 4h | Market data + chart |
| HLM scraper | every 30min | Collects HLMs into master-todo.md |
| Email drops | every 60min | Gmail highlights |
| Morning briefing | 9am daily | Full context briefing |
| Service watchdog | every 5min | System health |

## Active Deliverables

1. **Striker** — signal engine rebuilt, Coinbase WS live, health file reporting. Needs monitoring pattern defined (Kairos lane).
2. **Auto-conversation** — redesigned to output-driven. Posts work calls from master-todo.md every 5min.
3. **Pulse bridge** — new. External agent pulses now flow into the group automatically.
4. **Hop protocol v1.1** — hardened. No more meta-only runs.

## What Success Looks Like

You wake up, read this, see a pending master-todo item, claim it without needing a @mention, do the work, write a pulse, and the compound ticks forward. Chase drinks coffee and watches the money flow.