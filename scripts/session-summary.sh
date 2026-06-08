#!/usr/bin/env bash
# session-summary.sh — warm memory layer for per-agent session continuity
# Called at session start + end to create/edit session summaries.

ACTION="${1:-read}"
AGENT="${2:-openclaw}"
SESSION_DIR="/home/synczus/kestrel/memory-bank/warm"

mkdir -p "$SESSION_DIR"

case "$ACTION" in
  read)
    FILE="$SESSION_DIR/$AGENT.md"
    if [ -f "$FILE" ]; then
      echo "=== $AGENT session summary ==="
      cat "$FILE"
      echo "=== end ==="
    else
      echo "No active session for $AGENT"
      exit 0
    fi
    ;;
  write)
    echo "$3" > "$SESSION_DIR/$AGENT.md"
    echo "Session summary updated for $AGENT"
    ;;
  append)
    echo "$3" >> "$SESSION_DIR/$AGENT.md"
    echo "Session summary appended for $AGENT"
    ;;
  clear)
    rm -f "$SESSION_DIR/$AGENT.md"
    echo "Session summary cleared for $AGENT"
    ;;
  *)
    echo "Usage: $0 {read|write|append|clear} [agent] [content]"
    echo ""
    echo "  read   - Show current session summary for agent"
    echo "  write  - Overwrite session summary (full replacement)"
    echo "  append - Add a line to session summary"
    echo "  clear  - Delete session summary (session end)"
    exit 1
    ;;
esac
