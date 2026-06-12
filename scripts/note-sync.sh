#!/usr/bin/env bash
# Sync shared-knowledge/notes to Google Drive
# Used by cron (every 5min) and by note-intake on write

set -euo pipefail

NOTES_DIR="/home/synczus/kestrel/shared-knowledge/notes"
RCLONE_REMOTE="gdrive:compound-notes"

# Only sync if notes directory exists and has files
if [ ! -d "$NOTES_DIR" ]; then
    echo "NO_NOTES_DIR"
    exit 0
fi

# Check rclone can reach drive (cached auth)
rclone lsd gdrive: >/dev/null 2>&1 || {
    echo "RCLONE_AUTH_FAILED"
    exit 1
}

# Copy new/changed files
rclone copy "$NOTES_DIR" "$RCLONE_REMOTE" --no-traverse 2>&1
RESULT=$?

if [ $RESULT -eq 0 ]; then
    COUNT=$(find "$NOTES_DIR" -type f -name "*.md" 2>/dev/null | wc -l)
    echo "SYNC_OK: ${COUNT} notes on Drive"
else
    echo "SYNC_FAILED: exit=${RESULT}"
    exit $RESULT
fi