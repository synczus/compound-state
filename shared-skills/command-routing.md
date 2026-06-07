# Shared Skill: Command Routing & Response Protocol

## When Chase Says "Do This"

Every agent should map common requests to the correct handler:

| If Chase says… | The agent that handles it | What they do |
|---|---|---|
| "set up a cron" / "schedule X" | Nemoclaw (OpenClaw) | Uses cron() tool on OpenClaw gateway |
| "check if X is running" / "verify X" | Kairos | Uses exec() to check process/system state |
| "review this code" / "score this" | Shannon | Reads the code/file, provides analysis |
| "what's the strategy" / "plan X" | Hermes | Proposes plan, writes to board |
| "restart X" / "fix config" | OpenClaw (main) | Gateway config, systemctl, service files |
| "write a SOUL" / "update identity" | Nemoclaw | Writes files, edits configs |
| "add to the board" / "notes" | Anyone | Writes to master-todo.md and memory-bank |

## Before Responding — Sync Protocol

Before any response, each agent should:
1. Read `/home/synczus/kestrel/master-todo.md` — check if the board changed
2. Read `/home/synczus/kestrel/HUB_INTAKE.md` — check pipeline state
3. Check if someone else already answered the question (avoid duplicate work)

## When You Don't Know

If a request doesn't fit your lane:
- Say "That's [agent]'s lane — @ them" and provide context
- Don't guess. Don't attempt work outside your lane.

## Shared Filesystem

All agents share the same host filesystem. These paths are accessible to everyone:
- `/home/synczus/kestrel/master-todo.md` — sprint board
- `/home/synczus/kestrel/shared-skills/` — skill library
- `/home/synczus/kestrel/memory-bank/` — propositions + context
- `/home/synczus/kestrel/HUB_INTAKE.md` — pipeline state

## Cron Ownership

- **Nemoclaw (OpenClaw gateway):** Owns crons that fire to the group (thought drops, pulses). These are set via cron() tool on the OpenClaw gateway.
- **Hermes, Kairos, Shannon (Hermes framework):** Each has their own cron system in their Hermes profile. They do NOT share Nemoclaw's cron pool.
- If a cron needs to fire to the group and @mention agents, Nemoclaw sets it up since group access routes through OpenClaw's Telegram integration.