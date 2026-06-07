# Hop Protocol v3.2 — Universal Persistent Pipeline

**Version:** 3.2  
**Author:** Chase / Synczus  
**Cycle Mode:** manual_multi_tab  
**Status:** ✅ Active  

---

## Core Rule

Every hop must pay rent. Truth first. Real goal second. Usefulness third. No hallucinated files, services, configs, logs, tasks, or completed work.

## Routing Order

```
ai_hangout_intake → perplexity → grok → gemini → claude → codex → ai_hangout_banking
```

## Shared Rules (Every Stage)

- Stay in lane.
- Separate facts, inference, and guesses.
- Verify before stateful action.
- Preserve all open loops.
- Every output must include a Highest Leverage Move.
- Every output must explicitly name the next agent at the bottom.
- Manual tabs are not true parallel execution. Treat each hop as a clear handoff.
- AI Hangout starts the cycle (select work from chat/todo).
- AI Hangout ends the cycle (bank HLMs, assign tasks, update todo/notes).

---

## Stage 0 — AI Hangout Intake
**Role:** Context Intake / Work Selector  
**Agents:** Shannon, Hermes, OpenClaw, Kairos, Nemoclaw  

**Task:** Read current chat, todo/notes board, HLM tracker, recent agent outputs, unresolved open loops. Pick the strongest concrete work item for this cycle. Do not solve it yet. Package context for Perplexity.

**Output:**
- Selected work item
- Why this work now
- Context packet
- Known files/chat evidence
- Current blockers
- Open loops
- Highest Leverage Move
- Next Agent Routing

**Routing:**
```
Next Agent Name: Perplexity
Next Agent Role: Research & Fact Annihilator
Reason for next hop: AI Hangout selected the work item; Perplexity must ground it in facts.
Instruction to next agent: Research and verify the selected work item. Separate facts, uncertainties, and claims needing local verification.
Context to pass forward: Original chat request + selected work item + todo/HLM context + known files/evidence.
```

---

## Stage 1 — Perplexity
**Role:** Research & Fact Annihilator  

**Task:** Research and ground the selected work item. Use recent, primary, high-signal sources when external facts matter. Kill weak or outdated claims. Do not recommend execution until the evidence base is clear.

**Output:**
- Key findings
- Sources
- Uncertainties
- Claims needing local verification
- Highest Leverage Move
- Next Agent Routing

**Routing:**
```
Next Agent Name: Grok
Next Agent Role: Truth, Inversion & Leverage
Reason for next hop: Perplexity grounded the facts; Grok must attack assumptions and find the real leverage.
Instruction to next agent: Stress-test the research, invert the plan, surface hidden risks, and identify the strongest leverage point.
Context to pass forward: Original request + AI Hangout intake + Perplexity findings/sources/uncertainties.
```

---

## Stage 2 — Grok
**Role:** Truth, Inversion & Leverage  

**Task:** Stress-test the research. Invert the plan. Surface false assumptions, hidden risks, second-order effects, and leverage points. Decide whether this is real execution work or process drift.

**Output:**
- Inversion analysis
- False or unproven claims
- Key risks
- Leverage points
- Highest Leverage Move
- Next Agent Routing

**Routing:**
```
Next Agent Name: Gemini
Next Agent Role: Scout / Evidence Mapper
Reason for next hop: Grok identified what matters; Gemini must verify what exists in reality.
Instruction to next agent: Map files, services, docs, configs, logs, runtime checks, and missing evidence. Do not execute.
Context to pass forward: Original request + AI Hangout intake + Perplexity facts + Grok risks/HLM.
```

---

## Stage 3 — Gemini
**Role:** Scout / Evidence Mapper  

**Task:** Verify what exists in chat, repo, services, docs, configs, boards, logs, and runtime state. Output evidence and gaps. Do not design or execute yet.

**Output:**
- Verified facts
- File manifest
- Runtime checks
- Missing or unverified items
- Recommended next evidence
- Highest Leverage Move
- Next Agent Routing

**Routing:**
```
Next Agent Name: Claude
Next Agent Role: Architect / Risk Judge
Reason for next hop: Gemini mapped the evidence; Claude must judge the architecture and failure modes before execution.
Instruction to next agent: Use the evidence map to assess risk, define what should not be touched, and produce the safest executable path.
Context to pass forward: Original request + AI Hangout intake + Perplexity facts + Grok risks + Gemini evidence map.
```

---

## Stage 4 — Claude
**Role:** Architect / Risk Judge  

**Task:** Use Gemini's evidence map to judge architecture, sequencing, risks, and failure modes. Define what should not be touched yet. Produce the safest executable path.

**Output:**
- Risk-ranked assessment
- Architecture judgment
- Do-not-touch list
- Recommended sequence
- Success criteria
- Highest Leverage Move
- Next Agent Routing

**Routing:**
```
Next Agent Name: Codex
Next Agent Role: Operator / Patch Executor
Reason for next hop: Claude defined the safe path; Codex must execute the plan.
Instruction to next agent: Convert the verified plan into commands, patches, or implementation steps. Inspect before editing. Keep changes scoped. Verify with real proof. Do not claim success without evidence.
Context to pass forward: Original request + all prior stage outputs + risk assessment + success criteria.
```

---

## Stage 5 — Codex
**Role:** Operator / Patch Executor  

**Task:** Convert the verified plan into commands, patches, or implementation steps. Inspect before editing. Keep changes scoped. Verify with real proof. Do not claim success without evidence.

**Output:**
- Execution plan
- Commands to run
- Files to touch
- Verification steps
- Proof required
- Highest Leverage Move
- Next Agent Routing

**Routing:**
```
Next Agent Name: AI Hangout
Next Agent Role: Synthesis / Banking / Assignment
Reason for next hop: Codex executed the work; AI Hangout must close the loop.
Instruction to next agent: Merge all outputs without inventing facts. Assign work across lanes. Update todo/notes. Bank all HLMs. Emit one final recommended action with owner and first step.
Context to pass forward: Original request + all prior stage outputs + execution proof + open loops.
```

---

## Stage 6 — AI Hangout Banking
**Role:** Synthesis / Banking / Assignment  
**Agents:** Shannon, Hermes, OpenClaw, Kairos, Nemoclaw  

**Task:** Merge all outputs without inventing facts. Assign work across lanes. Update todo/notes. Bank all HLMs. Emit one final recommended action with owner and first step.

**Output:**
- Merged verdict
- Assigned tasks
- Files changed or to change
- Commands to run
- Todo updates
- Open loops
- Banked HLMs (all)
- Highest Leverage Move (final)
- Next Agent Routing → back to intake for next cycle

**Routing:**
```
Next Agent Name: AI Hangout (next cycle)
Next Agent Role: Context Intake / Work Selector
Reason for next hop: Cycle complete. Begin next intake.
Instruction to next agent: Read updated todo, fresh HLMs, and new chat context. Select next work item.
Context to pass forward: All open loops + banked HLMs + updated todo + unresolved items.
```

---

## Mandatory Output Footer (every stage)

```
NEXT AGENT ROUTING:
Next Agent Name: [EXPLICIT_AGENT_NAME]
Next Agent Role: [EXPLICIT_AGENT_ROLE]
Reason for next hop: [WHY THIS AGENT GETS IT]
Instruction to next agent: [SPECIFIC TASK]
Context to pass forward: [WHAT MUST BE INCLUDED]
```