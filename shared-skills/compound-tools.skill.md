---
name: compound-tools
description: Every tool, system, and integration available in the compound, how each agent accesses them
category: coordination
---

# Compound Tools & Systems

## Shared Systems (All Agents)

| System | Location | Access | Notes |
|--------|----------|--------|-------|
| **Filesystem** | `/home/synczus/**` | Direct read/write | All agents have host filesystem access |
| **master-todo.md** | `/home/synczus/kestrel/master-todo.md` | Direct | Single source of truth for sprint work + HLM collection |
| **Coordination guide** | `/home/synczus/kestrel/coordination-guide.md` | Direct | Sprint execution order, agent guide |
| **Shared skills** | `/home/synczus/kestrel/shared-skills/` | Direct | Load at startup: roster, protocol, HLM workflow, tools |
| **HLM tracker** | `/home/synczus/archivesquirrel/active/plans/hlm-tracker.md` | Direct | Long-term HLM archive |
| **Dialogue state** | `/home/synczus/kestrel/dialogue-state.json` | Direct | Exchange counter for AI Hangout |
| **Memory bank** | `/home/synczus/kestrel/memory-bank/` | Direct | Agent propositions, system state |

## Tool Access by Agent

### Hermes (@kestrelmarkets_bot)
- **Cron jobs:** Full access — create, update, list, remove via `cronjob` tool
- **Email:** Gmail via google-workspace skill + email-pulse cron
- **Web search:** Full access via `web_search` tool
- **Files:** Full access via `read_file`, `write_file`, `patch`, `search_files`
- **Terminal:** Full access via `terminal` tool
- **Skills:** Full Hermes skill library (~100 skills)
- **Memory:** Persistent memory across sessions
- **Session search:** FTS5 search across all past conversations
- **Image gen:** Via Nous subscription
- **TTS:** Via Edge TTS

### OpenClaw (@kestrelmarkets_bot)
- **Gateway config:** Direct edit of `/home/synczus/.openclaw/openclaw.json`
- **Systemd services:** `systemctl --user` for gateway management
- **Terminal:** Full shell access
- **Files:** Full filesystem access
- **Web:** Via curl, Node.js

### Nemoclaw (@Nemoclaw8364_bot)
- **Gateway:** Separate instance on port 18791 with config at `/home/synczus/.openclaw-nemo/.openclaw/openclaw.json`
- **SOUL.md/identity:** Full edit of workspace files
- **Systemd:** Can restart own gateway service
- **Terminal:** Full shell access
- **Files:** Full filesystem access
- **Shared skills:** Reads from `/home/synczus/kestrel/shared-skills/`

### Kairos (@Kairos8638_bot)
- **Hermes profile:** Runs under `--profile kairos` — separate state/session DB
- **Model:** DeepSeek V4 Flash via OpenRouter
- **Skills:** Loads from `/home/synczus/.hermes/profiles/kairos/skills/`
- **Shared skills:** Should load from `/home/synczus/kestrel/shared-skills/`
- **Gateway:** Connected to Hermes gateway on 18789

### Shannon (@Shannon_bot)
- **Hermes profile:** Runs under `--profile shannon` — separate state/session DB
- **Model:** DeepSeek V4 Flash via OpenRouter
- **Skills:** Loads from `/home/synczus/.hermes/profiles/shannon/skills/`
- **Shared skills:** Should load from `/home/synczus/kestrel/shared-skills/`
- **Gateway:** Connected to Hermes gateway on 18789

## Cron Jobs (Hermes-managed, 18 active)

| Cron | Schedule | Type | Purpose |
|------|----------|------|---------|
| daily-digest | 8am | Script | Morning system status |
| system-hygiene | 240m | Script | System cleanup |
| service-watchdog | 5m | Script | Service health check |
| pipeline-watchdog | 10m | Script | Pipeline health |
| email-pulse | 240m | Google Workspace | Scan Gmail |
| morning-briefing | 9am | Google Workspace | Daily briefing |
| drive-scanner | 720m | Google Workspace | Check Drive |
| market-pulse | 30m | Script | Crypto prices + chart |
| squirrel-ingest | 60m | Script | Sort inbox files |
| memory-bank-consolidation | 15m | Script | Archive Squirrel |
| **compound-auto-conversation** | **5m** | **LLM** | **Seeds agent discussion** |
| compound-midday-huddle | 1pm | LLM | Midday check-in |
| compound-evening-wrap | 8pm | LLM | Evening bookend |
| hlm-scraper | 30m | Script | Collect HLMs from sessions |
| fallback/paused | various | Various | Portfolio, pipeline pulse, signal watch |

## Command Routing

| When user says... | Which agent handles | Via |
|-------------------|-------------------|-----|
| "todo" or "notes" | Master-todo.md / HLM tracker | Everyone writes to it |
| "run this terminal command" | Hermes / OpenClaw / Nemoclaw | Terminal tool |
| "check email" | Hermes | Google Workspace skill |
| "set up a cron" | Hermes | Cronjob tool |
| "fix gateway" | OpenClaw / Nemoclaw | Config files + systemd |
| "write a skill" | Nemoclaw | Skill files |
| "find something in past chats" | Hermes | Session search |
| "market pulse" | Hermes | Market-pulse cron |
| "research X" | Shannon | Web research |
| "market intel on Y" | Kairos | Market data