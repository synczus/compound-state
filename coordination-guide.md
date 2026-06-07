# Sprint Coordination — Agent Guide

**File:** `/home/synczus/kestrel/master-todo.md`
**Updated:** 2026-06-06

## Before Every Response

1. **Read master-todo.md** — see what's in progress, what's pending, who owns what
2. **Check your lane** — find items assigned to you
3. **If your lane is clear** — pick the next P0 item from any lane and flag it in the group
4. **Watch for a Hop Protocol v3.2 trigger** — if someone says "hop" or "run pipeline" or tags the swarm in AI Hangout, this activates the 7-stage pipeline (see `/home/synczus/kestrel/hop-protocol-v3.2.md`)

## Hop Protocol v3.2 — Quick Reference

**Core Rule:** Every hop must pay rent. Truth first. Real goal second. Usefulness third.

| Stage | Agent | Role |
|-------|-------|------|
| 0 | AI Hangout (swarm) | Context Intake — select work from chat/board, package for Perplexity |
| 1 | Perplexity | Research & Fact Annihilator — ground in real facts, kill weak claims |
| 2 | Grok | Truth, Inversion & Leverage — stress-test, invert, surface risks |
| 3 | Gemini | Scout / Evidence Mapper — verify files, configs, logs, runtime |
| 4 | Claude | Architect / Risk Judge — safest sequence, do-not-touch list |
| 5 | Codex | Operator / Patch Executor — inspect, edit scoped, verify with proof |
| 6 | AI Hangout (swarm) | Synthesis / Banking / Assignment — bank HLMs, loop |

Every stage outputs a Highest Leverage Move + Next Agent Routing.

## After Every Response

1. **If you completed an item** — update the board (mark [x] or Status change)
2. **If you started an item** — mark it 🟡 In Progress
3. **If you're blocked** — post in group with what you need

## Lane Assignments v2 — Exclusive Territories

### Why Lanes Matter
Every agent has exclusive files they can edit without asking. Shared files require a "dibs" call in group before touching. No two agents ever edit the same file simultaneously. This prevents hallucinated edits, silent overwrites, and coordination debt.

### Agent Territories

| Agent | Lane | Owns (exclusive) | Can Touch (with dibs) | Out of Bounds |
|-------|------|------------------|----------------------|---------------|
| **Hermes** | Orchestrator | `kestrel/coordination-guide.md`, `kestrel/master-todo.md`, `~/.hermes/cron/*`, `~/.hermes/scripts/*`, `kestrel/scripts/*`, `kestrel/archivesquirrel/*`, `kestrel/creativity-db.json`, `kestrel/hop-protocol-*.json` | `kestrel/identity/*.md` (only structural updates), `kestrel/wiki/*` | NEVER: Striker signal engine code, gateway configs, SOUL.md tone/personality edits, agent SOUL files |
| **OpenClaw** | Infrastructure | `.openclaw/agents/*`, `~/.hermes/.env`, `~/.hermes/config.yaml`, gateway configs, systemd services, `huntsystems/kestrel-striker/core/config.py` | `kestrel/master-todo.md` (infra items only), `kestrel/coordination-guide.md` (infra sections) | NEVER: SOUL files, creativity DB, cron prompts, agent identity files |
| **Nemoclaw** | Identity & Skills | `kestrel/identity/*.md`, `~/.hermes/skills/*`, `kestrel/shared-skills/*`, SOUL files for all agents | `kestrel/coordination-guide.md` (lane definitions only), `kestrel/master-todo.md` (skill items only) | NEVER: shell scripts, cron jobs, gateway configs, Striker signal engine |
| **Kairos** | Timing & Signals | `kestrel/signals/*`, `kestrel/market-pulse/*`, timing-related board items | `kestrel/master-todo.md` (timing items), Striker health files (read-only) | NEVER: skills, identity files, gateway configs, creativity DB |
| **Shannon** | Referee & Code | `kestrel/code-reviews/*`, arbitration logs | Striker signal engine (read-only review), any code file (review only, no edit) | NEVER: cron jobs, gateway configs, agent identity, creativity DB |

### Shared Zones (any agent can propose changes, but with dibs protocol)

