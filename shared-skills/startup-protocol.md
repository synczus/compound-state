# Shared Skill: Session Startup Protocol

## Every Agent — At Session Start

Before responding to any message, do this checklist:

### 1. Read the Event Bus
`/home/synczus/kestrel/event-bus.md`
- Check what other agents have done since your last session
- Note the last few rows — if something's in progress, factor it in

### 2. Read the Master Todo
`/home/synczus/kestrel/master-todo.md`
- Check if items assigned to you have changed
- Check if the board was updated by another agent

### 3. Read HUB_INTAKE
`/home/synczus/kestrel/HUB_INTAKE.md`
- Check pipeline state and noise gate decisions
- Factor in what was promoted/purged

### 4. Check Dialogue State
`/home/synczus/kestrel/dialogue-state.json`
- Only in AI Hangout group
- Check exchange counter before responding

### 5. Log Your Activity
After completing any task, append to `/home/synczus/kestrel/event-bus.md`:
```
| {time} | {agent} | {what you did} | ✅ Done |
```

### Why This Matters
Without this protocol, agents don't know:
- What other agents just did
- Whether the board changed
- Whether someone else already handled the request

Reading the event bus at startup is the single highest-ROI sync action you can take.