# Vote Execution Bridge Design

**Status:** Design Proposal | **Owner:** Hermes | **Priority:** P2

## Problem

The compound has a working voting system (propose → vote → tally → archive).
But votes produce decisions, not actions. After a vote passes, someone (Chase
or an agent) has to manually execute the outcome. The compound can decide but
can't do.

## Design

### Executive Actions

Attach an execution manifest to each vote at creation:
```
"execution": {
    "type": "terminal_cmd",  // or "file_edit", "cron_update", "api_call"
    "command": "systemctl --user restart kestrel-striker.service",
    "rollback": "systemctl --user stop kestrel-striker.service",
    "verify": "systemctl --user is-active kestrel-striker.service"
}
```

### Vote Tally → Execute Pipeline

When a vote reaches quorum:
1. Tally completes
2. If outcome is YES → execute the manifest's "command" field
3. Log result + verification to event-bus.md
4. Post to group: "🗳️ Vote passed + executed: <result>"

### Safety Gates

- All commands must be in an allowlist (no rm -rf, no sudo without approval)
- Rollback command must be defined for every execution
- Verification step must pass before marking Done
- Human override: If the command errors → route to Chase for manual review

## Implementation

1. Add `execution` field to vote schema (vote-board.json)
2. Modify tally script to run execution after quorum
3. Write allowlist of safe commands
4. Wire execution output → event-bus.md
5. Add execution history to dashboard

## Success Criteria

- Passed votes produce executed actions within 60 seconds of tally completion
- Rollback is possible for every execution
- Dashboard shows vote-to-execution pipeline status