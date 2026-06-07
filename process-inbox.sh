#!/bin/bash
# Process the Kestrel thought inbox — categorize and organize
# Run: bash /home/synczus/kestrel/process-inbox.sh

INBOX="/home/synczus/inbox.md"
ARCHIVE="/home/synczus/inbox-archive.md"

if [ ! -f "$INBOX" ] || [ ! -s "$INBOX" ]; then
  echo "📭 Inbox is empty."
  exit 0
fi

COUNT=$(grep -c "^20" "$INBOX" 2>/dev/null || echo "0")
echo "📥 Processing $COUNT thoughts..."
echo ""
echo "═══════════════════════════════════════════"
echo "  THOUGHT INBOX"
echo "═══════════════════════════════════════════"
cat "$INBOX"
echo ""
echo "═══════════════════════════════════════════"

# Ask what to do with them
echo ""
echo "Actions:"
echo "  1. Keep as-is (already organized)"
echo "  2. Clear and archive to inbox-archive.md"
echo ""
read -p "Choose (1/2): " choice

if [ "$choice" = "2" ]; then
  cat "$INBOX" >> "$ARCHIVE"
  echo "" >> "$ARCHIVE"
  echo "--- Batch processed at $(date) ---" >> "$ARCHIVE"
  > "$INBOX"
  echo "✅ Inbox cleared. Archived to $ARCHIVE"
else
  echo "✅ Inbox preserved."
fi