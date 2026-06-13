"""History Service for tracking file versions and loading project memory."""

import hashlib
import logging
import os
import time
import uuid
from pathlib import Path

from vda.core.db import DatabaseManager

logger = logging.getLogger(__name__)

INITIAL_VERSION = "initial"

def get_project_hash(cwd: str) -> str:
    normalized_path = os.path.normpath(cwd).replace("\\", "/").lower()
    return hashlib.sha256(normalized_path.encode('utf-8')).hexdigest()[:16]

class HistoryService:
    def __init__(self, cwd: str = None):
        self.cwd = cwd or os.getcwd()
        self.project_hash = get_project_hash(self.cwd)
        home = Path.home()
        db_path = str(home / ".vda-desktop" / "sessions" / self.project_hash / "vda.db")
        self.db = DatabaseManager(db_path)

    def create_version(self, session_id: str, path: str, content: str) -> dict:
        """Create a new version of a file in the history tracking."""
        # Find latest version
        rows = self.db.fetchall("SELECT version, created_at FROM files WHERE path = ? ORDER BY created_at DESC", (path,))

        if not rows:
            next_version = INITIAL_VERSION
        else:
            latest_version = rows[0]["version"]
            if latest_version == INITIAL_VERSION:
                next_version = "v1"
            elif latest_version.startswith("v"):
                try:
                    num = int(latest_version[1:])
                    next_version = f"v{num + 1}"
                except ValueError:
                    next_version = f"v{int(time.time())}"
            else:
                next_version = f"v{int(time.time())}"

        file_id = str(uuid.uuid4())
        now = int(time.time())
        query = """
            INSERT INTO files (
                id, session_id, path, content, version, is_new, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, 0, ?, ?)
        """
        self.db.execute(query, (file_id, session_id, path, content, next_version, now, now))
        logger.info(f"Created file history version {next_version} for {path}")

        return {
            "id": file_id,
            "session_id": session_id,
            "path": path,
            "version": next_version
        }

    def get_latest_session_files(self, session_id: str) -> list[dict]:
        query = """
            SELECT f.* 
            FROM files f
            INNER JOIN (
                SELECT path, MAX(created_at) as max_created_at
                FROM files
                GROUP BY path
            ) latest ON f.path = latest.path AND f.created_at = latest.max_created_at
            WHERE f.session_id = ?
            ORDER BY f.path
        """
        rows = self.db.fetchall(query, (session_id,))
        return [dict(r) for r in rows]

    def get_project_memory(self) -> str:
        """Reads project-specific memory like OpenCode.md or VDA.md if present."""
        context_files = ["VDA.md", "OpenCode.md"]
        for cf in context_files:
            file_path = os.path.join(self.cwd, cf)
            if os.path.exists(file_path):
                try:
                    with open(file_path, encoding="utf-8") as f:
                        return f"# From:{file_path}\n{f.read()}"
                except Exception as e:
                    logger.error(f"Failed to read project memory {file_path}: {e}")
        return ""
