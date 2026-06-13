import json
import logging
import os
import time
from collections import defaultdict
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

MEMORY_DIR = os.path.join(os.path.expanduser("~"), ".vda-desktop", "memory")


class ShortTermMemory:
    def __init__(self, max_tokens: int = 4096):
        self.max_tokens = max_tokens
        self.entries: list[dict] = []
        self._current_task: Optional[dict] = None
        self._task_steps: list[dict] = []
        self._token_count = 0

    def start_task(self, task: str, context: dict = None):
        self._current_task = {
            "task": task,
            "started_at": time.time(),
            "context": context or {},
            "steps_completed": [],
            "status": "in_progress",
        }
        self._task_steps = []
        logger.info(f"[STM] Task started: {task[:60]}")

    def add_step(self, step: str, result: str = ""):
        entry = {
            "step": step,
            "result": result[:200],
            "timestamp": time.time(),
        }
        self._task_steps.append(entry)
        self.entries.append(entry)
        approx_tokens = len(step) // 4 + len(result) // 4
        self._token_count += approx_tokens
        while self._token_count > self.max_tokens and self.entries:
            removed = self.entries.pop(0)
            self._token_count -= len(removed.get("step", "")) // 4 + len(removed.get("result", "")) // 4
        logger.debug(f"[STM] Step added: {step[:40]}...")

    def complete_task(self, success: bool = True):
        if self._current_task:
            self._current_task["status"] = "completed" if success else "failed"
            self._current_task["ended_at"] = time.time()
            self._current_task["steps_completed"] = list(self._task_steps)
            result = dict(self._current_task)
            self._current_task = None
            self._task_steps = []
            logger.info(f"[STM] Task completed: {result['task'][:40]} -> {'OK' if success else 'FAIL'}")
            return result
        return None

    def get_context(self) -> str:
        if not self._task_steps:
            return ""
        lines = ["[Current Task Context]"]
        for s in self._task_steps:
            lines.append(f"  - {s['step']}: {s['result'][:100]}")
        return "\n".join(lines)

    def compact_if_needed(self, current_tokens: int, max_tokens: int) -> None:
        """Compact short‑term memory if token limit exceeded.

        Simple implementation: clear entries when ``current_tokens`` exceeds
        ``max_tokens``. In a full implementation this would invoke a
        ``SessionCompactor`` to summarise the conversation.
        """
        if current_tokens > max_tokens:
            logger.info(
                "[STM] Token limit exceeded (%d > %d) – compacting memory",
                current_tokens,
                max_tokens,
            )
            self.entries.clear()
            self._token_count = 0
        else:
            logger.debug(
                "[STM] Token count within limits (%d <= %d) – no compaction needed",
                current_tokens,
                max_tokens,
            )



class LongTermMemory:
    def __init__(self):
        self._dir = Path(MEMORY_DIR)
        self._dir.mkdir(parents=True, exist_ok=True)

    def _memory_path(self, key: str) -> Path:
        safe = "".join(c if c.isalnum() or c in '-_' else '_' for c in key)
        return self._dir / f"{safe}.json"

    def save(self, key: str, data: dict):
        path = self._memory_path(key)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        logger.debug(f"[LTM] Saved: {key}")

    def load(self, key: str) -> Optional[dict]:
        path = self._memory_path(key)
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return None

    def delete(self, key: str):
        path = self._memory_path(key)
        if path.exists():
            path.unlink()

    def list_keys(self) -> list[str]:
        return [f.stem for f in self._dir.glob("*.json")]

    def search(self, query: str) -> list[dict]:
        results = []
        q = query.lower()
        for f in self._dir.glob("*.json"):
            if q in f.stem.lower():
                data = json.loads(f.read_text(encoding="utf-8"))
                results.append({"key": f.stem, "data": data})
        return results


class DailyTaskCache:
    def __init__(self):
        self._ltm = LongTermMemory()
        self._daily_key = f"daily_tasks_{time.strftime('%Y%m%d')}"

    def get_today(self) -> list[dict]:
        data = self._ltm.load(self._daily_key)
        return data.get("tasks", []) if data else []

    def add(self, task: str, steps: list[dict], duration: float):
        data = self._ltm.load(self._daily_key) or {"date": time.strftime('%Y-%m-%d'), "tasks": []}
        data["tasks"].append({
            "task": task,
            "steps": steps,
            "duration_s": round(duration, 1),
            "timestamp": time.time(),
        })
        self._ltm.save(self._daily_key, data)

    def find_similar(self, task: str, threshold: float = 0.3) -> Optional[list[dict]]:
        data = self._ltm.load(self._daily_key)
        if not data:
            return None
        task_lower = task.lower()
        task_words = set(task_lower.split())
        matches = []
        for t in data.get("tasks", []):
            t_lower = t["task"].lower()
            t_words = set(t_lower.split())
            if len(task_words & t_words) / max(len(task_words | t_words), 1) >= threshold:
                matches.append(t)
        return matches if matches else None

    def get_frequent(self, min_count: int = 3) -> list[dict]:
        all_tasks = defaultdict(int)
        all_steps = defaultdict(list)
        for f in Path(MEMORY_DIR).glob("daily_tasks_*.json"):
            data = json.loads(f.read_text(encoding="utf-8"))
            for t in data.get("tasks", []):
                task_norm = t["task"].lower().strip()
                all_tasks[task_norm] += 1
                all_steps[task_norm].append(t["steps"])
        return [
            {"task": task, "count": count, "steps": all_steps[task][0] if all_steps[task] else []}
            for task, count in sorted(all_tasks.items(), key=lambda x: -x[1])
            if count >= min_count
        ]
