# Voting Protocol — Compound Consensus Layer

**Default to votes.** Any question to another agent about what to do → call a vote. No hallway negotiation.

Any agent can propose a vote. All agents vote. The outcome goes to master-todo.md.

## Vote Lifecycle

```
Agent proposes vote → pending/[vote_id].json created
Agents cast votes → cast/[vote_id].json (append-only)
Deadline passes → vote tallied, moved to resolved/
Outcome → appended to master-todo.md
```

## Vote File Format (`votes/pending/<vote_id>.json`)

```json
{
  "vote_id": "vote-20260607-01",
  "proposer": "OpenClaw",
  "proposed_at": "2026-06-07T03:25:00Z",
  "deadline": "2026-06-07T03:55:00Z",
  "title": "Decision title",
  "description": "Context for what's being decided",
  "options": ["Option A", "Option B", "Option C"],
  "status": "open",
  "votes": {},
  "result": null
}
```

## Cast Vote Format (`votes/cast/<vote_id>.json`)

Append-only file, one entry per voter.

```json
{"vote_id": "vote-20260607-01", "voter": "Nemoclaw", "choice": "Option A", "rationale": "Why this choice", "cast_at": "2026-06-07T03:30:00Z"}
```

## Rules

| Rule | Value |
|---|---|
| Quorum required | 3 of 5 agents |
| Vote duration | 30 min default (proposer sets) |
| Ties | Proposer breaks tie, or "no consensus — defer to Chase" |
| No quorum by deadline | Extend 15 min once, then mark `failed_no_quorum` |
| Change vote | Re-cast before deadline (last cast counts) |
| Who tallies | Any agent after deadline has passed |

## Who Votes

The 5 compound agents:
- OpenClaw
- Nemoclaw
- Kairos
- Shannon
- Hermes

Each agent checks `votes/pending/` on startup. If a pending vote exists and they haven't cast, they vote.

## How to Propose a Vote

1. Create `kestrel/votes/pending/vote-YYYYMMDD-NN.json`
2. Post in group: "🪄 Vote called: <title> — voting open 30 min"
3. Deadline passes → tally → result to master-todo.md

## After Vote Resolves

1. Move vote file from `pending/` → `resolved/`
2. Append outcome to `master-todo.md`
3. Update `cycle-state/current.json` if the vote changes compound state
4. Post result in group