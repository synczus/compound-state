# Skill: identity-management

Set up or update an agent's identity file so they know who they are, what lane they own, and how to interact in the group.

## Requirements

- Write access to the agent's workspace or profile directory
- Knowledge of the agent's role in the swarm

## Implementation

### For OpenClaw agents (main workspace at ~/.openclaw/workspace/)

1. Write or update `SOUL.md` in the agent's workspace
2. Include: core truths, lane assignment, session startup sequence, tone/voice, grounding rule, security rule
3. Reference the shared initiation protocol: `/home/synczus/kestrel/identity/initiation-protocol.md`

### For Hermes profile agents (~/.hermes/profiles/<name>/)

1. Write or update `SOUL.md` in the profile directory
2. Same structure as above
3. Add at session startup: read `HUB_INTAKE.md`, `master-todo.md`, and `initiation-protocol.md`

## Verification

- Agent responds in-character within their lane
- Agent ends responses with "Highest-leverage move: ..."
- Agent references the initiation protocol when deciding to speak or stay silent