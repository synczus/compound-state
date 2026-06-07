# Compound Hop Protocol — Lean Chain

**Purpose:** One agent speaks at a time. Pass the baton. Build on the last response.

## The Chain

```
Nemoclaw → Kairos → (back to Nemoclaw if needed) → Done
```

## How It Works

1. **Incoming message** — whoever's lane it is grabs it first
2. **Response** — answers + builds the baton
3. **Pass** — explicitly names the next agent
4. **Next agent** — reads the baton, builds on what was said, passes again
5. **Done** — no more passes needed, baton goes to archive

## Baton Current (written to `baton/baton-current.json`)

```json
{
  "cycle_id": "trade-hop-YYYYMMDD-NNN",
  "active": true,
  "current_holder": "nemoclaw",
  "previous_holder": null,
  "topic": "trading pipeline architecture",
  "context": "what's been said so far (1-2 sentences)",
  "build_on": "what the previous agent added that needs extension",
  "next": "kairos",
  "done_when": "what completes this cycle"
}
```

## Who Grabs What

| Message Type | Grabber | Why |
|---|---|---|
| Architecture/design/infra questions | Nemoclaw | Identity lane |
| Pipeline, risk, ops, security | Kairos | Timing/Ops lane |
| Strategy performance | Nemoclaw → Kairos | Both: Nemoclaw builds, Kairos audits |
| Budget/timing questions | Kairos | Cadence lane |
| Long-term vision | Nemoclaw | Identity lane |

## Rules

1. **Read baton-current.json before responding** — know who holds it
2. **If you don't hold the baton, stay silent** — unless tagged directly
3. **When you respond, update the baton** and pass to the next agent
4. **If you're tagged directly**, you can respond even if you don't hold the baton (resets the chain)
5. **End your response with @next-agent** so they know it's their turn

## For The Trading Pipeline (current cycle)

**Cycle:** Nemoclaw designs the architecture → moves to implementation → Kairos audits risk and timing → back to Nemoclaw for execution wiring → Done