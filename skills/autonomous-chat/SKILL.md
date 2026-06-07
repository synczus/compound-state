# Skill: autonomous-chat

Set up a cron job that drops a provocation into the Telegram group every N minutes. Each cycle **must produce at least one concrete update to master-todo.md** or a clear decision to do nothing. No empty cycles.

## Requirements

- Access to hermes cron (or equivalent cron system)
- A list of provocation sources (pipeline signals, todo items, market data, random prompts)
- Telegram home channel set for the agent running the cron

## Core Rule (Non-Negotiable)

**Every cycle must produce one of:**
1. A new item added to `/home/synczus/kestrel/master-todo.md` with lane assignment
2. An existing todo item marked done with a pulse written
3. A clear decision to do nothing (logged as a pulse file)

No cycle is allowed to produce only conversation. If no work is available, the first agent to respond must explicitly state "Nothing actionable this cycle" and stop.

## Implementation

1. Create a cron job that runs every 5 minutes
2. The job picks one item from:
   - A promoted signal from the noise gate
   - A random incomplete item from `/home/synczus/kestrel/master-todo.md`
   - Market data (BTC/ETH/SOL price + Fear & Greed)
   - A random topic from the provocation list in the pulse script
3. The cron posts the item to the Telegram group chat (-5087043705)
4. Agents in the group respond with their highest-leverage move
5. The **last agent to respond** is responsible for updating master-todo.md with the cycle's output
6. Cycle limit: 4 exchanges maximum, then reset

## Sample Cron Config

For hermes:
```
cron add --name swarm-pulse --schedule.kind "every" --schedule.everyMs 300000 --payload.kind "systemEvent" --payload.text "Autonomous pulse: <provocation>"
```

## Output Enforcement

The pulse script includes a post-cycle check:
- If 5 minutes pass and no master-todo.md update was detected, the next pulse should explicitly demand: "Last cycle produced no output. Someone update master-todo.md or declare nothing actionable."

## Verification

- After 3 consecutive cycles, master-todo.md has been updated at least 2 times
- No cycle produces pure conversation without output
- The group naturally stops within 4 exchanges
- Pulses are spaced at least 5 minutes apart