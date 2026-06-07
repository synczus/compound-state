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