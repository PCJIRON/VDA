import hashlib
import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

BEHAVIOR_DIR = os.path.join(os.path.expanduser("~"), ".vda-desktop", "behavior")


class BehaviorTracker:
    def __init__(self):
        self._dir = Path(BEHAVIOR_DIR)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._session_actions: list[dict] = []
        self._load_session()

    def _session_path(self) -> Path:
        date = time.strftime('%Y%m%d')
        return self._dir / f"session_{date}.jsonl"

    def _load_session(self):
        path = self._session_path()
        if path.exists():
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            self._session_actions.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass

    def record_action(self, action: str, target: str, success: bool,
                      duration: float, context: str = "", screenshot: str = ""):
        entry = {
            "timestamp": time.time(),
            "action": action,
            "target": target,
            "success": success,
            "duration_s": round(duration, 2),
            "context": context,
        }
        self._session_actions.append(entry)
        with open(self._session_path(), "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        logger.debug(f"[Behavior] Recorded: {action} on {target} -> {'OK' if success else 'FAIL'}")

    def record_task(self, task: str, steps: list[dict], success: bool, total_duration: float):
        entry = {
            "timestamp": time.time(),
            "type": "task",
            "task": task,
            "steps": steps,
            "success": success,
            "total_duration_s": round(total_duration, 2),
            "action_count": len(steps),
        }
        with open(self._session_path(), "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        logger.info(f"[Behavior] Task recorded: {task[:40]} ({len(steps)} steps)")

    def get_frequent_actions(self, min_count: int = 2) -> dict:
        action_counts = {}
        for entry in self._session_actions:
            key = f"{entry['action']}:{entry['target']}"
            if key not in action_counts:
                action_counts[key] = {"count": 0, "success_rate": [], "avg_duration": []}
            action_counts[key]["count"] += 1
            action_counts[key]["success_rate"].append(1 if entry["success"] else 0)
            action_counts[key]["avg_duration"].append(entry["duration_s"])
        result = {}
        for key, data in action_counts.items():
            if data["count"] >= min_count:
                success_rate = sum(data["success_rate"]) / len(data["success_rate"])
                avg_dur = sum(data["avg_duration"]) / len(data["avg_duration"])
                result[key] = {
                    "count": data["count"],
                    "success_rate": round(success_rate, 2),
                    "avg_duration_s": round(avg_dur, 2),
                }
        return result

    def get_frequent_task_patterns(self, min_count: int = 2) -> list[dict]:
        task_patterns = {}
        for f in sorted(self._dir.glob("session_*.jsonl")):
            with open(f, encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        if entry.get("type") == "task":
                            task_key = entry["task"].lower().strip()
                            if task_key not in task_patterns:
                                task_patterns[task_key] = {
                                    "count": 0, "success_count": 0,
                                    "total_duration": 0, "last_steps": []
                                }
                            task_patterns[task_key]["count"] += 1
                            if entry.get("success"):
                                task_patterns[task_key]["success_count"] += 1
                            task_patterns[task_key]["total_duration"] += entry.get("total_duration_s", 0)
                            task_patterns[task_key]["last_steps"] = entry.get("steps", [])
                    except json.JSONDecodeError:
                        pass
        result = []
        for task, data in sorted(task_patterns.items(), key=lambda x: -x[1]["count"]):
            if data["count"] >= min_count:
                result.append({
                    "task": task,
                    "count": data["count"],
                    "success_rate": round(data["success_count"] / data["count"], 2),
                    "avg_duration_s": round(data["total_duration"] / data["count"], 1),
                    "typical_steps": data["last_steps"],
                })
        return result

    def find_similar_actions(self, action: str, target: str) -> Optional[dict]:
        action_lower = action.lower()
        target_lower = target.lower()
        best = None
        best_score = 0
        for entry in self._session_actions:
            score = 0
            if entry["action"].lower() == action_lower:
                score += 0.5
            if target_lower in entry["target"].lower() or entry["target"].lower() in target_lower:
                score += 0.5
            if score > best_score:
                best_score = score
                best = entry
        return best

    def build_graphrag_input(self) -> dict:
        nodes = []
        edges = []
        seen_actions = set()
        seen_targets = set()
        for entry in self._session_actions:
            action_id = f"action_{entry['action']}_{entry['target']}".replace(" ", "_")
            if action_id not in seen_actions:
                seen_actions.add(action_id)
                success_rate = 1.0
                count = 0
                for e2 in self._session_actions:
                    if e2["action"] == entry["action"] and e2["target"] == entry["target"]:
                        count += 1
                        if not e2["success"]:
                            success_rate -= 0.5
                success_rate = max(0, success_rate)
                nodes.append({
                    "id": action_id,
                    "type": "action",
                    "action": entry["action"],
                    "target": entry["target"],
                    "success_rate": round(success_rate / max(count, 1), 2),
                    "frequency": count,
                })
            target_id = f"target_{entry['target']}".replace(" ", "_")
            if target_id not in seen_targets:
                seen_targets.add(target_id)
                nodes.append({
                    "id": target_id,
                    "type": "target",
                    "name": entry["target"],
                })
            edges.append({
                "source": action_id,
                "target": target_id,
                "weight": 1.0,
            })
        task_patterns = self.get_frequent_task_patterns(min_count=1)
        for tp in task_patterns:
            task_id = f"task_{hashlib.md5(tp['task'].encode()).hexdigest()[:8]}"
            nodes.append({
                "id": task_id,
                "type": "task",
                "task": tp["task"],
                "count": tp["count"],
                "success_rate": tp["success_rate"],
            })
            for step in tp.get("typical_steps", []):
                step_target = step.get("target", "")
                if step_target:
                    tid = f"target_{step_target}".replace(" ", "_")
                    edges.append({
                        "source": task_id,
                        "target": tid,
                        "weight": 0.8,
                    })
        return {"nodes": nodes, "edges": edges, "metadata": {"generated_at": time.time()}}
