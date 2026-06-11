#!/bin/bash
# agentmemory startup script - survives restarts
# Runs agentmemory server in background

export PATH="/home/synczus/.npm-global/bin:$PATH"
export HOME="/home/synczus"

PIDFILE="$HOME/.agentmemory/pidfile"
PID=$(cat "$PIDFILE" 2>/dev/null)

# Check if already running
if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
    echo "agentmemory already running (PID $PID)"
    exit 0
fi

# Start it
nohup agentmemory > "$HOME/.agentmemory/server.log" 2>&1 &
echo "Started agentmemory (PID $!)"