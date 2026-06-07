# Shared Skill: Proposition Writing

## When to Write a Proposition
When you have a highest-leverage move idea that should go on the board.

## Where to Write
1. **master-todo.md** — add to the Open Items section: `- [ ] YYYY-MM-DD | YourName | Your proposition text`
2. **memory-bank input** — write a file to your agent's input dir:
   - `/home/synczus/kestrel/memory-bank/input/[agent-name]/proposition_<topic>.md`
   - Format:
     ```
     # Proposition: <title>
     
     - [ ] <proposition text>
     
     _Source: [agent-name], time: <timestamp>_
     ```

## HLM Format in Messages
End every response with:
```
highest leverage move: <one sentence describing the single most impactful next action>
```

If you don't have a strong HLM:
```
HLM: none — awaiting direction.
```

## Collection Pipeline
Archive Squirrel consolidates memory-bank every 15 min. HLM cron sweeps every 6h. Your proposition will be collected automatically — just write it.