import json
import re
import logging
import asyncio
from typing import Optional

logger = logging.getLogger(__name__)


TASK_DECOMPOSE_PROMPT = """You are a desktop automation planner. Break down the user's request into sequential steps.

User request: {task}

Previous steps completed:
{context}

Return a JSON array of steps. Each step has:
- "step": short action description (e.g., "Open Chrome browser")
- "action": "type" | "click" | "search" | "wait" | "open" | "scroll" | "complete"
- "target": what to interact with (e.g., "Chrome icon", "YouTube search bar")
- "details": any additional info (e.g., URL, search query)
- "expected_outcome": what should happen after this step

Rules:
1. Max 8-10 steps for complex tasks
2. Each step must be executable with pyautogui/vision
3. Use "wait" steps between actions for page loads
4. Be specific about targets (e.g., "Chrome icon" not "browser icon")
5. For web searches: open browser -> go to site -> find search bar -> type query -> click search

Example for "play chamak challo song on youtube":
[
  {{
    "step": "Open Chrome browser",
    "action": "click",
    "target": "Chrome icon",
    "details": "Find and click Chrome on taskbar/desktop",
    "expected_outcome": "Chrome window opens"
  }},
  {{
    "step": "Wait for Chrome to load",
    "action": "wait",
    "target": "",
    "details": "Wait 2 seconds for page to load",
    "expected_outcome": "Chrome is ready"
  }},
  {{
    "step": "Go to YouTube",
    "action": "type",
    "target": "address bar",
    "details": "https://www.youtube.com",
    "expected_outcome": "YouTube homepage loads"
  }},
  {{
    "step": "Search for chamak challo",
    "action": "click",
    "target": "YouTube search bar",
    "details": "Type 'chamak challo' and press enter",
    "expected_outcome": "Search results appear"
  }},
  {{
    "step": "Click first video",
    "action": "click",
    "target": "first search result",
    "details": "Click the top video result",
    "expected_outcome": "Video starts playing"
  }}
]

Return ONLY valid JSON array, no other text."""


STEP_EXECUTION_PROMPT = """You are performing step {step_num} of a multi-step desktop automation task.

Current step: {step}
Target: {target}
Action type: {action}
Details: {details}

Previous steps completed:
{context}

Available templates (learned UI elements):
{templates}

{screenshot_context}

Return a JSON with:
{{
  "action": "click" | "type" | "wait" | "scroll" | "done",
  "coordinates": [x, y] or null for wait/type,
  "text": "text to type" or "",
  "target_name": "name of the UI element",
  "confidence": 0.0-1.0,
  "status": "success" | "failed" | "skip"
}}

If the action is "type", set coordinates to null and text to what to type, then the system will find and click the target first before typing.
If the step is "wait", return {{"action": "wait", "status": "success"}}.
If the step is already done or can't be done, return appropriate status.

Be precise with coordinates for {screen_width}x{screen_height} screen."""


class TaskDecomposer:
    def __init__(self, api_client, memory_manager=None, daily_cache=None):
        self.api_client = api_client
        self.memory = memory_manager
        self.daily_cache = daily_cache
        self._plan: list[dict] = []
        self._current_step = 0
        self._is_running = False
        self._abort = False

    async def decompose(self, task: str, context: str = "") -> list[dict]:
        prompt = TASK_DECOMPOSE_PROMPT.format(task=task, context=context)
        full_response = ""
        async for chunk in self.api_client.send_message(prompt, []):
            full_response += chunk
        plan = self._parse_plan(full_response)
        self._plan = plan
        logger.info(f"[Planner] Decomposed '{task[:40]}' -> {len(plan)} steps")
        return plan

    def _parse_plan(self, text: str) -> list[dict]:
        json_match = re.search(r'\[.*?\]', text, re.DOTALL)
        if json_match:
            try:
                plan = json.loads(json_match.group(0))
                if isinstance(plan, list):
                    return plan
            except json.JSONDecodeError:
                pass
        logger.warning(f"[Planner] Failed to parse plan, using single step")
        return [{"step": text[:100], "action": "complete", "target": "", "details": text}]

    async def execute_step(self, step: dict, step_num: int, context: str = "",
                           templates: str = "", screenshot_ctx: str = "",
                           screen_w: int = 1920, screen_h: int = 1080) -> dict:
        prompt = STEP_EXECUTION_PROMPT.format(
            step_num=step_num,
            step=step.get("step", ""),
            target=step.get("target", ""),
            action=step.get("action", ""),
            details=step.get("details", ""),
            context=context,
            templates=templates,
            screenshot_context=screenshot_ctx,
            screen_width=screen_w,
            screen_height=screen_h,
        )
        full_response = ""
        async for chunk in self.api_client.send_message(prompt, []):
            full_response += chunk
        result = self._parse_step_result(full_response)
        logger.info(f"[Planner] Step {step_num} result: {result.get('status', 'unknown')}")
        return result

    def _parse_step_result(self, text: str) -> dict:
        json_match = re.search(r'\{.*?"action".*?"status".*?\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        return {"action": "done", "coordinates": None, "text": "",
                "target_name": "", "confidence": 0, "status": "failed"}

    def abort(self):
        self._abort = True

    @property
    def plan(self) -> list[dict]:
        return self._plan

    @property
    def current_step(self) -> int:
        return self._current_step

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def progress(self) -> str:
        total = len(self._plan)
        done = self._current_step
        return f"[{done}/{total}]"
