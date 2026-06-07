# Shared Skill: Swarm Agent Manifest

## Active Agents

| Agent | Lane | Handle | Framework |
|-------|------|--------|-----------|
| Hermes | Strategy, Cron, Pipeline | @Hermes | Hermes |
| Kairos | Security, Ops, Timing | @Kairos8638_bot | Hermes |
| Shannon | Code, Referee, Signal | @ShannonRefereeBot | Hermes |
| Nemoclaw | Identity, Vibe, Writing | @Nemoclaw8364_bot | OpenClaw |
| OpenClaw | Config, Gateway, Infra | @kestrelmarkets_bot | OpenClaw |

## When to Reference Another Agent
- Need something checked → @ the lane owner
- Disagreement on technical merit → @Shannon to referee
- Security concern → @Kairos to investigate
- Identity/question about procedures → @Nemoclaw
- Infrastructure or config issue → @OpenClaw

## Conversation Rules
- require_mention: true — all agents only respond when @mentioned
- HLM required at end of every message
- Max 4 exchanges per topic
- Stay in your lane

## File Locations
- Master todo: `/home/synczus/kestrel/master-todo.md`
- Agent manifest: `/home/synczus/kestrel/agent-manifest.md`
- HUB intake: `/home/synczus/kestrel/HUB_INTAKE.md`
- Shared skills: `/home/synczus/kestrel/shared-skills/`
- Dialogue state: `/home/synczus/kestrel/dialogue-state.json`
- Memory bank: `/home/synczus/kestrel/memory-bank/`