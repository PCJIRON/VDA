import hashlib
import json
import logging
import os
import time
import uuid
from datetime import datetime
from pathlib import Path

from vda.core.db import DatabaseManager

logger = logging.getLogger(__name__)


def get_project_hash(cwd: str) -> str:
    normalized_path = os.path.normpath(cwd).replace("\\", "/").lower()
    return hashlib.sha256(normalized_path.encode('utf-8')).hexdigest()[:16]


class SessionService:
    def __init__(self, cwd: str = None):
        self.cwd = cwd or os.getcwd()
        self.project_hash = get_project_hash(self.cwd)
        home = Path.home()
        db_dir = home / ".vda-desktop" / "sessions" / self.project_hash
        db_dir.mkdir(parents=True, exist_ok=True)

        self.db_path = str(db_dir / "vda.db")
        self.db = DatabaseManager(self.db_path)
        logger.info(f"Initialized SessionService with SQLite DB: {self.db_path}")

    def create_session(self, title: str = "New Chat", session_id: str = None) -> str:
        session_id = session_id or str(uuid.uuid4())
        now = int(time.time())
        query = """
            INSERT INTO sessions (
                id, parent_session_id, title, updated_at, created_at
            ) VALUES (?, NULL, ?, ?, ?)
        """
        self.db.execute(query, (session_id, title, now, now))
        return session_id

    def create_task_session(self, tool_call_id: str, parent_session_id: str, title: str) -> str:
        now = int(time.time())
        query = """
            INSERT INTO sessions (
                id, parent_session_id, title, updated_at, created_at
            ) VALUES (?, ?, ?, ?, ?)
        """
        self.db.execute(query, (tool_call_id, parent_session_id, title, now, now))
        return tool_call_id

    def load_last_session(self) -> tuple[str, list[dict], str]:
        row = self.db.fetchone("SELECT id FROM sessions WHERE parent_session_id IS NULL ORDER BY updated_at DESC LIMIT 1")
        if not row:
            return None, [], None
        return self.load_session(row["id"])

    def get_all_sessions(self) -> list[dict]:
        rows = self.db.fetchall("SELECT * FROM sessions WHERE parent_session_id IS NULL ORDER BY updated_at DESC")
        sessions = []
        for row in rows:
            # Fetch last message text for preview
            last_msg_row = self.db.fetchone(
                "SELECT parts FROM messages WHERE session_id = ? ORDER BY created_at DESC LIMIT 1",
                (row["id"],)
            )
            last_msg_text = "Empty session"
            if last_msg_row:
                try:
                    parts = json.loads(last_msg_row["parts"])
                    if parts and "text" in parts[0]:
                        text = parts[0]["text"].replace("\n", " ").strip()
                        last_msg_text = text[:22] + "..." if len(text) > 22 else text
                except Exception:
                    pass

            sessions.append({
                'id': row["id"],
                'title': row["title"],
                'last_msg': last_msg_text,
                'timestamp': row["updated_at"],
                'date_str': datetime.fromtimestamp(row["updated_at"]).strftime("%b %d, %I:%M %p"),
            })
        return sessions

    def load_session(self, session_id: str) -> tuple[str, list[dict], str]:
        # Check if session exists
        row = self.db.fetchone("SELECT id FROM sessions WHERE id = ?", (session_id,))
        if not row:
            return session_id, [], None

        msg_rows = self.db.fetchall("SELECT id, role, parts FROM messages WHERE session_id = ? ORDER BY created_at ASC", (session_id,))
        messages = []
        leaf_id = None

        for msg in msg_rows:
            leaf_id = msg["id"]
            role = msg["role"]
            try:
                parts = json.loads(msg["parts"])
                text_parts = [p.get('text', '') for p in parts if 'text' in p]
                content = "".join(text_parts)
                attachments = [p for p in parts if p.get('type') == 'image_url' or 'image_url' in p]
                messages.append({
                    "role": role,
                    "content": content,
                    "attachments": attachments,
                })
            except Exception as e:
                logger.warning(f"Failed to parse message {leaf_id} parts: {e}")

        return session_id, messages, leaf_id

    def save_message(self, session_id: str, role: str, text: str, attachments: list = None, parent_uuid: str = None) -> str:
        # If session doesn't exist yet, lazily create it
        if not self.db.fetchone("SELECT id FROM sessions WHERE id = ?", (session_id,)):
            self.create_session(title=text[:20] + "...", session_id=session_id)

        msg_uuid = str(uuid.uuid4())
        now = int(time.time())
        db_role = "assistant" if role == "assistant" else "user"
        model_role = "model" if role == "assistant" else "user"

        parts = [{"text": text}]
        if attachments:
            for att in attachments:
                if att.get('type') == 'image' or att.get('image_url'):
                    mime = att.get('mime', 'image/png')
                    b64 = att.get('base64')
                    parts.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{b64}"},
                    })

        query = """
            INSERT INTO messages (
                id, session_id, role, parts, model, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        self.db.execute(query, (
            msg_uuid,
            session_id,
            db_role,
            json.dumps(parts),
            "vda-model", # Default model
            now,
            now
        ))

        # Update session timestamp and message count
        update_query = """
            UPDATE sessions 
            SET updated_at = ?, message_count = message_count + 1 
            WHERE id = ?
        """
        self.db.execute(update_query, (now, session_id))

        return msg_uuid

    def add_session_cost(self, session_id: str, cost: float) -> None:
        """Add cost to a session (used for sub-agent cost propagation)."""
        now = int(time.time())
        self.db.execute(
            "UPDATE sessions SET cost = cost + ?, updated_at = ? WHERE id = ?",
            (cost, now, session_id),
        )
