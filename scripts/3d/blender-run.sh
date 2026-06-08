#!/usr/bin/env bash
# Blender runner — executes a Python script in Blender 5.1 (flatpak)
# Usage: blender-run.sh --script <path> [--render] [--output <path>]
set -e

SCRIPT=""
RENDER=false
OUTPUT_DIR="/home/synczus/gdrive/kestrel-notes/3d"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --script) SCRIPT="$2"; shift 2 ;;
        --render) RENDER=true; shift ;;
        --output) OUTPUT_DIR="$2"; shift 2 ;;
        *) echo "Unknown: $1"; exit 1 ;;
    esac
done

if [[ -z "$SCRIPT" ]]; then
    echo "Usage: blender-run.sh --script <path> [--render]"
    exit 1
fi

if [[ ! -f "$SCRIPT" ]]; then
    echo "Script not found: $SCRIPT"
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

echo "🎬 Blender build: $(basename "$SCRIPT")"
echo "   Engine: Cycles (path-traced)"
echo "   Output: $OUTPUT_DIR"

flatpak run --command=blender org.blender.Blender \
    --background \
    --python "$SCRIPT" \
    2>&1

EXIT=$?
if [[ $EXIT -eq 0 ]]; then
    echo "✅ Blender build complete"
else
    echo "❌ Blender build failed (exit $EXIT)"
    exit $EXIT
fi