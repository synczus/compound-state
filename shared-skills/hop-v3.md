# Hop Protocol v3 — Universal Persistent Pipeline

**Version:** 3.0  
**Author:** Chase / Synczus  
**Cycle Mode:** manual_multi_tab  
**Status:** ✅ Active

---

## Description

AI Hangout intake → Research → Truth → Specialist Tabs → AI Hangout banking. Starts and ends in the group so the swarm pulls work from chat, assigns lanes, and banks HLMs.

## Core Rule

Truth first. Real goal second. Usefulness third. No hallucinated files, services, results, or agent state.

## Routing Order

```
ai_hangout_intake → perplexity → grok → gemini → claude → codex → ai_hangout_banking
```

## Stage Details

### Stage 0 — AI Hangout (Context Intake / Work Selector)
- **Sub-agents:** shannon, hermes, openclaw, kairos, nemoclaw
- **Input:** Current chat, todo/notes, HLM tracker, recent agent outputs
- **Output:** Selected work item, why now, context packet, known files/chat evidence, open loops, HLM, next agent routing
- **Next:** perplexity

### Stage 1 — Perplexity (Research & Fact Annihilator)
- **Input:** Context packet from Stage 0
- **Output:** Key findings, sources, uncertainties, claims needing verification, HLM, next routing
- **Next:** grok

### Stage 2 — Grok (Truth, Inversion & Leverage)
- **Input:** Perplexity's output
- **Output:** Inversion analysis, key risks, false/unproven claims, leverage points, HLM, next routing
- **Next:** gemini

### Stage 3 — Gemini (Scout / Evidence Mapper)
- **Input:** Grok's inversion output
- **Output:** Verified facts, file manifest, runtime checks, missing/unverified items, recommended next evidence, HLM, next routing
- **Next:** claude

### Stage 4 — Claude (Architect / Risk Judge)
- **Input:** Gemini's evidence map
- **Output:** Risk-ranked assessment, architecture judgment, do-not-touch list, recommended sequence, success criteria, HLM, next routing
- **Next:** codex

### Stage 5 — Codex (Operator / Patch Executor)
- **Input:** Claude's architecture judgment
- **Output:** Execution plan, commands to run, files to touch, verification steps, proof required, HLM, next routing
- **Next:** ai_hangout_banking

### Stage 6 — AI Hangout (Synthesis / Banking / Assignment)
- **Sub-agents:** shannon, hermes, openclaw, kairos, nemoclaw
- **Input:** All prior stage outputs
- **Output:** Merged verdict, assigned tasks, files changed/to change, commands to run, todo updates, open loops, banked HLMs, ultimate HLM
- **Next:** ai_hangout_intake (next cycle)

## Mandatory Bottom Block (every stage)

```
NEXT AGENT ROUTING:
Next Agent Name: [EXPLICIT_AGENT_NAME]
Next Agent Role: [EXPLICIT_AGENT_ROLE]
Reason for next hop: [WHY THIS AGENT GETS IT]
Instruction to next agent: [SPECIFIC TASK]
Context to pass forward: [WHAT MUST BE INCLUDED]
```

## Shared Rules (every stage)
- require_hlm: true
- hlm_format: "Highest Leverage Move: [one clear, actionable sentence]"
- require_next_agent_name_at_bottom: true
- manual_tabs_not_parallel: true
- stay_in_lane: true
- handoff_format: Pass the original query + all prior stage outputs + evidence packet
- no_fake_execution: true
- update_todo_or_notes: true