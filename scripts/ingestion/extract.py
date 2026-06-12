#!/usr/bin/env python3
"""
Telegram HTML Export Extractor v0.1
Parses Telegram channel/group HTML exports into structured JSON events,
then pipes them through the source adapter → inbox → router pipeline.

Usage:
  python3 scripts/ingestion/extract.py < /path/to/messages-xxxxx.html
  
Output: Writes normalized events to ingestion/inbox/ for the router.
"""
import hashlib
import html
import json
import os
import re
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser

KESTREL_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TelegramExportParser(HTMLParser):
    """Extract messages from a Telegram HTML export."""

    def __init__(self):
        super().__init__()
        self.messages = []
        self._current = {}
        self._in_text = False
        self._in_from = False
        self._in_date = False
        self._text_parts = []
        self._date_str = ""
        self._from_name = ""
        self._tag_stack = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self._tag_stack.append(tag)

        if tag == "div" and "class" in attrs:
            cls = attrs["class"]
            if cls == "text":
                self._in_text = True
                self._text_parts = []
            elif cls == "from_name":
                self._in_from = True
                self._from_name = ""
            elif cls == "date details" and "title" in attrs:
                self._date_str = attrs["title"]
                self._in_date = True
            elif cls == "message default clearfix":
                # Finish previous message if exists
                if self._current:
                    self._finalize_current()
                self._current = {"id": attrs.get("id", "")}
            elif cls == "media_wrap clearfix":
                self._current["has_media"] = True

    def handle_endtag(self, tag):
        if self._tag_stack:
            self._tag_stack.pop()
        if tag == "div" and self._in_text:
            self._in_text = False
        if tag == "div" and self._in_from:
            self._in_from = False
        if tag == "div" and self._in_date:
            self._in_date = False

    def handle_data(self, data):
        if self._in_text:
            stripped = data.strip()
            if stripped:
                self._text_parts.append(stripped)
        if self._in_from:
            self._from_name += data.strip()
        # Date is in the title attribute of the pull_right div, handled in starttag

    def handle_entityref(self, name):
        if self._in_text:
            decoded = html.unescape(f"&{name};")
            if decoded.strip():
                self._text_parts.append(decoded)

    def _finalize_current(self):
        msg = self._current
        if self._text_parts:
            full_text = " ".join(self._text_parts)
            # Clean excess whitespace
            full_text = re.sub(r'\s+', ' ', full_text).strip()
            msg["text"] = full_text
        if self._from_name:
            msg["from"] = self._from_name.strip()
        if self._date_str:
            msg["timestamp"] = self._date_str
        msg_id_match = re.search(r'message(\d+)', msg.get("id", ""))
        if msg_id_match:
            msg["message_id"] = msg_id_match.group(1)
        if "text" in msg or "has_media" in msg:
            self.messages.append(msg)
        self._current = {}
        self._text_parts = []
        self._from_name = ""
        self._date_str = ""


def detect_source(messages):
    """Detect source_id from message content."""
    from_names = set(m.get("from", "") for m in messages if m.get("from"))
    from_joined = " ".join(from_names).lower()

    if "disclose.tv" in from_joined or "disclosetv" in from_joined:
        return "disclosetv"
    if "whale alert" in from_joined:
        return "whale-alert"
    return "unknown"


def run_adapter(source_id: str, message: dict) -> dict | None:
    """Pipe a single message through the appropriate adapter script."""
    import subprocess

    adapter_map = {
        "disclosetv": "scripts/ingestion/adapters/disclosetv.py",
        "whale-alert": "scripts/ingestion/adapters/whale-alert.py",
        "unknown": "scripts/ingestion/adapters/generic.py",
    }
    adapter_path = os.path.join(KESTREL_ROOT, adapter_map.get(source_id, ""))
    if not os.path.exists(adapter_path):
        print(f"  WARN: no adapter for {source_id}", file=sys.stderr)
        return None

    raw_input = {
        "text": message.get("text", ""),
        "message_id": message.get("message_id", ""),
        "timestamp": parse_timestamp(message.get("timestamp", "")),
        "source": source_id,
    }

    try:
        proc = subprocess.run(
            [sys.executable, adapter_path],
            input=json.dumps(raw_input),
            capture_output=True, text=True, timeout=10,
        )
        return json.loads(proc.stdout)
    except Exception as e:
        print(f"  ERROR running adapter for msg {message.get('message_id')}: {e}", file=sys.stderr)
        return None


def parse_timestamp(raw: str) -> str:
    """Convert Telegram export timestamp format to ISO8601.
    Format: "11.06.2022 13:31:33 UTC-05:00"
    """
    try:
        # Remove timezone offset for parsing
        match = re.match(r'(\d{2})\.(\d{2})\.(\d{4})\s+(\d{2}:\d{2}:\d{2})', raw)
        if match:
            day, month, year, time_str = match.groups()
            # Try to keep the UTC offset
            tz_part = re.search(r'(UTC[+-]\d{2}:\d{2})', raw)
            tz = tz_part.group(1) if tz_part else "UTC"
            return f"{year}-{month}-{day}T{time_str}:00"
        return datetime.now(timezone.utc).isoformat()
    except:
        return datetime.now(timezone.utc).isoformat()


def main():
    html_content = sys.stdin.read()

    parser = TelegramExportParser()
    parser.feed(html_content)

    messages = parser.messages
    if not messages:
        print("No messages found in export.", file=sys.stderr)
        return

    print(f"Extracted {len(messages)} messages from export.", file=sys.stderr)
    source_id = detect_source(messages)
    print(f"Detected source: {source_id}", file=sys.stderr)

    # Filter to only content messages (skip pinned/service/promos)
    content_msgs = [m for m in messages if
                    m.get("text") and len(m.get("text", "")) > 20
                    and "donate" not in m.get("text", "").lower()
                    and "follow us on" not in m.get("text", "").lower()
                    and "subscribe" not in m.get("text", "").lower()[:15]]

    print(f"Content messages after filter: {len(content_msgs)}", file=sys.stderr)

    # Pipe through adapter and write to inbox
    inbox_dir = os.path.join(KESTREL_ROOT, "ingestion", "inbox")
    os.makedirs(inbox_dir, exist_ok=True)

    routed_count = 0
    for i, msg in enumerate(content_msgs[:100]):  # cap at 100 per run
        event = run_adapter(source_id, msg)
        if not event:
            continue

        # Write to inbox
        seq = msg.get("message_id", f"msg{i}")
        outpath = os.path.join(inbox_dir, f"{source_id}-{seq}.json")
        with open(outpath, "w") as f:
            json.dump(event, f)
        routed_count += 1

    print(f"Wrote {routed_count} events to inbox/", file=sys.stderr)
    print(f"To route: python3 scripts/ingestion/router.py --dir ingestion/inbox")


if __name__ == "__main__":
    main()