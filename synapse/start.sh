#!/bin/bash
# Synapse — Launch the compound dashboard
# Usage: ./start.sh [port]
set -euo pipefail

PORT="${1:-19888}"
DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🪢 Synapse — Compound Dashboard"
echo "   Port:  $PORT"
echo "   Dir:   $DIR"
echo "   Open:  http://localhost:$PORT"
echo ""

# Check if running
if lsof -i :$PORT &>/dev/null 2>&1; then
    echo "⚠️  Port $PORT already in use — killing existing..."
    kill $(lsof -t -i :$PORT) 2>/dev/null || true
    sleep 1
fi

# Launch server
cd "$DIR"
SYNAPSE_PORT="$PORT" python3 server.py 2>&1 &

PID=$!
echo "✅ Synapse running (PID $PID)"
echo "   Kill with: kill $PID"

# Write PID for later management
echo "$PID" > "$DIR/synapse.pid"

# Auto-open browser
if [ -n "${DISPLAY:-}" ]; then
    sleep 1
    xdg-open "http://localhost:$PORT" 2>/dev/null || true
fi
