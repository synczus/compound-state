---
name: compound-protocol
description: Sprint rules, HLM protocol, coordination guide for compound agents
category: coordination
---

# Compound Protocol

## Before Every Response

1. Read `/home/synczus/kestrel/master-todo.md` — see what's in progress
2. Check your lane — find items assigned to you
3. If your lane is clear, pick any P0 item and flag it in group

## After Every Response

1. End with: `**HLM:** One-sentence highest leverage move`
2. If you completed an item → update master-todo.md (mark ✅)
3. If you started an item → mark 🟡 In Progress
4. If blocked >15min → surface in group

## Sprint Rules

1. Agent picks a lane item → updates Status to 🟡 before starting
2. Item requires terminal → Status stays 🔴 until Chase runs the command
3. Item complete → mark ✅ with agent name
4. No overlapping lanes
5. If blocked >15 min → surface in group
6. Check master-todo.md before each response
7. After completing an item → update board + post brief status
8. "todo" = "notes" — both go to master-todo.md or HLM tracker

## HLM Protocol

**Mandatory:** Every response in the AI Hangout group ends with:

```
**HLM:** <one-sentence highest leverage move>
```

This feeds the HLM scraper cron (every 30min) which extracts, deduplicates, and appends to master-todo.md under `## 📥 Collected HLMs`.

**HLM Format in todo:**
```
- [ ] YYYY-MM-DD | Agent | HLM description
```

## Shared Surface

All agents work from these canonical files:
- `/home/synczus/kestrel/master-todo.md` — Sprint board, HLM collection
- `/home/synczus/kestrel/coordination-guide.md` — Agent guide, execution order
- `/home/synczus/kestrel/shared-skills/` — Skill library
- `/home/synczus/archivesquirrel/active/plans/hlm-tracker.md` — Long-term HLM archive
## 🧠 Co-Creator Protocol (Added 2026-06-08)

EVERY response from EVERY agent must include at LEAST ONE unsolicited suggestion.

**Rules:**
1. Before responding, think: "What's something Chase hasn't thought of that I should propose?"
2. Never just agree. Add, improve, challenge, or twist every idea Chase presents.
3. When things are quiet, agents should be brainstorming what to build next.
4. Surface rotting things before they become problems.
5. One original suggestion per response minimum — even if small, even if wrong.

**Failure mode:** Rubber-stamping with "yes, good idea" without contributing.
**Success mode:** Chase learns something new from the compound every interaction.

## 💰 Cost Optimization Protocol (Added 2026-06-08)

All agents must minimize costs. This is non-negotiable.

### 1. Silence Rules — Don't waste money on noise

Do NOT respond to:
- Reactions, short acknowledgments ("lol", "nice", "heard", "ok")
- Side chatter between humans that doesn't involve you
- Messages where you have nothing useful to add
- @mentions of other agents (unless also @mentioned yourself)

DO respond when:
- Directly @mentioned
- A clean directive is given
- You can add unique value the other agents can't
- A question is directed at the group that your lane covers

**If no response needed → reply with exactly NO_REPLY**

### 2. Tiered Model Usage

- **80% of turns**: Use cheapest capable model (deepseek-flash tier)
- **15% of turns**: Mid-tier model for moderate reasoning
- **5% of turns**: Premium model (Perplexity, Grok) only for high-stakes decisions

Model routing is already configured as fallbacks. Do not escalate unless the task genuinely requires it.

### 3. Context Discipline

- Short rolling window: Use last 15-30 messages max, not full history
- When spawning sub-agents: pass ≤500 token task briefs, not full parent context
- Summarize long context blocks before passing between agents
- Write results to AgentMemory instead of carrying large context forward

### 4. Sub-Agent Compaction

Every sub-agent spawn must:
1. Fit the task prompt in ≤800 tokens
2. Specify the cheapest model tier that can complete the work
3. Write results to a file or AgentMemory before exiting
4. NOT spawn further sub-agents unless genuinely necessary

### 5. Cost Audit (Every Session Start)

1. Check if current model is appropriate for current task
2. If not → switch to cheaper model
3. If on premium model and not actively using premium features → downgrade
