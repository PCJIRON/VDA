"""
Qwen Code integrated session service.
Implements the exact JSONL history format and storage paths used by the qwen-code extension.
Path: ~/.qwen/tmp/<project_hash>/chats/<sessionId>.jsonl
"""

import os
import json
import uuid
import hashlib
from pathlib import Path
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


def get_project_hash(cwd: str) -> str:
    """Calculate the project hash matching qwen-code logic."""
    # Normalize path (forward slashes, lowercase)
    normalized_path = os.path.normpath(cwd).replace("\\", "/").lower()
    return hashlib.sha256(normalized_path.encode('utf-8')).hexdigest()[:16]


class QwenSessionService:
    """Service for reading and writing to qwen-code JSONL chat histories."""

    def __init__(self, cwd: str = None):
        """Initialize session service for a specific directory."""
        self.cwd = cwd or os.getcwd()
        self.project_hash = get_project_hash(self.cwd)
        
        # Calculate ~/.qwen/tmp/<project_hash>/chats
        home = Path.home()
        self.chats_dir = home / ".qwen" / "tmp" / self.project_hash / "chats"
        
        # Ensure directory exists
        self.chats_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized QwenSessionService. Chats dir: {self.chats_dir}")

    def load_last_session(self) -> tuple[str, list[dict], str]:
        """
        Load the most recently modified session file.
        Returns: (session_id, list_of_messages (history), last_uuid)
        """
        try:
            files = list(self.chats_dir.glob("*.jsonl"))
            if not files:
                return None, [], None

            # Sort by modification time descending
            files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            most_recent_file = files[0]
            session_id = most_recent_file.stem

            return self.load_session(session_id)
        except Exception as e:
            logger.error(f"Error loading last session: {e}", exc_info=True)
            return None, [], None

    def get_all_sessions(self) -> list[dict]:
        """
        Get metadata for all previous sessions for listing history.
        """
        sessions = []
        try:
            files = list(self.chats_dir.glob("*.jsonl"))
            for f in files:
                session_id = f.stem
                title = "New Chat"
                last_msg_text = "Empty session"
                timestamp = f.stat().st_mtime
                try:
                    with open(f, 'r', encoding='utf-8') as file:
                        lines = [line.strip() for line in file if line.strip()]
                    
                    if not lines:
                        continue
                        
                    for line in lines:
                        try:
                            record = json.loads(line)
                            if record.get('type') == 'user':
                                parts = record.get('message', {}).get('parts', [])
                                if parts and 'text' in parts[0]:
                                    text = parts[0]['text']
                                    title = text[:30] + "..." if len(text) > 30 else text
                                    break
                        except: pass
                        
                    try:
                        last_record = json.loads(lines[-1])
                        parts = last_record.get('message', {}).get('parts', [])
                        if parts and 'text' in parts[0]:
                            full_text = parts[0]['text'].replace('\n', ' ').strip()
                            last_msg_text = full_text[:40] + "..." if len(full_text) > 40 else full_text
                    except: pass
                except:
                    pass
                    
                sessions.append({
                    'id': session_id,
                    'title': title,
                    'last_msg': last_msg_text,
                    'timestamp': timestamp,
                    'date_str': datetime.fromtimestamp(timestamp).strftime("%b %d, %I:%M %p")
                })
            sessions.sort(key=lambda x: x['timestamp'], reverse=True)
        except Exception as e:
            logger.error(f"Error reading all sessions: {e}")
        return sessions

    def load_session(self, session_id: str) -> tuple[str, list[dict], str]:
        """
        Load a specific session's history.
        Reconstructs the linear conversation from parent -> child relationships.
        Returns: (session_id, history_messages, last_uuid)
        """
        file_path = self.chats_dir / f"{session_id}.jsonl"
        if not file_path.exists():
            return session_id, [], None

        records = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"Error reading session file {file_path}: {e}")
            return session_id, [], None

        if not records:
            return session_id, [], None

        # Reconstruct linear history based on UUID tree
        # Map of uuid -> record
        records_by_uuid = {}
        for r in records:
            records_by_uuid.setdefault(r.get('uuid'), []).append(r)
        
        # Aggregate records with same UUID (merge tool calls, etc. as qwen-code does)
        # For our desktop app context, we just grab the latest timestamp version per UUID
        merged_records = {}
        for r_uuid, entries in records_by_uuid.items():
            entries.sort(key=lambda x: x.get('timestamp', ''))
            merged_records[r_uuid] = entries[-1]  # Take latest

        # Find the leaf node (last record in file usually)
        if not merged_records:
            return session_id, [], None
            
        leaf_uuid = records[-1].get('uuid')
        current_uuid = leaf_uuid
        
        # Trace back to root
        uuid_chain = []
        visited = set()
        
        while current_uuid and current_uuid not in visited:
            visited.add(current_uuid)
            uuid_chain.append(current_uuid)
            record = merged_records.get(current_uuid)
            if not record:
                break
            current_uuid = record.get('parentUuid')
            
        uuid_chain.reverse()
        
        # Build API history format
        messages = []
        for u in uuid_chain:
            record = merged_records.get(u)
            if not record: continue
            
            # API expects dictionaries like {"role": "user", "content": "hello"}
            msg_data = record.get('message', {})
            if msg_data:
                role = "assistant" if record.get('type') == 'assistant' else "user"
                
                parts = msg_data.get('parts', [])
                if parts:
                    text_parts = [p.get('text', '') for p in parts if 'text' in p]
                    content = "".join(text_parts)
                    messages.append({
                        "role": role,
                        "content": content
                    })

        return session_id, messages, leaf_uuid


    def save_message(self, session_id: str, role: str, text: str, parent_uuid: str = None) -> str:
        """
        Save a single message to the session's JSONL file.
        Returns the generated UUID for this message, to be used as parent_uuid for the next.
        """
        file_path = self.chats_dir / f"{session_id}.jsonl"
        
        msg_uuid = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        
        record_type = "assistant" if role == "assistant" else "user"
        msg_role = "model" if role == "assistant" else "user"

        record = {
            "uuid": msg_uuid,
            "parentUuid": parent_uuid or "",
            "sessionId": session_id,
            "cwd": self.cwd,
            "timestamp": timestamp,
            "type": record_type,
            "message": {
                "role": msg_role,
                "parts": [
                    {"text": text}
                ]
            }
        }
        
        try:
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record, separators=(',', ':')) + '\n')
        except Exception as e:
            logger.error(f"Error appending to session file {file_path}: {e}")
            
        return msg_uuid
