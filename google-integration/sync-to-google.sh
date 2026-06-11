#!/bin/bash
# ============================================================
# RCLONE → GOOGLE DRIVE :: SYNC ENGINE
# ============================================================
# Usage:
#   ./sync-to-google.sh                  # Dry run (--dry-run)
#   ./sync-to-google.sh --live           # Real sync
#   ./sync-to-google.sh --status         # Show sync state
# ============================================================

CONFIG_FILE="/home/synczus/.config/rclone/rclone.conf"
REMOTE="gdrive"
BASE_DIR="/home/synczus"
SYNC_LOG="/home/synczus/kestrel/google-integration/sync.log"
PIDFILE="/tmp/rclone-sync.pid"
CRYPTO_KEY_FILE="/home/synczus/kestrel/google-integration/sync-pass.txt"

DEFAULT_SOURCES=(
    "kestrel"
    "projects/active"
    ".openclaw"
    ".openclaw-nemo"
    ".hermes"
    "hub"
)

check_config() {
    if [ ! -f "$CONFIG_FILE" ]; then
        echo "❌ rclone config not found. Run: rclone config"
        echo "   Create a remote named 'gdrive' for Google Drive."
        exit 1
    fi
    if ! rclone listremotes 2>/dev/null | grep -q "^${REMOTE}:"; then
        echo "❌ Remote '${REMOTE}:' not configured in rclone."
        echo "   Run: rclone config"
        exit 1
    fi
    echo "✅ rclone remote '${REMOTE}:' found"
}

check_auth() {
    echo "🔍 Checking Google Drive auth..."
    if rclone lsd "${REMOTE}:" 2>&1 | grep -q "Error"; then
        echo "❌ Auth expired or invalid. Re-auth needed:"
        echo "   rclone config reconnect ${REMOTE}:"
        exit 1
    fi
    echo "✅ Auth valid"
}

sync_dir() {
    local source="$1"
    local dest="$2"
    local label="$3"
    
    local src_path="${BASE_DIR}/${source}"
    
    if [ ! -d "$src_path" ]; then
        echo "   ⚠️  Source '$src_path' not found — skipping"
        return
    fi
    
    local dry_run_flag=""
    [ "$DRY_RUN" = "true" ] && dry_run_flag="--dry-run"
    
    echo "   📤 Syncing $label..."
    rclone sync "$src_path" "${REMOTE}:kestrel-backup/${dest}" \
        $dry_run_flag \
        --progress \
        --exclude ".git/**" \
        --exclude "**/node_modules/**" \
        --exclude "**/__pycache__/**" \
        --exclude "*.pyc" \
        --exclude "venv/**" \
        --exclude ".venv/**" \
        --exclude "*.duckdb" \
        --exclude "*.db" \
        --exclude "auth/token.json" \
        --exclude "auth/credentials.json" \
        --exclude "*.log" \
        >> "$SYNC_LOG" 2>&1
    
    local size=$(du -sh "$src_path" 2>/dev/null | cut -f1)
    echo "   ✅ $label synced ($size)"
}

show_status() {
    echo "📊 Google Drive Sync Status"
    echo "==========================="
    echo ""
    echo "🟢 Sources (local):"
    for src in "${DEFAULT_SOURCES[@]}"; do
        local path="${BASE_DIR}/${src}"
        if [ -d "$path" ]; then
            local size=$(du -sh "$path" 2>/dev/null | cut -f1)
            echo "   $src → $size"
        fi
    done
    echo ""
    echo "🔵 Destinations (Google Drive):"
    rclone size "${REMOTE}:kestrel-backup/" 2>/dev/null || echo "   (empty or not synced yet)"
    echo ""
    echo "📋 Last sync:"
    tail -5 "$SYNC_LOG" 2>/dev/null || echo "   No sync history yet"
}

case "${1:-}" in
    --live)
        DRY_RUN="false"
        ;;
    --status)
        check_config
        check_auth
        show_status
        exit 0
        ;;
    --setup)
        echo "📦 RCLONE GOOGLE DRIVE SETUP"
        echo "============================"
        echo ""
        echo "Step 1: Run this in your terminal:"
        echo "   rclone config"
        echo ""
        echo "Step 2: Choose 'n' for new remote"
        echo "   Name: gdrive"
        echo "   Storage: drive (Google Drive)"
        echo ""
        echo "Step 3: Follow OAuth URL → auth in browser → paste token"
        echo ""
        echo "Step 4: Verify:"
        echo "   ./sync-to-google.sh --status"
        exit 0
        ;;
    *)
        DRY_RUN="true"
        echo "⚠️  DRY RUN — add --live for real sync"
        ;;
esac

echo "=========================================="
echo " RCLONE → GOOGLE DRIVE SYNC"
echo " $(date -u)"
echo "=========================================="
echo ""

check_config
check_auth

mkdir -p "$(dirname "$SYNC_LOG")"

TOTAL_SIZE=0
for src in "${DEFAULT_SOURCES[@]}"; do
    label=$(basename "$src")
    sync_dir "$src" "$src" "$label"
done

echo ""
echo "✅ Sync $( [ "$DRY_RUN" = "true" ] && echo "DRY RUN" || echo "COMPLETE" )"
echo "   $(date -u)"