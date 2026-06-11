#!/usr/bin/env bash
# Signal Ingestion Pulse — runs every 30 min via cron
# 1. Scans media/inbound/ for new Telegram HTML exports
# 2. Extracts → normalizes → routes through the pipeline
# 3. Appends routed signals to kestrel/signals.md
# 4. Tracks processed files to avoid re-processing
set -euo pipefail

KESTREL_ROOT="/home/synczus/kestrel"
MEDIA_INBOUND="/home/synczus/.openclaw/media/inbound"
INBOX_DIR="${KESTREL_ROOT}/ingestion/inbox"
ROUTED_DIR="${KESTREL_ROOT}/ingestion/routed"
SIGNALS_FILE="${KESTREL_ROOT}/signals.md"
PROCESSED_LOG="${KESTREL_ROOT}/ingestion/.processed_files.log"
EXTRACTOR="${KESTREL_ROOT}/scripts/ingestion/extract.py"
ROUTER="${KESTREL_ROOT}/scripts/ingestion/router.py"
HEARTBEAT="${KESTREL_ROOT}/scripts/heartbeat.sh"

mkdir -p "$INBOX_DIR" "$ROUTED_DIR"
touch "$PROCESSED_LOG"

NEW_FILES=0

# Step 1: Find new HTML exports
for f in "$MEDIA_INBOUND"/messages-*.html; do
    [ -f "$f" ] || continue
    fhash=$(md5sum "$f" | cut -d' ' -f1)
    if grep -q "$fhash" "$PROCESSED_LOG" 2>/dev/null; then
        continue  # already processed
    fi

    echo "[pulse] New export: $(basename "$f")"
    NEW_FILES=$((NEW_FILES + 1))

    # Step 2: Extract messages, normalize via adapter, write to inbox
    python3 "$EXTRACTOR" < "$f" 2>/dev/null || {
        echo "[pulse] WARN: extract failed for $(basename "$f")"
        continue
    }

    # Step 3: Route each inbox event
    ROUTED=0
    for event in "$INBOX_DIR"/*.json; do
        [ -f "$event" ] || continue
        python3 "$ROUTER" --stdin < "$event" 2>/dev/null >> "$SIGNALS_FILE" || true
        mv "$event" "$ROUTED_DIR/"
        ROUTED=$((ROUTED + 1))
    done

    echo "[pulse] Routed $ROUTED events from $(basename "$f")"

    # Mark processed
    echo "$fhash $(basename "$f")" >> "$PROCESSED_LOG"
done

# Step 4: Trim old routed files (>24h)
find "$ROUTED_DIR" -name "*.json" -mtime +1 -delete 2>/dev/null || true

# Step 5: Heartbeat
if [ "$NEW_FILES" -gt 0 ]; then
    echo "[pulse] Complete — $NEW_FILES new sources processed"
    bash "$HEARTBEAT" signal-pulse "ok" 2>/dev/null || true
else
    echo "[pulse] No new exports found"
fi