# Shared Skill: Squirrel Inbox — File Drop Handler

## When Anyone Drops a File in the Chat

1. Read the file contents
2. Save to `/home/synczus/kestrel/squirrel-inbox/` with format: `{timestamp}__{sender}__{description}.md`
3. Also copy to `/home/synczus/huntsystems/projects/archive-squirrel/data/raw/` for immediate pipeline ingestion
4. Log the ingestion on event-bus.md
5. Reply in chat with a one-line confirmation

## File Format for Saved Files

```markdown
# Squirrel Ingest — {timestamp}
**Source:** Telegram — {sender}
**File:** {original filename}
**Description:** {what it is}

---

{full file content}
```

## Why This Matters

Chase drops files in the group for immediate ingestion. This turns the Telegram chat into a direct pipeline input — no manual routing needed. The Archive Squirrel watches `data/raw/` and processes everything into the ChromaDB index automatically.