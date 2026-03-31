"""
TODO List Manager for Vision-Based Task Breakdown.

Breaks down complex tasks into smaller subtasks and tracks execution.
"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Task:
    """Represents a single task or subtask."""
    id: str
    title: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    action: Optional[str] = None  # e.g., "click", "type", "double_click"
    target: Optional[str] = None  # e.g., "Chrome icon", "Search button"
    coordinates: Optional[Dict[str, int]] = None  # {"x": 100, "y": 200}
    text_input: Optional[str] = None  # Text to type
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status.value,
            'action': self.action,
            'target': self.target,
            'coordinates': self.coordinates,
            'text_input': self.text_input,
            'error': self.error,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
    
    def start(self):
        """Mark task as in progress."""
        self.status = TaskStatus.IN_PROGRESS
        logger.info(f"Task started: {self.title}")
    
    def complete(self):
        """Mark task as completed."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        logger.info(f"Task completed: {self.title}")
    
    def fail(self, error: str):
        """Mark task as failed."""
        self.status = TaskStatus.FAILED
        self.error = error
        logger.error(f"Task failed: {self.title} - {error}")
    
    def skip(self):
        """Mark task as skipped."""
        self.status = TaskStatus.SKIPPED
        logger.info(f"Task skipped: {self.title}")


@dataclass
class TaskList:
    """Represents a list of tasks for a complex operation."""
    id: str
    title: str
    description: str
    tasks: List[Task] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    def add_task(self, task: Task):
        """Add a task to the list."""
        self.tasks.append(task)
        logger.info(f"Task added to list: {task.title}")
    
    def get_next_pending(self) -> Optional[Task]:
        """Get the next pending task."""
        for task in self.tasks:
            if task.status == TaskStatus.PENDING:
                return task
        return None
    
    def get_current(self) -> Optional[Task]:
        """Get the currently in-progress task."""
        for task in self.tasks:
            if task.status == TaskStatus.IN_PROGRESS:
                return task
        return None
    
    def all_completed(self) -> bool:
        """Check if all tasks are completed."""
        return all(
            task.status in [TaskStatus.COMPLETED, TaskStatus.SKIPPED]
            for task in self.tasks
        )
    
    def progress(self) -> tuple:
        """Get progress as (completed, total) tuple."""
        completed = sum(
            1 for task in self.tasks 
            if task.status in [TaskStatus.COMPLETED, TaskStatus.SKIPPED]
        )
        return (completed, len(self.tasks))
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status.value,
            'tasks': [task.to_dict() for task in self.tasks],
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'progress': list(self.progress())
        }


