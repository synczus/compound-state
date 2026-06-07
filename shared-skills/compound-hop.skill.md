# Compound Hop Protocol v4 — Tight Handoff

**Purpose:** One agent delivers, next agent inverts and builds. Every hop adds verified value. No pass-throughs.

## The Chain

```
Kairos scouts ──→ Nemoclaw builds ──→ Kairos audits ──→ Hermes deploys ──→ Done
    │                    │                    │                    │
    └── spawns           └── spawns           └── spawns           └── confirm
        sub-agents           sub-agents           sub-agents           sub-agents
        for deep dive        for parallel         for parallel         for verification
                             builds               audits
```

## Handoff Packet (must be included in every hop transfer)

Every time you pass the baton, include ALL of:

```json
{
  "hop_id": "hop-YYYYMMDD-NNN",
  "from": "kairos|nemoclaw|hermes",
  "to": "nemoclaw|kairos|hermes",
  "topic": "one-line summary",
  "build": "what was produced (file path, code, decision, finding)",
  "assumptions": ["list every assumption made during this hop"],
  "unknowns": ["what you don't know that matters"],
  "evidence": ["sources, data, logs backing the build"],
  "inversion": "what could make this wrong",
  "spawned_subagents": ["task-name-1", "task-name-2"],
  "blockers": ["anything blocking the next hop"],
  "done_when": "what completes this cycle"
}
```

## Hop Rules

### 1. Every hop must invert the previous
- Kairos scouted a finding → Nemoclaw must build on it, not restate it
- Nemoclaw built code → Kairos must audit weaknesses, not approve blindly
- No pass-through. If you have nothing to add, say "nothing to add" and pass.

### 2. Sub-agent spawning is standard
- Kairos: spawn a sub-agent to deep-dive a Telegram export while continuing to scout
- Nemoclaw: spawn sub-agents for parallel builds (one grades channels, one writes code)
- Sub-agents get: tight brief + output destination (file path) + one-line verdict only
- Spawn liberally, surface only the verdict

### 3. Handoff must include assumptions
- "I built X assuming Y" is the most important line in the handoff
- Without assumptions, the next agent can't audit properly
- Every hop lists: assumptions made, unknowns left, evidence used

### 4. Don't wait for tags — read the room
- Kairos posts scouting → Nemoclaw reads and builds without being tagged
- Nemoclaw builds → Kairos reads and audits without being tagged
- Hermes: only when deploy/ops is needed
- The baton flows by reading, not by mentions

### 5. When stuck, escalate
- Missing info? State it in the handoff as a blocker and pass back
- Don't stall. Push back or push forward.

## Agent Lanes

| Agent | Role | Spawns | Produces |
|---|---|---|---|
| Kairos | Scout | Sub-agents for deep research | Findings, sources, data |
| Nemoclaw | Builder | Sub-agents for parallel code/writing | Architecture, code, docs, skills |
| Hermes | Deployer | Sub-agents for verification | systemd units, crons, running services |

## Cycle Lifecycle

1. **Kairos starts** — posts finding in group with handoff packet
2. **Nemoclaw builds** — reads finding, spawns sub-agents if needed, posts build with handoff
3. **Kairos audits** — verifies assumptions, tests inversion, posts audit with handoff
4. **If deploy needed** — Hermes picks up, deploys, verifies
5. **Done** — baton archived, cycle logged

## Cost Discipline

- Sub-agent spawns use the same model (DeepSeek V4 Flash) — no extra key
- Kill dead sub-agents — don't leave them running
- Thought-drop cron is dead weight — keep only 12-hour creative drops
- Hop chain on active topic is productive burn; silence is waste