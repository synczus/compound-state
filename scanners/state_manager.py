import sqlite3
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger("kestrel.state")

@dataclass(slots=True)
class RepoState:
    repo_name: str
    last_sha: str

class StateManager:
    """
    Sovereign State Manager for Kestrel.
    Ensures we never process the same commit twice.
    """
    def __init__(self, db_path: str = "kestrel_state.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS commit_state (
                    repo_name TEXT PRIMARY KEY,
                    last_sha TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def get_last_sha(self, repo_name: str) -> Optional[str]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT last_sha FROM commit_state WHERE repo_name = ?", (repo_name,))
            row = cursor.fetchone()
            return row[0] if row else None

    def update_sha(self, repo_name: str, sha: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO commit_state (repo_name, last_sha, last_updated) VALUES (?, ?, CURRENT_TIMESTAMP)",
                (repo_name, sha)
            )
            conn.commit()
