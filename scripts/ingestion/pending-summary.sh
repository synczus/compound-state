#!/usr/bin/env bash
# Pending Summary — quick CLI view of what's waiting
# Usage: bash scripts/pending-summary.sh
set -euo pipefail

KESTREL_ROOT="/home/synczus/kestrel"

echo "╔══════════════════════════════════════╗"
echo "║     📋 PENDING QUEUE SUMMARY        ║"
echo "╚══════════════════════════════════════╝"
echo ""

# Count signals by lane
echo "── Signals ──"
if [ -f "$KESTREL_ROOT/signals.md" ]; then
  Q=$(grep -c '"queue"' "$KESTREL_ROOT/signals.md" 2>/dev/null || echo 0)
  U=$(grep -c '"urgent"' "$KESTREL_ROOT/signals.md" 2>/dev/null || echo 0)
  H=$(grep -c '"high_signal"' "$KESTREL_ROOT/signals.md" 2>/dev/null || echo 0)
  M=$(grep -c '"medium_signal"' "$KESTREL_ROOT/signals.md" 2>/dev/null || echo 0)
  TOTAL=$((Q + U + H + M))
  echo "  Total: $TOTAL"
  echo "  ⏳ Queued:   $Q (needs human review)"
  echo "  🚨 Urgent:   $U"
  echo "  🔵 High:     $H"
  echo "  🟣 Medium:   $M"
  
  # Show a sample queued item
  if [ "$Q" -gt 0 ]; then
    echo ""
    echo "  Oldest queued:"
    grep '"queue"' "$KESTREL_ROOT/signals.md" 2>/dev/null | head -1 | python3 -c "
import sys, json
try:
    d = json.loads(sys.stdin.readline())
    print(f'    [{d.get(\"source_id\",\"?\")}] {d.get(\"headline\",\"\")[:100]}')
except:
    pass
" 2>/dev/null
  fi
else
  echo "  No signal log yet"
fi

echo ""
echo "── To-Dos ──"
PENDING=$(grep -c '\[ \]' "$KESTREL_ROOT/master-todo.md" 2>/dev/null || echo 0)
echo "  $PENDING items pending"
if [ "$PENDING" -gt 0 ]; then
  echo ""
  grep '\- \[ \]' "$KESTREL_ROOT/master-todo.md" | head -5 | while read -r line; do
    echo "  • ${line:6}"
  done
  if [ "$PENDING" -gt 5 ]; then
    echo "  ... and $(($PENDING - 5)) more"
  fi
fi

echo ""
echo "── Next Ingestion Pulse ──"
NEXT=$(date -d "@$(($(date +%s) + 1800 - $(date +%s) % 1800))" '+%H:%M:%S' 2>/dev/null || echo "~30 min")
echo "  Next check at $NEXT"
echo ""
echo "  Web dashboard: http://localhost:19888"