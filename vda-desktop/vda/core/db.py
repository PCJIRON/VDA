"""Database manager for OpenCode-compatible SQLite session/memory storage."""

import sqlite3
import os
import json
import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# OpenCode schemas ported to SQLite syntax
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    parent_session_id TEXT,
    title TEXT NOT NULL,
    message_count INTEGER NOT NULL DEFAULT 0,
    prompt_tokens INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    cost REAL NOT NULL DEFAULT 0.0,
    summary_message_id TEXT,
    updated_at INTEGER NOT NULL,
    created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    parts TEXT NOT NULL,
    model TEXT,
    finished_at INTEGER,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS files (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    path TEXT NOT NULL,
    content TEXT NOT NULL,
    version TEXT NOT NULL,
    is_new INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

-- Indices for performance
CREATE INDEX IF NOT EXISTS idx_sessions_parent ON sessions(parent_session_id);
CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_files_session ON files(session_id);
CREATE INDEX IF NOT EXISTS idx_files_path ON files(path);
"""


class DatabaseManager:
    """Manages the SQLite database connection and operations."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_dir()
        self._init_db()

    def _ensure_dir(self) -> None:
        """Ensure the directory for the database exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

    def _init_db(self) -> None:
        """Initialize the database schema."""
        try:
            with self.get_connection() as conn:
                # Enable foreign keys
                conn.execute("PRAGMA foreign_keys = ON;")
                conn.executescript(SCHEMA_SQL)
                conn.commit()
            logger.info(f"Database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def get_connection(self) -> sqlite3.Connection:
        """Get a configured SQLite database connection."""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        # Use Row factory to allow column access by name
        conn.row_factory = sqlite3.Row
        return conn

    # -------------------------------------------------------------------------
    # Helper CRUD methods for direct use or by services
    # -------------------------------------------------------------------------

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a single query with auto-commit."""
        with self.get_connection() as conn:
            return conn.execute(query, params)
            
    def fetchone(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """Execute a query and fetch a single row."""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchone()
            
    def fetchall(self, query: str, params: tuple = ()) -> list[sqlite3.Row]:
        """Execute a query and fetch all rows."""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()