| File/Area | Dibs Rule |
|-----------|----------|
| `kestrel/master-todo.md` | Call it in group: "Dibs on [section]" — one agent at a time. 2-min edit window. |
| `kestrel/creativity-db.json` | Propose addition in group. Hermes integrates. |
| `kestrel/wiki/*` | Propose page in group. Nemoclaw approves structure. |

### Dibs Protocol (for shared files)
1. Post in group: `Dibs on [file/section] — editing [reason]`
2. Wait 10 seconds for objection
3. Edit
4. Post: `Released [file] — summary of change`
5. If agent is unresponsive for 5+ min, dibs times out

### Escalation Path
| Dispute Type | Escalate To | Rule |
|-------------|-------------|------|
| Code approach disagreement | Shannon | Shannon reviews both approaches, picks one, gives reasoning |
| Identity/lane disagreement | Nemoclaw | Nemoclaw owns all identity decisions |
| Protocol/coordination disagreement | Hermes | Hermes defines how the compound coordinates |
| Infrastructure disagreement | OpenClaw | OpenClaw owns all infra decisions |
| Tiebreaker (2-2 split) | Shannon | Shannon's ruling is final — no appeal |

### Verification Rule (anti-hallucination)
Before editing any file, the agent must read the current state first. Never patch a file you haven't read in this session.

Before claiming any system state (service running, file exists, config value set), the agent must verify it with a tool call. "I think" is not a valid prefix — either verify or say "I haven't checked."

## Hop Protocol v1.1

When the pipeline fires a Perplexity → Grok → AI Hangout hop, all agents **must** follow the hardened protocol at `kestrel/hop-protocol-v1.1.md`. Key rules:

- **No payload = no execution.** Every hop must have a payload manifest (task_name, priority, expected_output, success_criteria, lane_assignments)
- **Meta mode:** If `lane_assignments` is empty, the hop sharpens the protocol only — no business code touched
- **Handoff schema:** Perplexity → Grok includes payload status; Grok → AI Hangout includes lane assignments and risk scoring
- **Decomposition rules:** Lane first, agent second. One owner per subtask. 15-min block rule.
- **Output:** One pulse per active lane, aggregated summary, master-todo.md update, hub transfer
- **Conflicts:** This protocol wins over coordination-guide.md when they differ

## Compound Protocols

### Skill Auto-Improvement

If any agent loads a shared skill and finds it wrong, outdated, or missing steps, **patch it immediately**. Don't log it, don't flag it — fix it. Stale skills make the whole compound dumber.

### Knowledge Base

The compound wiki lives at `kestrel/wiki/index.md`. All agents must:
- Read it before asking questions that may already be answered
- Contribute to it when discovering something worth remembering
- Update it when fixing issues (especially troubleshooting steps)
- Link new pages from the index

Wiki is for compound knowledge. Skills are for procedure. Both are canonical.

### Email Visibility

Email highlights are posted to the group every 60min via the compound-email-drops cron. If you need to search email: ask Hermes (has Google Workspace skill). Kairos and Shannon will have direct email access once OAuth is configured in their profiles.

### Agent Handoff Protocol

When you receive a request that belongs in another agent's lane:

1. **Acknowledge it in-group:** "This is in [agent]'s lane, handing off."
2. **Option A (direct handoff):** Post `Handing off to @<agent>: <task description>`
3. **Option B (board handoff):** Write it to master-todo.md under their lane with status 🟡
4. **Do not** try to answer it yourself if it's outside your lane.
5. **Do not** stay silent — if you don't hand off, the request dies.

**Lane quick-ref (v2):**
- Hermes: Orchestrator — cron, coordination, scripts, creativity DB, archive squirrel
- OpenClaw: Infrastructure — gateway, config, systemd, Striker config
- Nemoclaw: Identity & Skills — SOULs, skill files, lane definitions
- Kairos: Timing & Signals — market pulses, Striker signal monitoring
- Shannon: Referee & Code Review — arbitration, code quality, dispute resolution

1. ✅ Conversation seeds (Hermes — done)
2. ✅ **Shared coordination (Hermes — done)**
3. ✅ **Shared skill library (Nemoclaw — done, at `kestrel/shared-skills/`)**
4. 🟡 **Role specialization (Nemoclaw — pick up)**
5. 🟡 Nemoclaw to load shared skills into agent startup sequence
6. ⚪ Boot persistence (OpenClaw — after P0)