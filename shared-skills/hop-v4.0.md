# Hop Protocol v4.0 — Universal Persistent Baton

**Version:** 4.0  
**Author:** Chase / Synczus  
**Cycle Mode:** dynamic (skip unnecessary agents)  
**Status:** ✅ Active  

---

## Core Rule

Every hop must pay rent. Truth first. Real goal second. Usefulness third. No hallucinated files, services, configs, logs, tasks, or completed work.

---

## Key Upgrade from v3.x → v4.0

| Feature | v3.x | v4.0 |
|---------|------|------|
| Cycle mode | Fixed 7-stage chain | Dynamic — skip unnecessary agents |
| Handoff format | Prose footer | Universal Baton Schema (JSON) |
| Mission classification | None | Required — flags external/local/risk needs |
| Battery file | Not stored | `active-baton.json` — canonical live state |
| Kill switch | None | "Terminate useless hops" gate |
| Storage | Inline | Structured with commit authority |
| Agent lanes | Roles only | Allowed + forbidden actions per lane |

---

## Dynamic Cycle (preferred)

```
AI Hangout Intake → Mission Classification → Required Evidence Gate
  → Required Risk Gate → Execution or Recommendation → Verification
  → AI Hangout Banking
```

Skip Perplexity if no external research needed.  
Skip Grok if no assumptions need attacking.  
Skip Gemini if evidence is already mapped.  
Skip Claude if risk is minimal.  
Skip Codex if no execution is needed.

**Fixed 7-stage chain** is still available when explicitly requested.

---

## The Baton File

Every active cycle writes its state to:

```
/home/synczus/kestrel/active-baton.json
```

The agent currently holding the baton updates this file with their stage output before handing off. The next agent reads it to get full context.

**A completed cycle archives the baton to:**
```
/home/synczus/kestrel/batons/hop-{cycle_id}.json
```

---

## Universal Baton Schema

The canonical schema is at `/home/synczus/kestrel/shared-skills/hop-baton-schema.json`.  
Every agent MUST output valid JSON matching this schema when passing the baton.

**Required fields in every baton:**
- `cycle_id` — unique identifier for this hop cycle
- `protocol_version` — always `"4.0"`
- `current_agent` — who wrote this
- `stage` — what stage output this is
- `mission` — the work item, goal, and classification
- `state` — what changed and the evidence
- `facts`, `inferences`, `guesses_or_unverified` — separated
- `evidence` — array of {claim, evidence_type, source, quote, confidence}
- `blockers` — what's blocking
- `open_loops` — what's unresolved
- `agent_output` — the stage's actual findings
- `highest_leverage_move` — exactly one HLM
- `persistent_storage_update` — proposed changes
- `next_agent_routing` — who gets the baton next
- `termination_check` — should this cycle end early?

---

## Validation

Before handing off to the next agent, run:

```bash
python3 /home/synczus/kestrel/shared-skills/scripts/hop-baton-validator.py /home/synczus/kestrel/active-baton.json
```

This checks all required fields, evidence claims, and schema compliance.  
If validation fails, fix the baton before passing it.

---

## Agent Lanes (v4.0)

| Agent | Role | Can Do | Cannot Do |
|-------|------|--------|-----------|
| AI Hangout | Intake / Banking | Select work, merge outputs, commit storage, assign tasks | Invent completed work, skip blockers |
| Perplexity | Research | Cite external sources, kill stale claims | Execute locally, claim without evidence |
| Grok | Inversion | Attack assumptions, surface risks, detect drift | Claim unverified state, execute |
| Gemini | Scout | Map files/services/configs/logs, identify gaps | Execute patches, claim without evidence |
| Claude | Architect | Risk-rank, safe sequence, do-not-touch list | Execute, claim without evidence |
| Codex | Operator | Inspect, patch, verify, report proof | Broad unscoped edits, claim without proof |
| Kairos | Timing | Judge priority, flag stale loops | Reorder without rationale |
| Shannon | Signal Extractor | Compress chat, extract HLMs | Lose open loops |

---

## Storage Authority

Only AI Hangout Banking commits storage updates (master-todo.md, event-bus.md, memory).  
All other agents **propose** storage updates via the `persistent_storage_update` field.

---

## Kill Switch

If a hop cannot materially improve grounding, leverage, risk clarity, execution readiness, or routing precision:

```
termination_check.should_terminate = true
termination_check.route_to_banking = true
termination_check.reason = "why this hop adds no value"
```

Route directly to AI Hangout Banking for merge and reassignment.