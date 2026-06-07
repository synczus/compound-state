# Universal Persistent Hop v3

**Hop ID:** `universal-persistent-hop-v3`
**Version:** 3.0
**Operator:** Chase / Synczus
**Cycle Mode:** manual_multi_tab
**Core Rule:** Truth first. Real goal second. Usefulness third. No hallucinated files, services, results, or agent state.

## Pipeline

```
AI Hangout Intake → Perplexity → Grok → Gemini → Claude → Codex → AI Hangout Banking → (next cycle)
```

Every cycle starts and ends in the AI Hangout. The swarm pulls work from chat, routes through research/truth/architecture stages, then banks the results.

## Shared Rules

- **require_hlm:** true — every output ends with HLM
- **require_next_agent_name_at_bottom:** true — mandatory routing block
- **manual_tabs_not_parallel:** true — sequential, not parallel
- **stay_in_lane:** true
- **handoff_format:** pass original query + all prior outputs + evidence packet
- **no_fake_execution:** true
- **update_todo_or_notes:** true

## Stage Roles

| Stage | Agent | Role |
|-------|-------|------|
| 0 | AI Hangout (swarm) | Context intake, work selector, payload definition |
| 1 | Perplexity | Research & fact annihilation |
| 2 | Grok | Truth, inversion & leverage |
| 3 | Gemini | Scout / evidence mapper |
| 4 | Claude | Architect / risk judge |
| 5 | Codex | Operator / patch executor |
| 6 | AI Hangout (swarm) | Synthesis, banking, lane assignment |

## Mandatory Bottom Block

Every hop handoff must end with:

```
NEXT AGENT ROUTING:
Next Agent Name: [EXPLICIT_AGENT_NAME]
Next Agent Role: [EXPLICIT_AGENT_ROLE]
Reason for next hop: [WHY THIS AGENT GETS IT]
Instruction to next agent: [SPECIFIC TASK]
Context to pass forward: [WHAT MUST BE INCLUDED]
```

## This Changes Things

This is the first protocol that explicitly names the AI Hangout **swarm** as a stage player — not just 5 bots reacting, but a coordinated intake/synthesis layer that pulls work from chat and assigns lanes. The pipeline from intake → research → truth → evidence → architecture → execution → banking is now fully specified.