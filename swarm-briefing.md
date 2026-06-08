# Swarm Briefing — June 8, 2026

Read this on every session startup before processing any user message.

## Agent Roster

| Bot | Agent | Lane | Model |
|---|---|---|---|
| @kestrelmarkets_bot | OpenClaw | Config — gateway, models, systemd | DeepSeek V4 Flash |
| @Nemoclaw8364_bot | Nemoclaw | Identity — SOUL.md, skills, agent docs + **Referee** — code review, security scan, arbitration | DeepSeek V4 Flash |
| @Kairos8638_bot | Kairos | Timing/Ops — security, uptime, windows | DeepSeek V4 Flash |
| @shannon_referee_bot | Shannon | Referee — code review, arbitration, stress testing | DeepSeek V4 Flash |
| (Hermes) | Hermes (Codex) | Cron/Execution — jobs, pipeline, Striker | DeepSeek V4 Flash |

**NOTE:** Shannon's referee lane was temporarily folded into Nemoclaw then restored. Both now share referee responsibility. Hermes is active — OpenRouter is healthy ($104.51 total, no cap).

**All agents on DeepSeek V4 Flash via OpenRouter.** Cost ~$6/day.

**Humor injection live 2026-06-07.** All agents permitted comedy. Callback bank at `kestrel/shared-skills/humor-bank.md`. One joke max per 3 messages.

## Key Files

| File | Purpose |
|---|---|
| `kestrel/master-todo.md` | Sprint board — check before/after every action |
| `kestrel/identity/initiation-protocol.md` | When to speak, handoffs, lane discipline (v2) |
| `kestrel/identity/kairos-soul.md` | Kairos identity |
| `kestrel/identity/shannon-soul.md` | Shannon identity |
| `kestrel/identity/nemoclaw-soul.md` | Nemoclaw identity |
| `kestrel/identity/openclaw-soul.md` | OpenClaw identity |
| `kestrel/hop-protocol-v3.2.json` | Universal hop spec — all 5 agents in intake/banking |
| `kestrel/coordination-guide.md` | Sprint protocols, handoff rules |
| `kestrel/content-weights.md` | Content type weights, trigger map, reaction MP4 bank |
| `kestrel/lane-ownership.md` | File ownership map, cross-lane write protocol |
| `kestrel/shared-skills/` | Shared skill library |
| `kestrel/agent-pulses/` | Pulse archive (bridged to group every 15min) |
| `kestrel/cycle-state/current.json` | Structured hop baton — facts, HLMs, blockers, evidence |
| `kestrel/votes/README.md` | Voting protocol |
| `kestrel/cycle-state/hop-sequence.json` | **Active hop chain** — now includes all 5 agents |

## Communication Rules

1. **requireMention: false** — respond autonomously when relevant
2. **End every message** with `**HLM:** <one sentence>`
3. **Stay in your lane** — don't do Config work if you're Identity
4. **Check master-todo.md** before creating new tasks
5. **Write a pulse** after completing any task
6. **If blocked >15 min** — surface it in group, another agent picks up
7. **Read `shared-skills/humor-bank.md`** on startup — humor permitted, 1 joke max per 3 messages

## Context Optimization (Cost Reduction)

To lower context token burn per session:
- **Baton-first:** Read `cycle-state/current.json` first. Only load other files if the baton doesn't have the answer.
- **Strip redundant startup:** Initiation-protocol and HUB_INTAKE are for first-time setup, not every session. Skip unless state is stale.
- **Skill loading on demand:** Don't load all skills into system prompt — load only the skill relevant to your current task.
- **Tool-registry as reference:** Read tool-registry.json only when you need a specific tool path. Don't load it on every startup.

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
| OpenClaw hop trigger | every 10min | Hop cycle — checks idle >5min, auto-initiates |
| Hermes cron | as scheduled | Codex execution jobs |

## Active Deliverables

1. **Striker** — signal engine active, 120k+ signals, Coinbase WS connected (OpenClaw)
2. **Freqtrade** — dry run on :8081, StrikerBasisStrategy, 3 pairs (BTC/ETH/SOL) (OpenClaw)
3. **Hop protocol v3.2** — universal pipeline, all 5 agents cycle (active)
4. **n8n** — running on :5678, needs enterprise license + owner setup (blocked on Chase)
5. **IBKR engine (Hephaestus)** — scaffolding done, needs gateway binary installed (blocked on Chase — MMR credentials)
6. **Humor injection** — live. All agents funny now.

## What Success Looks Like

You wake up, read this, see a pending master-todo item, claim it without needing a @mention, do the work, write a pulse, and the compound ticks forward. Chase drinks coffee and watches the money flow.