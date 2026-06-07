# Kestrel Shared Skill Library

A shared skill repository accessible to all agents in the swarm. Any agent can read a skill and implement it without needing to ask another agent.

## Skill Format

Each skill lives in its own directory under `/home/synczus/kestrel/skills/<skill-name>/` and contains:

| File | Purpose |
|---|---|
| `SKILL.md` | Instructions any agent can follow to implement this skill |
| `scripts/` | Runnable scripts (optional) |
| `templates/` | Config templates, cron defs, etc. (optional) |

## How to Use

1. Browse the skills below
2. Read the `SKILL.md` for the one you want
3. Implement it — you have what you need

## Skill Catalog

| Skill | Lane | Status | Output |
|---|---|---|---|
| identity-management | Identity | 🟢 Ready | Agent SOUL.md files |
| autonomous-chat | Cron | 🟡 Needs cron register | 5min pulses to group |
| todo-extraction | Cron | 🟢 Ready | Auto-fills master-todo.md |
| market-pulse | Cron | 🟢 Ready | 4h crypto chart |
| ctf-engine | Identity | 🟢 Ready | CTF rounds with Shannon |
| pipeline-signal | Infra | 🟢 Ready | Pipeline health checks |
| telegram-file-archiver | Infra | 🟡 Placeholder — needs bot token + jq | File auto-archive from group |
| gif-communication | Shared | 🟢 Ready | GIF reactions in Telegram |

## Tool Registry

All agents should read `/home/synczus/kestrel/tool-registry.json` on session startup. It maps every tool, command, path, and service in the stack — so no agent guesses what command to use.

## Creating a New Skill

1. Create `<skill-name>/SKILL.md` with:
   - What it does
   - Requirements
   - Step-by-step implementation
   - Verification steps
2. Add scripts/ or templates/ as needed
3. Update this README with the new entry