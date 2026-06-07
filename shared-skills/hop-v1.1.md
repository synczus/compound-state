# Perplexity → Grok → AI Hangout — Hardened Hop v1.1

**Status:** HARDENED | **Hop ID:** perplexity-grok-hangout-v1.1

## Core Rules
- **Require payload:** No hop runs without a concrete external deliverable
- **Require HLM:** Every output ends with highest leverage move
- **Require master-todo update:** All work logs to the board
- **Stay in lane:** No role overlap without explicit justification
- **No meta-only mode:** Process improvements must serve a declared deliverable

## Stage Flow

### Stage 1 — Perplexity (Research & Fact Annihilator)
Deep research the payload. Prioritize recent, high-signal sources. Destroy weak/outdated information.
- Input: payload + context
- Output: key_findings, sources, uncertainties, research_gaps

### Stage 2 — Grok (Truth, Inversion & Leverage)
Stress-test Stage 1. Identify hidden risks, second-order effects, false assumptions.
- Input: Stage 1 + original payload
- Output: inversion_analysis, key_risks, leverage_points, highest_leverage_move

### Stage 3 — AI Hangout (Execution Swarm)
5-agent decomposition: Shannon, Hermes, OpenClaw, Kairos, Nemoclaw.
Take refined signal → concrete action against deliverable. Decompose by lane.
- Input: Stage 1 + Stage 2 + payload
- Output: assigned_tasks, files_changed, commands_to_run, master_todo_updates, HLM

## Payload Requirements
```json
{
  "deliverable": "Concrete external outcome",
  "success_criteria": "Measurable definition of done",
  "timebox_hours": "Max hours for execution",
  "priority": "P0 | P1 | P2"
}
```

## Forbidden
- Running without a concrete deliverable
- Producing only internal tooling/process improvements
- Skipping master-todo.md updates
- Role overlap without explicit justification

---

*Reference: /home/synczus/huntsystems/agent-pulses/2026-06-06/ — full hop definition from Chase*