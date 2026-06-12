#!/usr/bin/env python3
"""
Note Intake Server — webhook-based Telegram message receiver.
Uses cloudflared tunnel for public HTTPS endpoint.
Telegram pushes updates here instead of Hermes polling.

Saves user messages to shared-knowledge/notes/.
"""

import json
import os
import re
import subprocess
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

NOTES_DIR = Path("/home/synczus/kestrel/shared-knowledge/notes")
AUTHORIZED_CHATS = {"1406238565"}  # user DM
PORT = 18788

# Read bot token from .env
BOT_TOKEN = ""
env_path = Path("/home/synczus/kestrel/.env")
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if line.startswith("TELEGRAM_BOT_TOKEN="):
            BOT_TOKEN = line.split("=", 1)[1].strip()
            break

if not BOT_TOKEN:
    print("NO_BOT_TOKEN", flush=True)
    sys.exit(1)

API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"


def sanitize_title(text: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9 _-]", "", text.strip())
    return clean[:50].rstrip() if clean else "note"


def save_note(chat_id: str, msg: dict) -> str | None:
    mid = msg["message_id"]
    date_ts = msg.get("date", int(time.time()))
    dt = datetime.fromtimestamp(date_ts, tz=timezone.utc)
    text = ""
    is_voice = False

    if "text" in msg:
        text = msg["text"]
    elif "caption" in msg:
        text = msg["caption"]
    elif "voice" in msg:
        is_voice = True
        duration = msg["voice"].get("duration", 0)
        file_id = msg["voice"]["file_id"]
        text = "[VOICE NOTE — {}s — needs transcription: file_id={}]".format(duration, file_id)
    elif "audio" in msg:
        text = "[AUDIO: {}]".format(msg["audio"].get("title", "unknown"))
    else:
        text = "[OTHER MESSAGE]"

    if not text.strip():
        return None

    hint = sanitize_title(text)
    timestamp = dt.strftime("%Y%m%d-%H%M%S")
    filename = "{}_{}.md".format(timestamp, hint[:40])
    filepath = NOTES_DIR / filename

    counter = 1
    while filepath.exists():
        filepath = NOTES_DIR / "{}_{}_{}.md".format(timestamp, hint[:35], counter)
        counter += 1

    voice_line = "**Type:** Voice note\n" if is_voice else ""
    content = (
        "# Note — {}\n"
        "**Source:** Telegram (chat: {})\n"
        "**Message ID:** {}\n"
        "{}\n"
        "{}\n"
    ).format(
        dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
        chat_id,
        mid,
        voice_line,
        text,
    )
    filepath.write_text(content)
    return filename


class NoteHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            update = json.loads(body)
        except json.JSONDecodeError:
            self.send_response(200)
            self.end_headers()
            return

        msg = update.get("message", {})
        chat_id = str(msg.get("chat", {}).get("id", ""))
        mid = msg.get("message_id", 0)

        if chat_id in AUTHORIZED_CHATS and mid:
            filename = save_note(chat_id, msg)
            if filename:
                print("SAVED: {}".format(filename), flush=True)

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, fmt, *args):
        pass  # silent


def main():
    NOTES_DIR.mkdir(parents=True, exist_ok=True)

    # Start cloudflared tunnel
    tunnel_proc = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", "http://localhost:{}".format(PORT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    # Wait for tunnel URL
    tunnel_url = None
    start = time.time()
    url_pat = re.compile(r"(https://[a-zA-Z0-9.-]+\.trycloudflare\.com)")
    while time.time() - start < 30:
        line = tunnel_proc.stdout.readline()
        if not line:
            continue
        m = url_pat.search(line)
        if m:
            tunnel_url = m.group(1)
            break
        if "Failed" in line or "error" in line.lower():
            print("TUNNEL_ERR: {}".format(line.strip()), flush=True)
            tunnel_proc.kill()
            sys.exit(1)

    if not tunnel_url:
        print("NO_TUNNEL_URL", flush=True)
        tunnel_proc.kill()
        sys.exit(1)

    print("TUNNEL_URL={}".format(tunnel_url), flush=True)

    # Register webhook with Telegram
    webhook_url = "{}/webhook".format(tunnel_url)
    req = urllib.request.Request(
        "{}/setWebhook".format(API_BASE),
        data=json.dumps({"url": webhook_url, "allowed_updates": ["message"]}).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            print("WEBHOOK_SET: {}".format(result), flush=True)
    except Exception as e:
        print("WEBHOOK_ERR: {}".format(e), flush=True)
        tunnel_proc.kill()
        sys.exit(1)

    # Start HTTP server
    server = HTTPServer(("0.0.0.0", PORT), NoteHandler)
    print("SERVER_STARTED port={}".format(PORT), flush=True)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
        tunnel_proc.kill()
        # Cleanup webhook
        try:
            urllib.request.urlopen(
                urllib.request.Request(
                    "{}/setWebhook".format(API_BASE),
                    data=json.dumps({"url": ""}).encode(),
                    headers={"Content-Type": "application/json"},
                ),
                timeout=5,
            )
        except Exception:
            pass
        print("SHUTDOWN", flush=True)


if __name__ == "__main__":
    main()