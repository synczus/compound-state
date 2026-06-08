#!/usr/bin/env bash
# Kestrel → Google Drive backup sync
# Run via cron daily, or manually.
# Syncs key data directories to gdrive:backup/
set -e

TIMESTAMP=$(date -u +%Y%m%d-%H%M%S)
LOG="/home/synczus/kestrel/logs/gdrive-backup.log"
mkdir -p "$(dirname "$LOG")"

echo "[$TIMESTAMP] Starting GDrive backup..." | tee -a "$LOG"

# ── Key directories to back up ────────────────────────────────────
# Kestrel core (exclude logs, caches, venv, large binaries)
rclone sync /home/synczus/kestrel gdrive:backup/kestrel \
    --exclude logs/** \
    --exclude '*.pyc' \
    --exclude __pycache__/** \
    --exclude .venv/** \
    --exclude node_modules/** \
    --exclude '.git/**' \
    --exclude '*.duckdb' \
    --exclude '*.db' \
    --exclude '*.db-*' \
    --progress \
    --log-file "$LOG" \
    --log-level INFO 2>&1 | tail -5

# Configuration files
rclone sync /home/synczus/.config/rclone gdrive:backup/config/rclone \
    --progress 2>&1 | tail -2

rclone sync /home/synczus/.config/systemd gdrive:backup/config/systemd \
    --progress 2>&1 | tail -2

# Key shell configs
rclone copy /home/synczus/.bashrc gdrive:backup/config/ 2>&1 || true
rclone copy /home/synczus/.bash_aliases gdrive:backup/config/ 2>&1 || true
rclone copy /home/synczus/.profile gdrive:backup/config/ 2>&1 || true

# Kestrel environment + credentials (encrypted)
if [ -f /home/synczus/kestrel/.env ]; then
    rclone copy /home/synczus/kestrel/.env gdrive:backup/credentials/ 2>&1 || true
fi

# Desktop shortcuts
rclone sync /home/synczus/Desktop gdrive:backup/desktop \
    --exclude '*.desktop' \
    --progress 2>&1 | tail -2

echo "[$(date -u +%Y%m%d-%H%M%S)] Backup complete" | tee -a "$LOG"