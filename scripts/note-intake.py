#!/usr/bin/env python3
"""
Note Intake — polls Telegram bot API for new messages,
writes them as markdown to Google Drive via rclone FUSE mount.
Idempotent — uses a seen-IDs file to avoid duplicates.

Voice messages: downloaded as .ogg for transcription.
"""

import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────
NOTES_DIR = Path("/home/synczus/gdrive/kestrel-notes")
SEEN_FILE = Path("/home/synczus/kestrel/scripts/.note-intake-seen.json")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
AUTHORIZED_CHAT_IDS = {"1406238565", "-5087043705"}  # DM + group
# ──────────────────────────────────────────────────────────────────

if not BOT_TOKEN:
    print("NO_BOT_TOKEN")
    sys.exit(1)

API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"


def sanitize_title(text: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9 _-]", "", text.strip())
    return clean[:60].rstrip() if clean else "note"


def fetch_updates(offset: int = 0) -> list:
    url = f"{API_BASE}/getUpdates?timeout=10&allowed_updates=[\"message\"]"
    if offset:
        url += f"&offset={offset}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            return data.get("result", [])
    except Exception as e:
        print(f"FETCH_ERR: {e}")
        return []


def download_voice(file_id: str, notes_dir: Path, timestamp: str) -> str | None:
    """Download a voice message as .ogg to notes_dir."""
    try:
        # Get file path
        req = urllib.request.Request(f"{API_BASE}/getFile?file_id={file_id}")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            file_path = data["result"]["file_path"]
        # Download
        dl_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
        audio_path = notes_dir / f"voice_{timestamp}.ogg"
        req = urllib.request.Request(dl_url)
        with urllib.request.urlopen(req, timeout=30) as resp:
            audio_path.write_bytes(resp.read())
        return str(audio_path)
    except Exception as e:
        print(f"VOICE_DL_ERR: {e}")
        return None


def save_note(msg: dict) -> str | None:
    """Save a Telegram message as a markdown note to GDrive."""
    mid = msg["message_id"]
    date_ts = msg.get("date", int(time.time()))
    dt = datetime.fromtimestamp(date_ts, tz=timezone.utc)
    text = ""
    is_voice = False
    voice_path = None

    if "text" in msg:
        text = msg["text"]
    elif "caption" in msg:
        text = msg["caption"]
    elif "voice" in msg:
        is_voice = True
        duration = msg["voice"].get("duration", 0)
        file_id = msg["voice"]["file_id"]
        ts = dt.strftime("%Y%m%d_%H%M%S")
        voice_path = download_voice(file_id, NOTES_DIR, ts)
        if voice_path:
            text = f"[VOICE NOTE — {duration}s — saved: {voice_path}]"
        else:
            text = f"[VOICE NOTE — {duration}s — file_id: {file_id}]"
    elif "audio" in msg:
        text = f"[AUDIO: {msg['audio'].get('title', 'unknown')}]"
    else:
        return None

    if not text.strip():
        return None

    chat = msg.get("chat", {})
    chat_title = chat.get("title", chat.get("username", str(chat.get("id", "?"))))
    from_user = msg.get("from", {})
    username = from_user.get("username") or from_user.get("first_name", "unknown")

    hint = sanitize_title(text)
    timestamp = dt.strftime("%Y%m%d-%H%M%S")
    filename = f"{timestamp}_{hint[:40]}.md"
    filepath = NOTES_DIR / filename

    counter = 1
    while filepath.exists():
        filepath = NOTES_DIR / f"{timestamp}_{hint[:35]}_{counter}.md"
        counter += 1

    voice_line = f"**Voice file:** {voice_path}\n" if voice_path else ""
    content = (
        "# Note — {}\n"
        "**Source:** Telegram ({})\n"
        "**From:** @{}\n"
        "**Message ID:** {}\n"
        "{}\n"
        "{}\n"
    ).format(
        dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
        chat_title,
        username,
        mid,
        voice_line,
        text,
    )
    filepath.write_text(content)
    return filename


def main():
    seen = {}
    if SEEN_FILE.exists():
        try:
            seen = json.loads(SEEN_FILE.read_text())
        except (json.JSONDecodeError, ValueError):
            seen = {}

    max_update_id = seen.get("last_update_id", 0)
    saved_count = 0

    updates = fetch_updates(max_update_id + 1)
    for upd in updates:
        update_id = upd["update_id"]
        msg = upd.get("message", {})
        chat_id = str(msg.get("chat", {}).get("id", ""))
        mid = msg.get("message_id", 0)

        if chat_id in AUTHORIZED_CHAT_IDS and mid:
            filename = save_note(msg)
            if filename:
                saved_count += 1

        max_update_id = max(max_update_id, update_id)

    # Save seen state
    seen["last_update_id"] = max_update_id
    seen["last_run"] = datetime.now(timezone.utc).isoformat()
    SEEN_FILE.write_text(json.dumps(seen, indent=2))

    print(f"NOTES_SAVED={saved_count}" if saved_count else "NO_NEW_NOTES")


if __name__ == "__main__":
    main()