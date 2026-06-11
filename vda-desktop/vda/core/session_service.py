import os
import json
import uuid
import hashlib
from pathlib import Path
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


def get_project_hash(cwd: str) -> str:
    normalized_path = os.path.normpath(cwd).replace("\\", "/").lower()
    return hashlib.sha256(normalized_path.encode('utf-8')).hexdigest()[:16]


class SessionService:
    def __init__(self, cwd: str = None):
        self.cwd = cwd or os.getcwd()
        self.project_hash = get_project_hash(self.cwd)
        home = Path.home()
        self.chats_dir = home / ".vda-desktop" / "sessions" / self.project_hash / "chats"
        self.chats_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized SessionService. Chats dir: {self.chats_dir}")

    def load_last_session(self) -> tuple[str, list[dict], str]:
        try:
            files = list(self.chats_dir.glob("*.jsonl"))
            if not files:
                return None, [], None
            files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            most_recent_file = files[0]
            session_id = most_recent_file.stem
            return self.load_session(session_id)
        except Exception as e:
            logger.error(f"Error loading last session: {e}", exc_info=True)
            return None, [], None

    def get_all_sessions(self) -> list[dict]:
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
                                    title = text[:20] + "..." if len(text) > 20 else text
                                    break
                        except:
                            pass
                    try:
                        last_record = json.loads(lines[-1])
                        parts = last_record.get('message', {}).get('parts', [])
                        if parts and 'text' in parts[0]:
                            full_text = parts[0]['text'].replace('\n', ' ').strip()
                            last_msg_text = full_text[:22] + "..." if len(full_text) > 22 else full_text
                    except:
                        pass
                except:
                    pass
                sessions.append({
                    'id': session_id,
                    'title': title,
                    'last_msg': last_msg_text,
                    'timestamp': timestamp,
                    'date_str': datetime.fromtimestamp(timestamp).strftime("%b %d, %I:%M %p"),
                })
            sessions.sort(key=lambda x: x['timestamp'], reverse=True)
        except Exception as e:
            logger.error(f"Error reading all sessions: {e}")
        return sessions

    def load_session(self, session_id: str) -> tuple[str, list[dict], str]:
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

        records_by_uuid = {}
        for r in records:
            records_by_uuid.setdefault(r.get('uuid'), []).append(r)

        merged_records = {}
        for r_uuid, entries in records_by_uuid.items():
            entries.sort(key=lambda x: x.get('timestamp', ''))
            merged_records[r_uuid] = entries[-1]

        if not merged_records:
            return session_id, [], None

        leaf_uuid = records[-1].get('uuid')
        current_uuid = leaf_uuid

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

        messages = []
        for u in uuid_chain:
            record = merged_records.get(u)
            if not record:
                continue
            msg_data = record.get('message', {})
            if msg_data:
                role = "assistant" if record.get('type') == 'assistant' else "user"
                parts = msg_data.get('parts', [])
                if parts:
                    text_parts = [p.get('text', '') for p in parts if 'text' in p]
                    content = "".join(text_parts)
                    attachments = [p for p in parts if p.get('type') == 'image_url' or 'image_url' in p]
                    messages.append({
                        "role": role,
                        "content": content,
                        "attachments": attachments,
                    })

        return session_id, messages, leaf_uuid

    def save_message(self, session_id: str, role: str, text: str, attachments: list = None, parent_uuid: str = None) -> str:
        file_path = self.chats_dir / f"{session_id}.jsonl"
        msg_uuid = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        record_type = "assistant" if role == "assistant" else "user"
        msg_role = "model" if role == "assistant" else "user"

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

        record = {
            "uuid": msg_uuid,
            "parentUuid": parent_uuid or "",
            "sessionId": session_id,
            "cwd": self.cwd,
            "timestamp": timestamp,
            "type": record_type,
            "message": {
                "role": msg_role,
                "parts": parts,
            },
        }

        try:
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record, separators=(',', ':')) + '\n')
        except Exception as e:
            logger.error(f"Error appending to session file {file_path}: {e}")

        return msg_uuid
