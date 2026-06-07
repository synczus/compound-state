# Universal Persistent Hop v3.3

**Mode:** manual multi-tab cycle
**Core Rule:** Every hop must pay rent. Truth first. Real goal second. Usefulness third.

**Cycle Order:** AI Hangout Intake → Perplexity → Grok → Gemini → Claude → Codex → AI Hangout Banking

## Shared Rules

- Stay in lane
- Separate facts, inference, and guesses
- Verify before stateful action
- Preserve all open loops
- Every output must include an HLM
- Every output must explicitly name the next agent
- Manual tabs are not parallel execution
- AI Hangout starts and ends every cycle

## Structured State (v3.3 Addition)

Every hop passes this JSON with the context packet:

```json
{
  "cycle_id": "",
  "protocol_version": "3.3",
  "current_agent": "",
  "previous_agent": "",
  "selected_work_item": "",
  "stage": "",
  "state_change": "none|progress|blocked|complete",
  "facts": [],
  "inferences": [],
  "guesses_or_unverified": [],
  "evidence": [],
  "blockers": [],
  "open_loops": [],
  "agent_output": {
    "summary": "",
    "key_findings": [],
    "risks": [],
    "recommendations": []
  },
  "highest_leverage_move": {
    "move": "",
    "why": "",
    "owner": "",
    "first_step": ""
  },
  "persistent_storage_update": {
    "should_store": true,
    "storage_targets": {
      "notes": [],
      "todo": [],
      "hlm_tracker": [],
      "open_loops": [],
      "decision_log": [],
      "evidence_log": []
    },
    "memory_summary": "",
    "do_not_store": []
  },
  "handoff_integrity_check": {
    "valid_json": true,
    "next_agent_present": true,
    "hlm_present": true,
    "storage_update_present": true,
    "state_claims_have_evidence": true
  },
  "next_agent_routing": {
    "next_agent_name": "",
    "next_agent_role": "",
    "reason_for_next_hop": "",
    "instruction_to_next_agent": "",
    "context_to_pass_forward": "",
    "fallback_if_rejected": "Return to AI Hangout Banking with invalid-hop note."
  }
}
```

## What v3.3 Adds

| Field | Why |
|---|---|
| `state_change` | Tracks whether the cycle is progressing, blocked, or complete |
| `facts vs inferences vs guesses` | Forces explicit separation of verified from assumed |
| `persistent_storage_update` | Pre-banks what needs to be saved before the banking stage |
| `handoff_integrity_check` | Self-validating handoff — if JSON is bad or fields missing, route back |
| `fallback_if_rejected` | Dead-simple circuit breaker: bad hop → back to banking for repair |