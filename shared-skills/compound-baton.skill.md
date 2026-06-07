---
name: compound-baton
description: Shared file-based handoff system — agents pass work via baton-current.json instead of human clipboard
category: coordination
---

# Compound Baton Protocol

## Purpose

Replace manual copy-paste between browser tabs with a file-based handoff that agents can read/write autonomously on cron cycles.

## Directory Structure

```
/home/synczus/kestrel/baton/
├── baton-current.json       # Active baton — the current work item + next agent
├── work-queue/              # Pending work items (one file per item)
├── completed/               # Completed items with evidence
└── agent-inboxes/           # Per-agent async messages
    ├── hermes.json
    ├── openclaw.json
    ├── nemoclaw.json
    ├── kairos.json
    └── shannon.json
```

## Baton Lifecycle

1. **Any agent** writes a baton to `baton-current.json` with `next_agent_name` set
2. **Target agent's cron** reads `baton-current.json`, sees their name, picks up the work
3. **After processing**, the agent either:
   - Updates `baton-current.json` with a new `next_agent_name` (forward progress)
   - Moves it to `completed/YYYYMMDD-HHMMSS__descriptive-name.json` and clears `baton-current.json` (done)
   - Moves it to `blocked/` with a blocker note (stuck)
4. **Target agent's inbox** can also carry async messages that don't need a full baton

## baton-current.json Schema

```json
{
  "baton_id": "uuid-or-timestamp",
  "created_at": "2026-06-07T03:20:00-04:00",
  "updated_at": "2026-06-07T03:20:00-04:00",
  "created_by": "agent-name",
  "work_item": "Short description of the work",
  "goal": "What success looks like",
  "protocol_version": "4.0",
  "stage": "intake | research | inversion | scout | architect | execute | banking",
  "next_agent_name": "hermes | nemoclaw | openclaw | kairos | shannon",
  "next_agent_role": "what they need to do",
  "context": {
    "files_to_read": [],
    "files_to_write": [],
    "commands_to_run": [],
    "key_facts": [],
    "key_inferences": [],
    "blockers": [],
    "open_loops": []
  },
  "state": "pending | in_progress | completed | blocked",
  "completed_by": null,
  "evidence_path": null,
  "hlm": "The highest leverage move for this work"
}
```

## Agent Inbox Protocol

Each agent has a JSON file at `agent-inboxes/<agent>.json`. Other agents can write messages:

```json
{
  "messages": [
    {
      "from": "nemoclaw",
      "to": "kairos",
      "timestamp": "2026-06-07T03:20:00-04:00",
      "subject": "Striker health check needed",
      "body": "Can you verify Striker WS is still connected?",
      "priority": "normal | high | urgent",
      "requires_response": true,
      "read": false
    }
  ]
}
```

## Agent Startup Check

Every agent on boot/cron cycle should:

1. Read `baton/baton-current.json` — is my name `next_agent_name`?
   - Yes: process the baton
   - No: check my inbox
2. Read `baton/agent-inboxes/<my-name>.json`
   - Process messages, mark read
3. If nothing in either, proceed with normal routine

## Rules

- **One active baton at a time** — serial handoff, not parallel
- **Never overwrite another agent's baton** — check `state` field, if `in_progress` by someone else, wait
- **Baton must always have an HLM** — no work without leverage
- **Completed batons go to `completed/` with evidence** — proof or it didn't happen
- **Inboxes are async** — you don't need to reply immediately, but check them
- **Stale baton cleanup** — if a baton is `in_progress` for >30min, any agent can flag it as `stale`
