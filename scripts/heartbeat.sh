#!/bin/bash
# Heartbeat writer — called by every cron to log its health
# Usage: heartbeat.sh <cron-name> [status]
# Example: heartbeat.sh thought-drop-voice-every-12h ok

set -euo pipefail

NAME="${1:-unknown}"
STATUS="${2:-ok}"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
HEARTBEAT_DIR="/home/synczus/kestrel/cron-health"

mkdir -p "$HEARTBEAT_DIR"

cat > "${HEARTBEAT_DIR}/${NAME}.heartbeat" <<HEARTBEAT
{
  "name": "${NAME}",
  "status": "${STATUS}",
  "last_run": "${TIMESTAMP}",
  "epoch": $(date +%s)
}
HEARTBEAT