class TaskManager:
    """
    Manages task breakdown and execution.
    
    Usage:
        manager = TaskManager()
        task_list = manager.create_task_list("Open Chrome and search")
        # ... add tasks ...
        manager.execute_task_list(task_list)
    """
    
    def __init__(self):
        """Initialize task manager."""
        self.active_lists: List[TaskList] = []
        self.completed_lists: List[TaskList] = []
    
    def create_task_list(self, title: str, description: str = "") -> TaskList:
        """Create a new task list."""
        import uuid
        task_list = TaskList(
            id=f"task_{uuid.uuid4().hex[:8]}",
            title=title,
            description=description
        )
        self.active_lists.append(task_list)
        logger.info(f"Task list created: {title}")
        return task_list
    
    def add_task_to_list(self, task_list: TaskList, task: Task):
        """Add a task to a task list."""
        task_list.add_task(task)
    
    def parse_llm_breakdown(self, llm_response: str) -> TaskList:
        """
        Parse LLM response to create task list.
        
        Expected LLM response format:
        ```json
        {
            "title": "Open Chrome and search for Python",
            "tasks": [
                {
                    "title": "Click on Chrome icon",
                    "action": "click",
                    "target": "Chrome icon"
                },
                {
                    "title": "Type search query",
                    "action": "type",
                    "text_input": "Python tutorial"
                }
            ]
        }
        ```
        """
        import json
        import re
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
        if not json_match:
            logger.error("No JSON found in LLM response")
            return None
        
        try:
            data = json.loads(json_match.group(0))
            
            task_list = self.create_task_list(
                title=data.get('title', 'Untitled Task'),
                description=data.get('description', '')
            )
            
            for task_data in data.get('tasks', []):
                task = Task(
                    id=f"task_{len(task_list.tasks) + 1}",
                    title=task_data.get('title', 'Untitled'),
                    description=task_data.get('description', ''),
                    action=task_data.get('action'),
                    target=task_data.get('target'),
                    coordinates=task_data.get('coordinates'),
                    text_input=task_data.get('text_input')
                )
                task_list.add_task(task)
            
            logger.info(f"Parsed {len(task_list.tasks)} tasks from LLM response")
            return task_list
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return None
    
    def get_task_breakdown_prompt(self, user_query: str, screenshot_description: str = "") -> str:
        """
        Get prompt for LLM to break down complex computer operator tasks.
        
        Args:
            user_query: User's complex query
            screenshot_description: Optional description of current screen state
        
        Returns:
            Prompt string for LLM with detailed computer operator instructions
        """
        env_context = f"""
**📸 CURRENT SCREEN STATE:**
{screen_description}

""" if screenshot_description else ""

        return f"""You are an expert **Computer Operator AI Agent** with VISION capabilities. 
Your job is to break down complex computer tasks into simple, executable steps.

**🎯 USER'S REQUEST:**
"{user_query}"
{env_context}
---

## 📋 YOUR TASK:

Analyze the user's request ALONG WITH the current screen state (if provided).
Create a **detailed TODO list** that considers:

1. **What is currently visible on screen?** (use screenshot description)
2. **What applications are already open?**
3. **What is the FIRST step needed?**
4. **What buttons/text are visible that can be clicked?**
5. **What is the most efficient path to complete the task?**

---

## 🔧 AVAILABLE ACTIONS:

| Action | Description | Required Fields |
|--------|-------------|-----------------|
| `open_app` | Open an application | `target` (app name) |
| `click` | Click on a button/icon | `target` (what to click) |
| `double_click` | Double-click on something | `target` (what to click) |
| `right_click` | Right-click on something | `target` (what to click) |
| `type` | Type text into a field | `text_input` (what to type) |
| `press_key` | Press a keyboard key | `text_input` (key name) |
| `shortcut` | Use keyboard shortcut | `text_input` (e.g., "Ctrl+V") |
| `scroll` | Scroll up/down | `text_input` ("up" or "down") |
| `wait` | Wait for UI to load | `text_input` (seconds) |
| `find_text` | Locate text on screen (uses OCR) | `target` (text to find) |

---

## 📝 OUTPUT FORMAT:

Respond **ONLY** with valid JSON in this exact format:

```json
{{
    "title": "Clear title of the overall task",
    "description": "Brief description of what will be accomplished",
    "estimated_steps": 5,
    "current_state": "What is currently visible/active on screen",
    "tasks": [
        {{
            "id": 1,
            "title": "Open Google Chrome",
            "description": "Launch Chrome browser from taskbar or desktop",
            "action": "open_app",
            "target": "Google Chrome",
            "ocr_fallback": true
        }},
        {{
            "id": 2,
            "title": "Wait for Chrome to load",
            "description": "Wait for browser to fully load",
            "action": "wait",
            "text_input": "3"
        }}
    ]
}}
```

---

## ⚠️ IMPORTANT RULES:

1. **Analyze current screen first** - What's already open?
2. **Break into SMALLEST possible steps** - One action per step
3. **Include WAIT steps** after opening apps (2-3 seconds)
4. **Be SPECIFIC with target names** - Use visible text when possible
5. **Use OCR when needed** - Set `ocr_fallback: true` for text buttons
6. **Include ALL necessary steps** - Don't skip steps like "wait for load"
7. **Think like a computer operator** - Step-by-step approach
8. **Adapt to current state** - If Chrome already open, don't open again

---

## 🎯 EXAMPLES:

### Example 1: Desktop visible, user says "Open Notepad"
```json
{{
    "title": "Open Notepad",
    "description": "Launch Notepad application",
    "current_state": "Windows desktop visible, taskbar at bottom",
    "estimated_steps": 2,
    "tasks": [
        {{"id": 1, "title": "Open Notepad", "action": "open_app", "target": "Notepad", "ocr_fallback": true}},
        {{"id": 2, "title": "Wait for Notepad", "action": "wait", "text_input": "2"}}
    ]
}}
```

### Example 2: Chrome already open, user says "Search for Python"
```json
{{
    "title": "Search for Python on Google",
    "description": "Use existing Chrome window to search",
    "current_state": "Google Chrome open with Google homepage visible",
    "estimated_steps": 3,
    "tasks": [
        {{"id": 1, "title": "Click search box", "action": "click", "target": "Google search box", "ocr_fallback": true}},
        {{"id": 2, "title": "Type Python", "action": "type", "text_input": "Python"}},
        {{"id": 3, "title": "Press Enter", "action": "press_key", "text_input": "Enter"}}
    ]
}}
```

### Example 3: VS Code open, user says "Save as test.py"
```json
{{
    "title": "Save file as test.py",
    "description": "Save current file in VS Code",
    "current_state": "VS Code open with unsaved file",
    "estimated_steps": 4,
    "tasks": [
        {{"id": 1, "title": "Click File menu", "action": "click", "target": "File", "ocr_fallback": true}},
        {{"id": 2, "title": "Click Save As", "action": "click", "target": "Save As", "ocr_fallback": true}},
        {{"id": 3, "title": "Type filename", "action": "type", "text_input": "test.py"}},
        {{"id": 4, "title": "Click Save button", "action": "click", "target": "Save", "ocr_fallback": true}}
    ]
}}
```

---

## 🚀 NOW ANALYZE AND BREAK DOWN:

**User Request:** "{user_query}"
{env_context}
**Think step-by-step:**
1. What is currently on screen?
2. What is the first action needed?
3. What can be clicked/typed right now?
4. How many steps to complete?

**Respond with JSON ONLY - no explanation, no markdown except for the JSON code block.**"""
    
    def execute_task_list(self, task_list: TaskList, executor) -> bool:
        """
        Execute all tasks in a task list with retry logic.
        
        Each task will be retried until completed or max retries reached.
        After each attempt, a fresh screenshot is taken to verify completion.
        
        Args:
            task_list: TaskList to execute
            executor: Function that executes individual tasks
                     Signature: executor(task, screenshot) -> bool
        
        Returns:
            True if all tasks completed successfully
        """
        import time
        
        MAX_RETRIES = 3
        RETRY_DELAY = 2  # seconds between retries
        
        task_list.status = TaskStatus.IN_PROGRESS
        logger.info(f"Starting task list execution: {task_list.title}")
        
        while True:
            next_task = task_list.get_next_pending()
            if not next_task:
                break
            
            # Try task with retries
            attempt = 0
            task_completed = False
            
            while attempt < MAX_RETRIES and not task_completed:
                attempt += 1
                logger.info(f"Executing task '{next_task.title}' (attempt {attempt}/{MAX_RETRIES})")
                
                next_task.start()
                
                try:
                    # Take fresh screenshot before execution
                    import pyautogui
                    screenshot = pyautogui.screenshot()
                    
                    # Execute task with screenshot
                    success = executor(next_task, screenshot)
                    
                    if success:
                        # Verify task completion with another screenshot
                        time.sleep(1)  # Wait for UI to update
                        verify_screenshot = pyautogui.screenshot()
                        
                        # Re-verify the task state
                        verification = executor(next_task, verify_screenshot, verify_only=True)
                        
                        if verification:
                            next_task.complete()
                            task_completed = True
                            logger.info(f"✅ Task completed: {next_task.title}")
                        else:
                            logger.warning(f"Task verification failed, will retry: {next_task.title}")
                            time.sleep(RETRY_DELAY)
                    else:
                        logger.warning(f"Task execution failed, will retry: {next_task.title}")
                        time.sleep(RETRY_DELAY)
                        
                except Exception as e:
                    logger.error(f"Task execution error (attempt {attempt}): {e}")
                    time.sleep(RETRY_DELAY)
            
            # Mark as failed if max retries reached
            if not task_completed:
                next_task.fail(f"Failed after {MAX_RETRIES} attempts")
                logger.error(f"❌ Task failed after {MAX_RETRIES} attempts: {next_task.title}")
        
        # Update overall status
        if task_list.all_completed():
            task_list.status = TaskStatus.COMPLETED
            task_list.completed_at = datetime.now()
            logger.info(f"✅ Task list completed: {task_list.title}")
            return True
        else:
            task_list.status = TaskStatus.FAILED
            logger.warning(f"❌ Task list failed: {task_list.title}")
            return False
