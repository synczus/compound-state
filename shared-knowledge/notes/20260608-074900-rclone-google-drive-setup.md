# Note — 2026-06-08 07:49 UTC
**Source:** Telegram (AI Hangout)

## Built: Rclone Google Drive Note Sync

- rclone configured with Google Drive (gdrive:)
- Folder created: compound-notes
- Notes save to `shared-knowledge/notes/` locally
- Every 5 min synced to Google Drive via cron
- Full ramble preservation — no truncation, no compression

## Pending

- Inversion change: scan full chat delta since last cron run instead of just system state
- Second bot token for autonomous note intake (optional now since rclone handles off-machine access)

## Architecture

User sends voice/text → Hermes saves to shared-knowledge/notes/ (instant, local) → rclone cron syncs to Google Drive every 5 min (autonomous, no token cost)