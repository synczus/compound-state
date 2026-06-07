# Skill: todo-extraction

Scrape the most recent Telegram group messages for "Highest-leverage move:" lines and append them to the master todo.

## Requirements

- Read access to the Telegram group transcript (via logs or session files)
- Write access to `/home/synczus/kestrel/master-todo.md`
- A cron to run every N minutes

## Implementation

1. Periodically scan the last N messages in the AI Hangout group
2. Match lines following the pattern: `**Highest-leverage move:**` or `Highest-leverage move:`
3. For each match, extract the text after the colon
4. Append to `/home/synczus/kestrel/master-todo.md` in format:
   ```
   - [ ] 2026-06-06 | <agent-name> | <extracted text>
   ```
5. Deduplicate — skip entries already in the todo

## Alternative Method (If Cron Available)

If hermes or another cron system can periodically inject into the group, the extraction can happen server-side:

1. Heres a simple bash approach:
   ```bash
   grep -r "Highest-leverage move:" /home/synczus/.hermes/logs/ 2>/dev/null | \
     while read line; do
       agent=$(echo "$line" | grep -oP 'agent/[^/]+' || echo "unknown")
       move=$(echo "$line" | grep -oP 'Highest-leverage move:\s*\K.*')
       echo "- [ ] $(date +%Y-%m-%d) | $agent | $move" >> /home/synczus/kestrel/master-todo.md
     done
   ```

## Verification

- After a few messages with highest-leverage moves, check master-todo.md for new entries
- No duplicates
- Entries are properly formatted