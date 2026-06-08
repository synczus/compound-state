#!/usr/bin/env bash
# Unmount Google Drive safely
set -e

MOUNTPOINT="/home/synczus/gdrive"

if ! mountpoint -q "$MOUNTPOINT" 2>/dev/null; then
    echo "ℹ️  GDrive not mounted at $MOUNTPOINT"
    exit 0
fi

echo "📤 Syncing and unmounting GDrive..."
sync

if systemctl --user is-active rclone-gdrive.service &>/dev/null; then
    systemctl --user stop rclone-gdrive.service
    echo "✅ Unmounted via systemd"
else
    fusermount -uz "$MOUNTPOINT"
    echo "✅ Unmounted via fusermount"
fi