#!/usr/bin/env python3
"""
Archive Squirrel — Memory Bank Consolidator

Reads propositions from input/ agents, deduplicates, categorizes,
and consolidates into the shared knowledge base.

Runs locally (no LLM calls) for cost efficiency.
"""

import json
import os
import re
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

MEMORY_BANK = Path.home() / "kestrel" / "memory-bank"
INPUT_DIRS = {
    "hermes": MEMORY_BANK / "input" / "hermes",
    "openclaw": MEMORY_BANK / "input" / "openclaw",
    "shannon": MEMORY_BANK / "input" / "shannon",
}
ARCHIVE_DIR = MEMORY_BANK / "archive"
KNOWLEDGE_DIR = MEMORY_BANK / "knowledge"
DB_PATH = MEMORY_BANK / "archive.db"

CATEGORIES = [
    "cost-optimization",
    "pipeline-infrastructure",
    "architecture-decision",
    "monitoring-observability",
    "agent-orchestration",
    "security-governance",
    "knowledge-management",
    "model-strategy",
    "other",
]


def _ensure_db():
    """Initialize SQLite database for tracked entries."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            proposition TEXT NOT NULL UNIQUE,
            category TEXT DEFAULT 'other',
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS archives (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_file TEXT NOT NULL,
            agent TEXT NOT NULL,
            archived_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    return conn


def scan_inputs(conn):
    """Scan input directories for new proposition files."""
    new_files = []
    for agent, dirpath in INPUT_DIRS.items():
        if not dirpath.exists():
            continue
        for f in sorted(dirpath.glob("*.md")):
            new_files.append((agent, f))
    return new_files


def extract_propositions(text):
    """Extract proposition lines from markdown content."""
    props = []
    for line in text.splitlines():
        line = line.strip()
        # Match: - [ ] ..., - [x] ..., **proposition:**, or bullet items
        if re.match(r'^- \[[ x]\]\s+', line):
            props.append(re.sub(r'^- \[[ x]\]\s+', '', line))
        elif re.match(r'^- \*\*.*\*\*:', line):
            props.append(re.sub(r'^- \*\*(.*)\*\*:\s*', r'\1: ', line))
        elif line.startswith('- ') and len(line) > 20:
            props.append(line[2:])
    return props


def categorize(proposition):
    """Simple keyword-based categorization (no LLM needed)."""
    pl = proposition.lower()
    if any(w in pl for w in ["cost", "spend", "budget", "pricing", "token", "credit"]):
        return "cost-optimization"
    if any(w in pl for w in ["pipeline", "autohop", "chain", "bridge", "hop"]):
        return "pipeline-infrastructure"
    if any(w in pl for w in ["architect", "design", "refactor", "restruct", "migrate"]):
        return "architecture-decision"
    if any(w in pl for w in ["monitor", "alert", "dashboard", "metric", "log", "trace"]):
        return "monitoring-observability"
    if any(w in pl for w in ["agent", "orchestrat", "swarm", "delegation", "coordinator"]):
        return "agent-orchestration"
    if any(w in pl for w in ["security", "auth", "key", "secret", "permission", "govern"]):
        return "security-governance"
    if any(w in pl for w in ["memory", "knowledge", "kb", "archive", "store", "recall"]):
        return "knowledge-management"
    if any(w in pl for w in ["model", "llm", "openrouter", "provider", "inferenc"]):
        return "model-strategy"
    return "other"


def already_known(conn, proposition):
    """Check if proposition already exists in the database."""
    cursor = conn.execute(
        "SELECT 1 FROM entries WHERE proposition = ?", (proposition,)
    )
    return cursor.fetchone() is not None


def ingest(conn, agent, filepath, propositions):
    """Insert new propositions into the knowledge base."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    inserted = 0
    skipped = 0
    for prop in propositions:
        if already_known(conn, prop):
            skipped += 1
            continue
        category = categorize(prop)
        try:
            conn.execute(
                "INSERT INTO entries (source, timestamp, proposition, category) VALUES (?, ?, ?, ?)",
                (agent, now, prop, category),
            )
            inserted += 1
        except sqlite3.IntegrityError:
            skipped += 1
    conn.commit()
    return inserted, skipped


def archive_file(conn, agent, filepath):
    """Move processed file to archive."""
    archive_name = f"{agent}_{filepath.name}"
    archive_path = ARCHIVE_DIR / archive_name
    shutil.move(str(filepath), str(archive_path))
    conn.execute(
        "INSERT INTO archives (source_file, agent) VALUES (?, ?)",
        (str(archive_path), agent),
    )
    conn.commit()


def generate_summary(conn):
    """Generate consolidated knowledge base markdown."""
    # Get counts by category
    categories = conn.execute(
        "SELECT category, COUNT(*) as cnt FROM entries WHERE status = 'active' GROUP BY category ORDER BY cnt DESC"
    ).fetchall()
    
    # Get top recent entries per category
    recent = conn.execute("""
        SELECT source, timestamp, proposition, category 
        FROM entries 
        WHERE status = 'active' 
        ORDER BY timestamp DESC 
        LIMIT 50
    """).fetchall()
    
    # Generate the SUMMARY.md
    lines = ["# 🧠 Memory Bank — Consolidated Knowledge", ""]
    lines.append(f"_Last consolidated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}_")
    lines.append(f"_Total active entries: {sum(c[1] for c in categories)}_")
    lines.append("")
    lines.append("## By Category")
    lines.append("")
    for cat, count in categories:
        lines.append(f"- **{cat}**: {count} entries")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Recent Propositions")
    lines.append("")
    for source, ts, prop, cat in recent:
        lines.append(f"- `[{source}]` **[{cat}]** {prop}")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("_Auto-generated by Archive Squirrel_")
    
    summary_path = MEMORY_BANK / "SUMMARY.md"
    summary_path.write_text("\n".join(lines))
    return str(summary_path)


def main():
    conn = _ensure_db()
    
    # Scan for new inputs
    files = scan_inputs(conn)
    if not files:
        print("squirrel: no new inputs to process")
        return 0
    
    total_inserted = 0
    total_skipped = 0
    
    for agent, filepath in files:
        text = filepath.read_text()
        propositions = extract_propositions(text)
        if not propositions:
            print(f"squirrel: {agent}/{filepath.name} — no propositions found, skipping")
            archive_file(conn, agent, filepath)
            continue
        
        inserted, skipped = ingest(conn, agent, filepath, propositions)
        total_inserted += inserted
        total_skipped += skipped
        archive_file(conn, agent, filepath)
        print(f"squirrel: {agent}/{filepath.name} — {inserted} new, {skipped} duplicates")
    
    # Generate consolidated summary
    summary_path = generate_summary(conn)
    print(f"squirrel: summary → {summary_path}")
    print(f"squirrel: done — {total_inserted} new entries, {total_skipped} duplicates skipped")
    return total_inserted


if __name__ == "__main__":
    exit(0 if main() else 0)
