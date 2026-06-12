#!/usr/bin/env bash
# Blender MCP Server — connects LLM agents to a running Blender instance
# Requires: Blender 5.1+ with BlenderMCP addon enabled
# Usage:
#   blender-mcp.sh start     # Start MCP server in background
#   blender-mcp.sh stop      # Stop MCP server
#   blender-mcp.sh status    # Check if server is running
set -e

ACTION="${1:-status}"
PIDFILE="/tmp/blender-mcp.pid"
LOGFILE="/home/synczus/kestrel/logs/blender-mcp.log"

case "$ACTION" in
    start)
        if [[ -f "$PIDFILE" ]] && kill -0 $(cat "$PIDFILE") 2>/dev/null; then
            echo "✅ Blender MCP already running (PID $(cat $PIDFILE))"
            exit 0
        fi
        mkdir -p "$(dirname "$LOGFILE")"
        echo "🔧 Starting Blender MCP server..."
        nohup uvx blender-mcp > "$LOGFILE" 2>&1 &
        echo $! > "$PIDFILE"
        # Wait for it to initialize
        sleep 3
        if kill -0 $(cat "$PIDFILE") 2>/dev/null; then
            echo "✅ Blender MCP started (PID $(cat $PIDFILE))"
            echo "   Log: $LOGFILE"
        else
            echo "❌ Blender MCP failed to start"
            tail -5 "$LOGFILE"
            exit 1
        fi
        ;;
    stop)
        if [[ ! -f "$PIDFILE" ]]; then
            echo "ℹ️  Blender MCP not running"
            exit 0
        fi
        PID=$(cat "$PIDFILE")
        kill "$PID" 2>/dev/null || true
        rm -f "$PIDFILE"
        echo "✅ Blender MCP stopped"
        ;;
    status)
        if [[ -f "$PIDFILE" ]] && kill -0 $(cat "$PIDFILE") 2>/dev/null; then
            echo "✅ Blender MCP running (PID $(cat $PIDFILE))"
            echo "   Log tail:"
            tail -3 "$LOGFILE" 2>/dev/null || echo "   (no log)"
        else
            echo "❌ Blender MCP not running"
            rm -f "$PIDFILE" 2>/dev/null || true
        fi
        ;;
    *)
        echo "Usage: blender-mcp.sh {start|stop|status}"
        exit 1
        ;;
esac