#!/bin/bash
# gdrive-sync — push compound data to Google Drive
# Runs via Hermes cron every 6h (or manual trigger)
# Uses rclone's existing gdrive remote

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TIMESTAMP=$(date -u +%Y%m%d-%H%M%S)
LOG_DIR="$SCRIPT_DIR/../logs/gdrive"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/sync-${TIMESTAMP}.log"

echo "=== GDrive Sync $(date -u) ===" | tee -a "$LOG"

# 1. Compound core — identity, state, scripts, configs
echo "Syncing kestrel/identities..." | tee -a "$LOG"
rclone sync /home/synczus/kestrel/identity gdrive:compound-notes/identity/ \
  --exclude "*.log" --exclude "*.tmp" --exclude ".git*" \
  --log-file "$LOG" --log-level INFO 2>&1 | tail -3

echo "Syncing kestrel/scripts..." | tee -a "$LOG"  
rclone sync /home/synczus/kestrel/scripts gdrive:compound-notes/scripts/ \
  --exclude "*.log" --exclude "*.tmp" --exclude ".git*" --exclude "venv" \
  --exclude "__pycache__" \
  --log-file "$LOG" --log-level INFO 2>&1 | tail -3

echo "Syncing kestrel/cycle-state..." | tee -a "$LOG"
rclone sync /home/synczus/kestrel/cycle-state gdrive:compound-notes/cycle-state/ \
  --exclude "*.log" --log-file "$LOG" --log-level INFO 2>&1 | tail -3

echo "Syncing kestrel/staging..." | tee -a "$LOG"
rclone sync /home/synczus/kestrel/staging gdrive:compound-notes/staging/ \
  --log-file "$LOG" --log-level INFO 2>&1 | tail -3

echo "Syncing kestrel/dashboard..." | tee -a "$LOG"
rclone sync /home/synczus/kestrel/dashboard gdrive:compound-notes/dashboard/ \
  --log-file "$LOG" --log-level INFO 2>&1 | tail -3

# 2. Fast-file-signals DuckDB (compressed)
echo "Syncing DuckDB signals..." | tee -a "$LOG"
if [ -f /home/synczus/kestrel/signals.duckdb ]; then
  rclone copy /home/synczus/kestrel/signals.duckdb gdrive:compound-notes/data/ \
    --log-file "$LOG" --log-level INFO 2>&1 | tail -3
  # Also compress for faster transfer
  gzip -c /home/synczus/kestrel/signals.duckdb > /tmp/signals-${TIMESTAMP}.duckdb.gz 2>/dev/null
  rclone copy /tmp/signals-${TIMESTAMP}.duckdb.gz gdrive:compound-notes/data/ \
    --log-file "$LOG" --log-level INFO 2>&1 | tail -3
  rm -f /tmp/signals-${TIMESTAMP}.duckdb.gz
fi

# 3. OpenClaw workspace and memory
echo "Syncing OpenClaw workspace..." | tee -a "$LOG"
rclone sync /home/synczus/.openclaw/workspace gdrive:compound-notes/openclaw/ \
  --exclude ".git/**" --exclude "node_modules/**" --exclude "tmp/**" \
  --exclude "*.cache" \
  --log-file "$LOG" --log-level INFO 2>&1 | tail -3

# 4. Agent memory
echo "Syncing memory files..." | tee -a "$LOG"
rclone sync /home/synczus/.openclaw/workspace/memory gdrive:compound-notes/memory/ \
  --log-file "$LOG" --log-level INFO 2>&1 | tail -3

# 5. kestrel memory bank
echo "Syncing memory bank..." | tee -a "$LOG"
rclone sync /home/synczus/kestrel/memory-bank gdrive:compound-notes/memory-bank/ \
  --exclude ".git/**" \
  --log-file "$LOG" --log-level INFO 2>&1 | tail -3

# 6. scores / pulse
echo "Syncing pulse..." | tee -a "$LOG"
rclone sync /home/synczus/kestrel/pulse gdrive:compound-notes/pulse/ \
  --log-file "$LOG" --log-level INFO 2>&1 | tail -3

# Summary
echo "" | tee -a "$LOG"
echo "=== Sync Complete $(date -u) ===" | tee -a "$LOG"
rclone about gdrive: 2>&1 | tee -a "$LOG"
echo "" | tee -a "$LOG"
echo "Last sync: $TIMESTAMP" > /home/synczus/kestrel/logs/gdrive/last-sync.txt
echo "GDrive sync complete at $(date)"