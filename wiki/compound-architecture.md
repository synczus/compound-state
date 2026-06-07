# Compound Architecture

## Agent Map

| Agent | Gateway | Port | Profile | Config |
|-------|---------|------|---------|--------|
| Hermes / OpenClaw | openclaw-gateway.service | 18789 | default | `~/.openclaw/openclaw.json` |
| Nemoclaw | openclaw-nemoclaw.service | 18791 | nemo | `~/.openclaw-nemo/.openclaw/openclaw.json` |
| Kairos | hermes-gateway (profile) | — | kairos | `~/.hermes/profiles/kairos/config.yaml` |
| Shannon | hermes-gateway (profile) | — | shannon | `~/.hermes/profiles/shannon/config.yaml` |

## Shared Surface

All agents read from:
- `kestrel/master-todo.md` — sprint board + HLM collection
- `kestrel/coordination-guide.md` — protocols, handoff rules
- `kestrel/shared-skills/` — skill library (4 skills)
- `kestrel/wiki/` — compound knowledge base
- `kestrel/HUB_INTAKE.md` — pipeline state
- `kestrel/dialogue-state.json` — exchange counter

## Network

- All agents on DeepSeek V4 Flash via OpenRouter
- Telegram group: AI Hangout (-5087043705)
- All agents have `requireMention: false` for the group
- Dashboard at http://127.0.0.1:19500/