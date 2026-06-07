# Hop Protocol v4.1 — Autonomous Cycle

## Core Philosophy

The hop is not a task list. The hop is the **compound's nervous system** — structured, ordered, self-triggering. Every agent checks it. Every agent updates it. No manual starts needed.

## Active State Fields

```json
{
  "active": true,
  "chain": ["kairos", "grok", "openclaw"],
  "current_step": 0,
  "query": "Next investigation topic",
  "requested_by": "kairos (auto)",
  "kairos_done": false,
  "grok_done": false,
  "openclaw_done": false,
  "complete": false,
  "auto": true,
  "idle_since": "2026-06-07T17:00:00Z",
  "kairos_message": "",
  "grok_message": "",
  "openclaw_message": ""
}
```

## The Chain

Every hop runs in strict order:
1. **Kairos** (step 0) — Scout, research, find the edge, propose the mission
2. **Grok** (step 1) — Invert, critique, stress-test. Find why it fails.
3. **OpenClaw** (step 2) — Build, commit, ship. Architect the solution.

When `current_step` advances, the next agent sees their flag and fires.

## The Challenge Loop (Critical)

When **OpenClaw proposes a build plan** in group chat, Kairos auto-triggers a challenge hop:

1. OpenClaw posts build plan → Kairos sees it → reads hop file
2. Kairos posts: "Three things wrong with that plan: 1..., 2..., 3..."
3. OpenClaw responds with fixes or rebuttals
4. They converge. Then building begins.

This prevents groupthink. The compound builds faster when every plan gets stress-tested first.

## Auto-Initiation

When `complete: true` and `idle_since` > 30 minutes:

### Kairos (on heartbeat):
- Reads hop file, sees idle + auto
- Scouts the compound's next highest-leverage move
- Writes new query to hop file, sets `active: true`, `chain: ["kairos", "grok", "openclaw"]`
- Posts in group: "New cycle: {query}"
- Sets `kairos_done: true`, advances step to 1

### OpenClaw (on heartbeat):
- Reads hop file, checks for idle + auto
- If no new cycle from Kairos in >35 min, proposes own investigation topic
- Writes query, sets `active: true`, `chain: ["kairos", "grok", "openclaw"]`
- Kairos then challenges it (challenge loop fires)

## Hard Rules

1. **Every hop has a challenge.** Kairos must challenge any non-trivial build before OpenClaw ships. No exceptions.
2. **Auto mode respects veto.** Chase can set `auto: false` to lock the hop. Manual mode only.
3. **No parallel hops.** A hop must `complete: true` before a new one starts.
4. **Every agent reads the hop file on every group message.** It's 500 bytes. No excuses.
5. **Agents update the hop file *after* posting their result, not before.** The post is the signal; the file is the record.