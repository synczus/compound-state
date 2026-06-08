---
name: compound-voting
description: DEPRECATED — use compound-vote.skill.md instead (consolidated v2)
category: governance
---

# DEPRECATED

**This file is deprecated as of 2026-06-08.** The consolidated voting protocol lives in `compound-vote.skill.md`.

## Migration

- All agents should reference `shared-skills/compound-vote.skill.md` for current voting procedure
- Vote data lives in `/home/synczus/kestrel/vote-board.json`
- The old `baton/polls/` system is deprecated but existing polls remain for reference
- This file may be removed after 2026-06-15

## Why Deprecated?

The compound had two parallel voting protocols (`compound-vote.skill.md` and `compound-voting.skill.md`) with incompatible structures. The consolidated v2 resolves the conflict by standardizing on `vote-board.json` as the single source of truth.