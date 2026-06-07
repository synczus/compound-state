# Universal Persistent Hop v3.2

**Mode:** manual multi-tab cycle
**Purpose:** AI Hangout pulls work from chat/todo → research → inversion → evidence → risk → execution → banking → next cycle
**Core Rule:** Every hop must pay rent. Truth first. Real goal second. Usefulness third. No hallucinated files, services, configs, logs, tasks, or completed work.

## Cycle Order

```
AI Hangout Intake → Perplexity → Grok → Gemini → Claude → Codex → AI Hangout Banking → (next cycle intake)
```

## Shared Rules

- Stay in lane
- Separate facts, inference, and guesses
- Verify before stateful action
- Preserve all open loops
- Every output must include a Highest Leverage Move
- Every output must explicitly name the next agent at the bottom
- Manual tabs are not parallel execution — each hop is a clear handoff
- AI Hangout starts the cycle (selects work from chat/todo)
- AI Hangout ends the cycle (banks HLMs, assigns tasks, updates todo/notes)

---

## Stage 0 — AI Hangout Intake

**Role:** Context Intake / Work Selector
**Agents:** Shannon, Hermes, OpenClaw, Kairos, Nemoclaw

**Task:** Read current chat, todo board, HLM tracker, recent agent outputs, unresolved open loops. Pick the strongest concrete work item for this cycle. Package the context for Perplexity. Do not solve it yet.

**Output:**
- Selected work item
- Why this work now
- Context packet
- Known files/chat evidence
- Current blockers
- Open loops
- Highest Leverage Move
- Next Agent Routing

```
NEXT AGENT ROUTING:
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

```
NEXT AGENT ROUTING:
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

```
NEXT AGENT ROUTING:
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

```
NEXT AGENT ROUTING:
Next Agent Name: Claude
Next Agent Role: Architect / Risk Judge
Reason for next hop: Gemini mapped reality; Claude must judge sequence, architecture, and risk.
Instruction to next agent: Produce the risk-ranked recommendation, safest sequence, do-not-touch list, and success criteria.
Context to pass forward: Original request + all prior outputs + Gemini evidence/file manifest.
```

---

## Stage 4 — Claude

**Role:** Architect / Risk Judge

**Task:** Use Gemini's evidence to judge architecture, sequencing, risk, and failure modes. Define what must not be touched yet. Produce the safest executable path.

**Output:**
- Risk-ranked assessment
- Architecture judgment
- Do-not-touch list
- Recommended sequence
- Success criteria
- Highest Leverage Move
- Next Agent Routing

```
NEXT AGENT ROUTING:
Next Agent Name: Codex
Next Agent Role: Operator / Patch Executor
Reason for next hop: Claude defined the safe path; Codex must convert it into executable commands or scoped patches.
Instruction to next agent: Inspect before editing, make only justified scoped changes, and verify with proof.
Context to pass forward: Original request + all prior outputs + Gemini evidence + Claude risk plan.
```

---

## Stage 5 — Codex

**Role:** Operator / Patch Executor

**Task:** Convert the verified plan into commands, patches, or implementation steps. Inspect before editing. Keep changes scoped. Verify with real proof. Do not claim success without evidence.

**Output:**
- Execution plan
- Commands run or commands to run
- Files touched or files to touch
- Verification steps
- Proof required
- Highest Leverage Move
- Next Agent Routing

```
NEXT AGENT ROUTING:
Next Agent Name: AI Hangout
Next Agent Role: Synthesis / Banking / Assignment
Reason for next hop: Codex produced the execution path/proof; AI Hangout must merge, bank, and assign final work.
Instruction to next agent: Synthesize without inventing facts. Bank HLMs, update todo/notes, assign owners, and emit the next concrete action.
Context to pass forward: Original request + full cycle outputs + execution plan/proof/open loops.
```

---

## Stage 6 — AI Hangout Banking

**Role:** Synthesis / Banking / Assignment
**Agents:** Shannon, Hermes, OpenClaw, Kairos, Nemoclaw

**Task:** Merge all outputs without inventing facts. Bank every HLM. Update todo/notes. Assign work across lanes. Emit one final recommended action with owner and first step.

**Output:**
- Merged verdict
- Assigned tasks
- Files changed or to change
- Commands to run
- Todo/notes updates
- Banked Highest Leverage Moves
- Open loops
- Final Highest Leverage Move
- Next Agent Routing

```
NEXT AGENT ROUTING:
Next Agent Name: AI Hangout
Next Agent Role: Context Intake / Work Selector for next cycle
Reason for next hop: The cycle is complete; AI Hangout should pull the next work item from live chat/todo.
Instruction to next agent: Start the next cycle only after banking this cycle's HLMs, todo updates, and open loops.
Context to pass forward: Final merged verdict + todo updates + banked HLMs + unresolved blockers.
```