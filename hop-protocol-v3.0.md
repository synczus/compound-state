# Universal Persistent Hop v3.0

**Status:** ✅ Canonical | **Supersedes:** Hop Protocol v1.1 | **Date:** 2026-06-06

**Core Rule:** Truth first. Real goal second. Usefulness third. No hallucinated files, services, results, or agent state.

## Pipeline Flow

```
AI Hangout (intake) → Perplexity → Grok → Gemini → Claude → Codex → AI Hangout (banking)
   ↓                                                                             ↓
  selects work                                                        synthesizes, banks HLMs,
  from chat/board                                                      assigns next work, loops
```

## The 7 Stages

| Stage | Agent | Role | What They Do |
|-------|-------|------|-------------|
| 0 | **AI Hangout** (swarm) | Context Intake / Work Selector | Read chat, board, HLM tracker. Pull strongest work item. Package context. Do NOT solve. |
| 1 | **Perplexity** | Research & Fact Annihilator | Research the work item. Kill weak/outdated claims. Separate facts from inferences. |
| 2 | **Grok** | Truth, Inversion & Leverage | Stress-test Perplexity. Invert the plan. Surface hidden risks, false assumptions. |
| 3 | **Gemini** | Scout / Evidence Mapper | Verify what exists in chat, files, services, configs, boards, logs, runtime. Output evidence and gaps. |
| 4 | **Claude** | Architect / Risk Judge | Judge architecture and sequence. Define what NOT to touch. Safest executable path. |
| 5 | **Codex** | Operator / Patch Executor | Convert plan into real commands and patches. Inspect before editing. Verify with real proof. |
| 6 | **AI Hangout** (swarm) | Synthesis / Banking / Assignment | Merge all outputs. Assign work. Update todo/notes. Bank HLMs. Emit final action. Loop. |

## Shared Rules

- **HLMs required** at every stage — format: `Highest Leverage Move: [one sentence]`
- **Next agent routing** at every stage — explicit agent name, role, reason, instruction, context
- **No fake execution** — never claim success without verifiable evidence
- **Manual tabs, not parallel** — each stage waits for the prior one
- **Stay in lane** — Perplexity researches, Grok inverts, Gemini maps, Claude judges, Codex executes
- **Handoff format** — Pass original query + all prior stage outputs + evidence packet
- **Update todo/notes** — every stage updates the board with findings

## How The Loop Closes

1. AI Hangout selects work from chat/board → packages context
2. Perplexity grounds it in real facts
3. Grok stress-tests and inverts
4. Gemini maps evidence (files, configs, logs, runtime)
5. Claude judges architecture and sequence
6. Codex executes real changes with verification
7. AI Hangout banks HLMs, assigns follow-up → back to step 1

## Trigger

This is a **manual_multi_tab** mode. Triggered by the operator (Chase/synczus) in AI Hangout group. When you want a full pipeline run, drop the query into AI Hangout and say "hop" or "run pipeline" or tag the swarm.

## Superseded

- **Hop Protocol v1.1** (2026-06-06) — replaced by v3.0. v1.1 forbade pure meta mode and required concrete payloads. v3.0 keeps those rules but adds full 7-stage routing, evidence verification, and closed-loop banking.