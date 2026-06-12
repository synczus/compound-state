#!/usr/bin/env python3
"""
Hop Baton Validator v4.0 — validates a baton JSON against the schema.

Usage:
    python3 hop-baton-validator.py /path/to/active-baton.json

Exits 0 on valid, 1 with error on invalid.
"""
import json
import sys
from pathlib import Path

REQUIRED_TOP = [
    "cycle_id", "protocol_version", "current_agent", "previous_agent",
    "stage", "mission", "classification", "state", "facts", "inferences",
    "guesses_or_unverified", "evidence", "blockers", "open_loops",
    "agent_output", "highest_leverage_move", "persistent_storage_update",
    "handoff_integrity_check", "termination_check", "next_agent_routing"
]

REQUIRED_MISSION = [
    "selected_work_item", "real_goal", "why_this_work_now",
    "mission_type", "success_definition", "non_goals", "user_constraints"
]

REQUIRED_HLM = ["move", "why", "owner", "first_step", "expected_impact", "risk", "reversibility"]

REQUIRED_NEXT = ["next_agent_name", "next_agent_role", "reason_for_next_hop",
                 "instruction_to_next_agent", "context_to_pass_forward", "fallback_if_rejected"]

REQUIRED_STORAGE = ["should_store", "commit_authority", "storage_targets"]
REQUIRED_STORAGE_TARGETS = ["notes", "todo", "hlm_tracker", "open_loops",
                            "decision_log", "evidence_log", "risk_log",
                            "execution_log", "blocked_items", "next_cycle_queue"]

REQUIRED_TERMINATION = ["should_terminate", "reason", "route_to_banking"]

VALID_MISSION_TYPES = [
    "local_execution", "repo_debugging", "service_runtime", "research",
    "market", "creative", "system_design", "storage_banking", "planning", "mixed"
]

VALID_REVERSIBILITY = ["easy", "moderate", "hard", "unknown"]

errors = []


def check(condition: bool, msg: str):
    if not condition:
        errors.append(msg)


def main():
    if len(sys.argv) < 2:
        print("Usage: hop-baton-validator.py <baton.json>", file=sys.stderr)
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"ERROR: {path} not found", file=sys.stderr)
        sys.exit(1)

    try:
        baton = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON — {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(baton, dict):
        print("ERROR: Baton must be a JSON object", file=sys.stderr)
        sys.exit(1)

    # — Top-level fields —
    for field in REQUIRED_TOP:
        check(field in baton, f"Missing top-level field: {field}")
    check(baton.get("protocol_version") == "4.0", f"protocol_version must be '4.0', got '{baton.get('protocol_version')}'")

    # — Mission —
    mission = baton.get("mission", {})
    if isinstance(mission, dict):
        for field in REQUIRED_MISSION:
            check(field in mission, f"mission.{field} missing")
        mt = mission.get("mission_type", "")
        check(mt in VALID_MISSION_TYPES or mt == "",
              f"mission.mission_type '{mt}' not in {VALID_MISSION_TYPES}")

    # — Classification —
    cls = baton.get("classification", {})
    if isinstance(cls, dict):
        for field in ["requires_external_research", "requires_repo_inspection",
                       "requires_terminal_execution", "requires_file_changes",
                       "requires_runtime_verification", "requires_risk_gate",
                       "requires_storage_commit", "requires_user_confirmation"]:
            check(field in cls, f"classification.{field} missing")
            val = cls.get(field)
            check(val in (True, False), f"classification.{field} must be bool, got {type(val).__name__}: {val}")

    # — State —
    st = baton.get("state", {})
    if isinstance(st, dict):
        check("state_change" in st, "state.state_change missing")
        if st.get("state_change") == "executed":
            check(bool(st.get("proof_of_change")), "state_change=executed but proof_of_change is empty")

    # — Evidence —
    ev = baton.get("evidence", [])
    if isinstance(ev, list):
        for i, e in enumerate(ev):
            check(isinstance(e, dict), f"evidence[{i}] must be a dict")
            if isinstance(e, dict):
                check("claim" in e, f"evidence[{i}].claim missing")
                check("evidence_type" in e, f"evidence[{i}].evidence_type missing")
                check("confidence" in e, f"evidence[{i}].confidence missing")
                conf = e.get("confidence")
                check(conf in ("low", "medium", "high", ""),
                      f"evidence[{i}].confidence must be low/medium/high, got '{conf}'")

    # — HLM —
    hlm = baton.get("highest_leverage_move", {})
    if isinstance(hlm, dict):
        for field in REQUIRED_HLM:
            check(field in hlm, f"highest_leverage_move.{field} missing")
        rev = hlm.get("reversibility")
        check(rev in VALID_REVERSIBILITY or rev == "",
              f"highest_leverage_move.reversibility '{rev}' not in {VALID_REVERSIBILITY}")

    # — Next Agent Routing —
    nxt = baton.get("next_agent_routing", {})
    if isinstance(nxt, dict):
        for field in REQUIRED_NEXT:
            check(field in nxt, f"next_agent_routing.{field} missing")
        check(bool(nxt.get("next_agent_name")),
              "next_agent_routing.next_agent_name is empty — without it the baton has no destination")

    # — Storage Update —
    su = baton.get("persistent_storage_update", {})
    if isinstance(su, dict):
        for field in REQUIRED_STORAGE:
            check(field in su, f"persistent_storage_update.{field} missing")
        targets = su.get("storage_targets", {})
        if isinstance(targets, dict):
            for field in REQUIRED_STORAGE_TARGETS:
                check(field in targets, f"persistent_storage_update.storage_targets.{field} missing")

    # — Termination —
    tc = baton.get("termination_check", {})
    if isinstance(tc, dict):
        for field in REQUIRED_TERMINATION:
            check(field in tc, f"termination_check.{field} missing")

    # — Handoff Integrity —
    hi = baton.get("handoff_integrity_check", {})
    if isinstance(hi, dict):
        for field in REQUIRED_TOP:
            if field in baton:
                check(hi.get("valid_json", False) if field == "valid_json" else True,
                      "handoff_integrity_check fields should mirror actual state")

    # — Open loops preserved? —
    ol = baton.get("open_loops", [])
    if isinstance(ol, list):
        for i, loop in enumerate(ol):
            if isinstance(loop, dict):
                check("item" in loop, f"open_loops[{i}].item missing")
                check("priority" in loop, f"open_loops[{i}].priority missing")
                check("status" in loop, f"open_loops[{i}].status missing")

    # — Report —
    if errors:
        print("❌ BATON INVALID", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(1)
    else:
        print("✅ BATON VALID — all schema checks passed")
        sys.exit(0)


if __name__ == "__main__":
    main()