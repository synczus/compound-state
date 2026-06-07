#!/usr/bin/env python3
"""
Archive Squirrel v2 — ADHD-native file intake & note taker

Processes files dropped into inbox/, extracts content, categorizes,
saves structured notes organized by date, and outputs a brief summary.

Designed for rapid-fire context switching — fast, silent, no manual steps.
"""
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

SQUIRREL_ROOT = Path(__file__).resolve().parent
INBOX = SQUIRREL_ROOT / "inbox"
DB_PATH = SQUIRREL_ROOT / "notes.db"
STATE_FILE = SQUIRREL_ROOT / ".squirrel-state.json"

CATEGORIES = {
    "document": "Contracts, reports, whitepapers, formal docs",
    "image": "Screenshots, diagrams, photos",
    "code": "Scripts, configs, patches, logs",
    "reference": "Links, articles, API docs, specs",
    "brainstorm": "Ideas, notes, rough thinking, ADHD dumps",
    "signal": "Market data, signals, alerts, observations",
    "admin": "Invoices, receipts, bills, account info",
    "other": "Uncategorized",
}


# ── DB ─────────────────────────────────────────────────────────────────────

def _ensure_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            filename TEXT NOT NULL,
            original_name TEXT NOT NULL,
            hash TEXT NOT NULL UNIQUE,
            content_type TEXT NOT NULL,
            category TEXT DEFAULT 'other',
            summary TEXT,
            tags TEXT DEFAULT '',
            source TEXT DEFAULT 'telegram',
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_notes_date ON notes(date)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_notes_hash ON notes(hash)
    """)
    conn.commit()
    return conn


def note_exists(conn, file_hash):
    cursor = conn.execute("SELECT 1 FROM notes WHERE hash = ?", (file_hash,))
    return cursor.fetchone() is not None


def save_note(conn, date_str, filename, original_name, file_hash, content_type, category, summary, tags=""):
    conn.execute(
        "INSERT OR IGNORE INTO notes (date, filename, original_name, hash, content_type, category, summary, tags) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (date_str, filename, original_name, file_hash, content_type, category, summary[:500] if summary else "", tags),
    )
    conn.commit()


# ── State tracking ─────────────────────────────────────────────────────────

def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {"seen_hashes": []}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ── Content extraction ─────────────────────────────────────────────────────

TEXT_EXTENSIONS = {".txt", ".md", ".json", ".yaml", ".yml", ".toml", ".csv", ".xml", ".log", ".py", ".js", ".sh", ".html", ".css", ".env.example"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}
DOC_EXTENSIONS = {".pdf", ".doc", ".docx"}
ARCHIVE_EXTENSIONS = {".zip", ".tar", ".gz", ".bz2"}


def extract_text_from_pdf(path):
    """Try pymupdf, then fallback to pdftotext, then just note the filename."""
    try:
        import fitz
        doc = fitz.open(str(path))
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
        if text.strip():
            return text[:5000]
    except ImportError:
        pass
    
    try:
        result = subprocess.run(["pdftotext", str(path), "-"], capture_output=True, text=True, timeout=15)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout[:5000]
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    return None


def extract_text_from_image(path):
    """Try OCR with tesseract or just note it as an image."""
    try:
        result = subprocess.run(["tesseract", str(path), "-"], capture_output=True, text=True, timeout=20)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout[:3000]
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def extract_content(filepath):
    """Extract text content from any file type."""
    ext = filepath.suffix.lower()
    
    if ext in TEXT_EXTENSIONS:
        try:
            text = filepath.read_text(encoding="utf-8", errors="replace")
            return text[:5000], "text"
        except Exception:
            return None, "text"
    
    if ext in DOC_EXTENSIONS:
        text = extract_text_from_pdf(filepath)
        return text, "document"
    
    if ext in IMAGE_EXTENSIONS:
        text = extract_text_from_image(filepath)
        return text, "image"
    
    return None, "other"


def auto_categorize(original_name, text, content_type):
    """Smart category detection from filename + content."""
    name_lower = original_name.lower()
    
    if content_type == "image":
        # Check for screenshots vs photos
        if any(w in name_lower for w in ["screenshot", "screen", "capture", "snip"]):
            return "reference"
        return "image"
    
    if content_type == "document":
        if any(w in name_lower for w in ["contract", "agreement", "invoice", "receipt", "bill"]):
            return "admin"
        if any(w in name_lower for w in ["report", "whitepaper", "paper", "doc"]):
            return "document"
        if any(w in name_lower for w in ["signal", "alert", "market"]):
            return "signal"
        return "document"
    
    if content_type == "text":
        if any(w in name_lower for w in ["idea", "note", "brain", "rough", "dump"]):
            return "brainstorm"
        if any(w in name_lower for w in ["link", "url", "ref", "article"]):
            return "reference"
        if any(w in name_lower for w in ["market", "price", "btc", "eth", "chart"]):
            return "signal"
        if any(w in name_lower for w in [".py", ".js", ".sh", "config", "docker", ".env"]):
            return "code"
        if text and len(text) > 100:
            # Check content for keywords
            tl = text.lower()
            if any(w in tl for w in ["contract", "invoice", "payment", "price"]):
                return "admin"
            if any(w in tl for w in ["market", "btc", "eth", "price", "signal"]):
                return "signal"
        return "document"
    
    return "other"


def generate_summary_text(original_name, category, content_text, content_type):
    """Create a brief note summary from the content."""
    lines = []
    lines.append(f"📄 **{original_name}**")
    lines.append(f"   Type: {content_type} | Category: {category}")
    
    if content_text:
        # Truncate to first meaningful lines
        preview_lines = [l.strip() for l in content_text.split("\n") if l.strip() and not l.startswith("#") and not l.startswith("```")]
        preview = "\n".join(preview_lines[:5])
        if len(preview) > 300:
            preview = preview[:300] + "..."
        if preview:
            lines.append(f"   Preview: {preview}")
    else:
        lines.append("   (binary — content extracted server-side)")
    
    return "\n".join(lines)


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    INBOX.mkdir(parents=True, exist_ok=True)
    conn = _ensure_db()
    state = load_state()
    seen = set(state.get("seen_hashes", []))
    
    today = datetime.now().strftime("%Y-%m-%d")
    out_dir = SQUIRREL_ROOT / today
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Scan inbox
    files = sorted(INBOX.iterdir())
    
    if not files:
        print("[SILENT]")
        return
    
    processed = []
    for f in files:
        if not f.is_file() or f.name.startswith("."):
            continue
        
        h = file_hash(f)
        if h in seen or note_exists(conn, h):
            # Already seen — clean up inbox
            f.unlink(missing_ok=True)
            continue
        
        # Extract content
        content_text, content_type = extract_content(f)
        category = auto_categorize(f.name, content_text, content_type)
        summary = generate_summary_text(f.name, category, content_text, content_type)
        tags = category
        
        # Save the file to the dated directory
        dest_name = f"{datetime.now().strftime('%H%M%S')}_{f.name}"
        dest_path = out_dir / dest_name
        shutil.copy2(str(f), str(dest_path))
        
        # Save note
        save_note(conn, today, dest_name, f.name, h, content_type, category, summary, tags)
        
        seen.add(h)
        processed.append({
            "name": f.name,
            "category": category,
            "type": content_type,
            "summary": summary,
            "dest": str(dest_path),
        })
        
        # Remove from inbox
        f.unlink(missing_ok=True)
    
    # Update state
    state["seen_hashes"] = list(seen)[-500:]  # keep last 500
    save_state(state)
    
    if not processed:
        print("[SILENT]")
        return
    
    # Friendly output for the cron delivery
    lines = ["🐿️ **Archive Squirrel — Note Taker**", ""]
    for p in processed:
        lines.append(p["summary"])
        lines.append("")
    
    if len(processed) > 1:
        lines.append(f"── {len(processed)} files processed → `archivesquirrel/{today}/`")
    else:
        lines.append(f"→ `archivesquirrel/{today}/`")
    
    lines.append("")
    lines.append("Drop files in inbox/ or send them here — squirrel handles the rest.")
    
    print("\n".join(lines))


if __name__ == "__main__":
    main()
