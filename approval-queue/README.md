# Approval Gate

Operations that cost >$5 or delete infrastructure are queued here.
Chase approves/rejects via message reaction or chat command.

## How it works:
1. Agent writes `.pending.json` with cost, risk, and operation summary
2. Posts to AI Hangout: "⚡ Approval needed: <operation> ($X)"
3. Chase approves: file becomes `.approved.json`, agent executes
4. Chase rejects: file becomes `.rejected.json`, agent drops it
5. Auto-expire: pending >24h become `.stale.json`

## Current format:
```json
{
  "id": "approval-YYYYMMDD-HHMM",
  "agent": "who_requested",
  "operation": "what to do",
  "cost": 0.0,
  "risk": "low|medium|high",
  "justification": "why this matters",
  "created": "ISO timestamp",
  "status": "pending|approved|rejected|stale"
}
```
