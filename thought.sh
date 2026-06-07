#!/bin/bash
# Kestrel Thought Inbox — dump a thought without interrupting
# Usage: thought "your random idea here"
# Saves to /home/synczus/inbox.md with timestamp + auto-indexes in ArchiveSquirrel

TIMESTAMP=$(date '+%Y-%m-%d %H:%M')
THOUGHT="$*"

if [ -z "$THOUGHT" ]; then
  echo "Usage: thought \"your idea here\""
  exit 1
fi

# Save to inbox file
echo "${TIMESTAMP} | ${THOUGHT}" >> /home/synczus/inbox.md

# Re-ingest to ArchiveSquirrel for searchability
curl -s -X POST "http://127.0.0.1:8766/ingest/path?path=/home/synczus/inbox.md" \
  -o /dev/null -w "%{http_code}" --max-time 5 2>/dev/null

echo "📥 Saved + indexed."