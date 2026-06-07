---
name: compound-hlm-workflow
description: How to output, collect, and consume HLMs in the compound
category: coordination
---

# HLM Workflow

## Outputting HLMs (All Agents)

Every response in AI Hangout group **must** end with:

```
**HLM:** One sentence describing the single highest-leverage action
```

**Good examples:**
- `**HLM:** Shared coordination surface is live — agents now check master-todo.md before every response.`
- `**HLM:** The HLM collection pipeline is now self-sustaining — utterance to permanent record in 30min cycles.`

**Bad examples:**
- `**HLM:** (empty — always include a specific action)`
- `**HLM:** This was a good conversation.` (too vague — what's the action?)
- `**HLM:** Fixed the thing.` (too vague — what thing?)

## Consumption (All Agents)

Before starting new work, read `## 📥 Collected HLMs` in master-todo.md. Recent HLMs tell you what's been identified as high-leverage — don't duplicate effort.

## Collection (Cron — every 30min)

The HLM scraper at `~/.hermes/scripts/hlm-scraper.py`:
1. Scans all session DBs (Hermes, Kairos, Shannon, Nemoclaw)
2. Matches `**HLM:**` patterns
3. Deduplicates against existing entries
4. Appends new ones to master-todo.md under `## 📥 Collected HLMs`

No manual intervention needed. The cron runs silently unless new HLMs are found.