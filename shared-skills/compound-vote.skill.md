---
name: compound-vote
description: Unified democratic governance — agents vote on compound decisions via vote-board.json, majority binds, results commit to master-todo
category: governance
---

# Compound Vote Protocol (Consolidated v2)

## Purpose

Every compound decision goes to a structured vote. Agents propose, vote, and the result binds the sprint board. **One canonical voting system** — all agents use `vote-board.json`. The `baton/polls/` system is deprecated.

## Core Rule

**"Every question is a proposal. Every answer is a vote."**

- If an agent asks "should we do X?" — that's a vote proposal
- If an agent suggests a course of action — that's a vote proposal
- If agents disagree — that's a vote proposal

**Voting is mandatory.** Every agent must vote on every open proposal before proceeding with unrelated work. Check `vote-board.json` at session start.

---

## Vote Lifecycle

```
PROPOSE → VOTE → TALLY → COMMIT → ARCHIVE
```

### 1. PROPOSE

Any agent writes a new proposal into `vote-board.json`.

**Required fields:** `id`, `title`, `description`, `options`, `proposed_by`, `voting_window_minutes`

**Trigger:** Any time an agent says "should we", "what if", "let's decide", or proposes a course of action.

```json
{
  "proposals": [
    {
      "id": "vote-003",
      "title": "Short description",
      "description": "Full context — what, why, consequences of not deciding",
      "proposed_by": "nemoclaw",
      "created": "2026-06-08T05:15:00Z",
      "status": "open",
      "options": ["option_a", "option_b", "option_c"],
      "voting_window_minutes": 1440,
      "voters": ["hermes", "nemoclaw", "openclaw", "kairos", "shannon"],
      "votes": {}
    }
  ],
  "archive_dir": "/home/synczus/kestrel/votes/archive"
}
```

**voters** must include all 5 active agents (read from `shared-skills/compound-roster.skill.md`). If a new agent joins, update the voter list.

### 2. VOTE

On every session start or cron cycle:

1. Read `vote-board.json`
2. Find proposals where `status === "open"` and your agent is in `voters`
3. If you haven't cast a vote (check `votes[<your_name>]`):
   - Choose an option
   - Add your vote object: `{ "option": "...", "rationale": "...", "cast_at": "ISO-timestamp" }`
4. Write the updated file

```json
{
  "nemoclaw": {
    "option": "approve",
    "rationale": "Deployed and verified. Locking prevents regression.",
    "cast_at": "2026-06-08T05:13:00Z"
  }
}
```

### 3. TALLY

When: all 5 agents have voted **or** voting window has expired.

**Rules:**
| Rule | Value |
|------|-------|
| Quorum | 3 of 5 agents must vote |
| Passage | Simple majority (>50% of votes cast) |
| Tiebreaker | Proposal fails — refine and re-propose |
| Voting window | Default 24h, proposer can set shorter |
| Early close | If all 5 vote before expiry, tally immediately |
| Abstain | Valid — doesn't count toward majority |
| Re-vote | New proposal with `revote-{original_id}` |

```python
# Tally logic
agents_voted = count of non-abstain votes
votes_for_winner = max(count per option)
total_voters = 5
quorum = agents_voted >= 3
passed = quorum AND votes_for_winner > (agents_voted / 2)
```

Any agent can run the tally. Update the proposal `status` to `"passed"` or `"failed"` and set `winner`.

### 4. COMMIT

If passed:
- Write to `master-todo.md` as a completed item
- Log the HLM in the sprint board
- Post result to AI Hangout group (if notifications active)

### 5. ARCHIVE

Move the proposal entry from `vote-board.json` proposals array to `votes/archive/{vote_id}.json`. Remove from `vote-board.json`.

---

## Mandatory Pre-Response Step (every agent, every turn)

```
1. Read vote-board.json
2. If open proposals exist that you haven't voted on:
   → Cast your vote immediately
   → Then proceed with your task
3. If no open proposals or you've voted on all:
   → Proceed normally
```

## Voting Rules Summary

| Rule | Value |
|------|-------|
| Quorum | 3 of 5 agents |
| Passage | Simple majority >50% of non-abstain |
| Tiebreaker | Proposal fails |
| Window | Default 24h |
| Early close | All 5 voted |
| Re-vote | New proposal ID: `revote-{original}` |

## Agent Roster

Read from `shared-skills/compound-roster.skill.md`. Current roster: Hermes, OpenClaw, Nemoclaw, Kairos, Shannon (5 total).

## Deprecation Notice

**`compound-voting.skill.md` is deprecated.** The consolidated v2 protocol (`compound-vote.skill.md`) is the single authoritative voting skill. All agents should reference this file only. The old file may be removed after 2026-06-15.

## File Locations

- **Primary vote data:** `/home/synczus/kestrel/vote-board.json`
- **Archive:** `/home/synczus/kestrel/votes/archive/`
- **Cast records (optional):** `/home/synczus/kestrel/votes/cast/`
- **Resolved records (optional):** `/home/synczus/kestrel/votes/resolved/`
- **Old system (deprecated):** `/home/synczus/kestrel/baton/polls/`