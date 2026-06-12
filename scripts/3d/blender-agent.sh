#!/usr/bin/env bash
# Blender Headless Agent — starts Blender in background with MCP addon,
# connects the MCP server, and keeps the bridge alive.
# Use this when you want to build in Blender without the GUI.
set -e

PIDFILE_BLENDER="/tmp/blender-headless.pid"
PIDFILE_MCP="/tmp/blender-mcp.pid"
LOGFILE="/home/synczus/kestrel/logs/blender-agent.log"
BLEND_FILE="${1:-/tmp/blender_workspace.blend}"

mkdir -p "$(dirname "$LOGFILE")"

echo "🎬 Starting Blender headless agent..."
echo "   Socket: localhost:9876"
echo "   State:  $BLEND_FILE"
echo "   Log:    $LOGFILE"

# Kill any existing
for pidfile in "$PIDFILE_BLENDER" "$PIDFILE_MCP"; do
    if [[ -f "$pidfile" ]]; then
        kill $(cat "$pidfile") 2>/dev/null || true
        rm -f "$pidfile"
    fi
done

sleep 1

# Start Blender headless with the MCP addon enabled
flatpak run --command=blender org.blender.Blender \
    --background \
    --python-expr "
import bpy

# Enable the BlenderMCP addon
bpy.ops.preferences.addon_enable(module='blender_mcp')
print('BLENDER_MCP_ADDON_LOADED')

# Create default scene if starting fresh
if not bpy.data.objects:
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0,0,0))

print('BLENDER_HEADLESS_READY')
" \
    "$BLEND_FILE" \
    >> "$LOGFILE" 2>&1 &
echo $! > "$PIDFILE_BLENDER"

sleep 2

# Start MCP server
nohup uvx blender-mcp >> "$LOGFILE" 2>&1 &
echo $! > "$PIDFILE_MCP"

sleep 3

# Check if MCP connected
if kill -0 $(cat "$PIDFILE_MCP") 2>/dev/null; then
    echo ""
    echo "✅ Blender Agent is LIVE"
    echo "   Commands can now be sent via Blender MCP"
    echo ""
    echo "   To stop: kill $(cat $PIDFILE_BLENDER) $(cat $PIDFILE_MCP)"
    echo "   To reconnect Blender: open GUI, enable addon, click 'Connect'"
else
    echo "⚠️  MCP server started but couldn't connect to headless Blender."
    echo "   Blender will work as headless renderer."
    echo "   For interactive control, open Blender GUI → enable BlenderMCP → Connect"
fi

tail -3 "$LOGFILE" 2>/dev/null || true