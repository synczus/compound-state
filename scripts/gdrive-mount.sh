#!/usr/bin/env bash
# Mount Google Drive via rclone FUSE (or open existing mount)
set -e

MOUNTPOINT="/home/synczus/gdrive"

if mountpoint -q "$MOUNTPOINT" 2>/dev/null; then
    echo "✅ GDrive already mounted at $MOUNTPOINT"
    nautilus "$MOUNTPOINT" &
    exit 0
fi

mkdir -p "$MOUNTPOINT"

# Try systemd service first
if systemctl --user is-enabled rclone-gdrive.service &>/dev/null; then
    echo "🔧 Starting systemd mount service..."
    systemctl --user start rclone-gdrive.service
    sleep 2
    if mountpoint -q "$MOUNTPOINT"; then
        echo "✅ GDrive mounted via systemd"
        nautilus "$MOUNTPOINT" &
        exit 0
    fi
fi

# Fallback: direct mount (will prompt for password)
echo "📎 Mounting Google Drive (direct)..."
rclone mount gdrive: "$MOUNTPOINT" \
    --vfs-cache-mode writes \
    --daemon \
    --log-file /home/synczus/.cache/rclone/gdrive-mount.log \
    --log-level INFO

sleep 2
if mountpoint -q "$MOUNTPOINT"; then
    echo "✅ GDrive mounted"
    nautilus "$MOUNTPOINT" &
else
    echo "❌ Mount failed — check /home/synczus/.cache/rclone/gdrive-mount.log"
    exit 1
fi