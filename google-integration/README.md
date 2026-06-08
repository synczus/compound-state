# Google Ecosystem Integration

## Architecture
```
rclone sync ──→ Google Drive ──→ Gemini API (on top)
```

**Foundation:** rclone syncs compound directories to Google Drive.
**Layer 2:** `google-notes.py` writes to Google Docs via Drive API.
**Layer 3:** Gemini accesses Drive files for AI processing.

## Status
- ✅ rclone installed
- ✅ `sync-to-google.sh` script ready
- ✅ `google-notes.py` script ready
- ❌ Needs OAuth — run `rclone config` once (30 seconds)

## Setup (One-Time)
```bash
# Auth with Google
rclone config
# Name: gdrive
# Storage: drive

# Verify
./sync-to-google.sh --status

# First sync (select directories ~2GB)
./sync-to-google.sh --live
```

## Scheduled Sync
Once auth is done, enable auto-sync:
```bash
crontab -e
# Add: */30 * * * * /home/synczus/kestrel/google-integration/sync-to-google.sh --live
```

## Usage
```bash
# Sync your workspace
./sync-to-google.sh              # Dry run
./sync-to-google.sh --live       # Real sync
./sync-to-google.sh --status     # Check state

# Take a note (after OAuth)
python3 google-notes.py "Buy ETH at 1600"
```
