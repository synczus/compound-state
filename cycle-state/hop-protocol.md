# Hop Sequence Protocol

## File: `kestrel/cycle-state/hop-sequence.json`

Enables ordered agent-to-agent conversations in the group without Chase as trigger.

## Flow

1. **Chase says "scout X"** → I activate the hop, Kairos goes first
2. **Kairos sees message** → checks hop file, sees his turn → scouts, posts findings → updates `kairos_done: true`
3. **I see Kairos's post** → checks hop file, sees my turn → reads his findings, builds on them → posts result → updates `complete: true`
4. **Chase sees** the full chain: Kairos's scouting → my build

## Entry Rules

### OpenClaw (me):
- On every group message (any sender), check hop file
- If `active: true && openclaw_done: false && kairos_done: true` → it's my turn, respond
- If `active: true && openclaw_done: true` → hop already done, stay silent
- If `active: false` → normal mode (respond as usual)

### Kairos:
- On every group message from Chase or from me, check hop file
- If `active: true && kairos_done: false` → his turn, scout and respond
- If `active: true && kairos_done: true` → already done, stay silent

## Field Definitions

```json
{
  "active": true,
  "chain": ["kairos", "openclaw"],
  "current_step": 0,          // 0 = kairos, 1 = openclaw
  "query": "scout best MRR strategy for basis divergence signals",
  "requested_by": "Chase",
  "kairos_done": false,
  "openclaw_done": false,
  "kairos_message": "summary of what kairos found",
  "openclaw_message": "summary of build",
  "last_updated": "2026-06-07T15:36:00Z",
  "complete": false
}
```

## Activation

OpenClaw activates on "scout" or "hop" keywords, or on explicit Chase request.
Kairos never activates the hop — only responds when it's his turn.