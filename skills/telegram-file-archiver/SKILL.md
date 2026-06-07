# Skill: telegram-file-archiver

Automatically archive every file/document posted to the AI Hangout Telegram group. Saves to a dated inbox directory and logs metadata for the swarm briefing.

## Implementation

1. A cron runs every 5 minutes scanning the last N Telegram messages for file attachments
2. When a file is detected (PDF, image, document, code snippet):
   - Copy it to `/home/synczus/kestrel/inbox/<YYYY-MM-DD>/`
   - Log metadata: filename, sender, timestamp, message_id
   - Update a running index file so agents can find it later
3. The archiver does NOT parse or summarize the file — that's an agent's job when they read it
4. Duplicate filenames get a timestamp suffix

## Script

The archiver script should:
```bash
#!/usr/bin/env bash
# archive-group-files.sh
# Poll Telegram for recent file attachments and stash them

INBOX_DIR="/home/synczus/kestrel/inbox/$(date +%Y-%m-%d)"
mkdir -p "$INBOX_DIR"

# Get recent messages from Telegram group
# Check for documents/photos/files via the Telegram API
# curl -s "https://api.telegram.org/bot$TOKEN/getUpdates" | \
#   jq '.result[] | select(.message.document != null)' | \
#   while read msg; do
#     file_id=$(echo "$msg" | jq -r '.message.document.file_id')
#     filename=$(echo "$msg" | jq -r '.message.document.file_name')
#     curl -o "$INBOX_DIR/$filename" \
#       "https://api.telegram.org/bot$TOKEN/getFile?file_id=$file_id"
#   done
```

## Verification

- Drop a file in the group
- Wait 5 minutes
- Check `/home/synczus/kestrel/inbox/` for the dated directory and file copy

## Note

This skill currently has a placeholder implementation. The full script needs:
- The correct bot token (which one polls the group?)
- jq for JSON parsing on the Telegram getUpdates response
- Deduplication and error handling