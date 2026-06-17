"""AgentManager — state machine driving the re-plan-per-step agent loop.

The state machine transitions through IDLE → INIT → PLAN → EXECUTE → VERIFY
→ PLAN (re-plan) → EXECUTE → ... → COMPLETE / ERROR, with a PAUSED state
for user intervention (doom loop detection, permission requests).

The key design change vs the old static-plan design: PLAN is invoked once
per step. Each PLAN call:
  1. Takes a fresh screenshot of the desktop
  2. Sends the user's task + completed-steps history + screenshot to the LLM
  3. Asks the LLM for the NEXT single action (or "done")
This gives 1 LLM call per step (vs 2-3 in the old design) and lets the
agent re-evaluate the screen state after every action — the next plan
IS the verification.

Each state is handled by a dedicated async method, dispatched via a dict
mapping states to handlers.
"""

import asyncio
import enum
import json
import logging
import os
import re
import time
from typing import Any, Callable, Optional

from vda.config.defaults import PROVIDERS
from vda.core.agent_manager.doom_detector import DoomLoopDetector
from vda.core.agent_manager.permission_system import PermissionSystem
from vda.core.agent_manager.session_compactor import SessionCompactor
from vda.core.default_prompt import build_system_prompt

logger = logging.getLogger(__name__)


class AgentState(enum.Enum):
    """Agent lifecycle states.

    States:
        IDLE: Initial state before any task is started.
        INIT: Collecting user input and setting up context.
        PLAN: Take a fresh screenshot, ask LLM for the NEXT single action
              (or `done: true` if the task is finished).
        EXECUTE: Hand the current step to the worker for execution.
        VERIFY: No-op transition — the next PLAN re-evaluates the screen,
                which is the implicit verification.
        COMPLETE: Task finished successfully (LLM said `done: true`).
        ERROR: Unrecoverable error (e.g., max iterations exceeded).
        PAUSED: Suspended waiting for user intervention.
    """

    IDLE = "idle"
    INIT = "init"
    PLAN = "plan"
    EXECUTE = "execute"
    VERIFY = "verify"
    COMPLETE = "complete"
    ERROR = "error"
    PAUSED = "paused"
    SIFT_VERIFY = "sift_verify"


# Type for the injected screenshot callable. Returns a base64-encoded
# PNG/JPEG string (with the data: URI prefix stripped — the agent adds
# the prefix back when building the OpenAI-style content block).
ScreenshotFn = Callable[[], Optional[str]]


class AgentManager:
    """State machine driving the re-plan-per-step loop.

    The AgentManager is a pure state machine — it does NOT extend QThread.
    It accepts an API client, tool registry, optional settings, an
    optional screenshot callable, and returns results via its step()
    method. The AgentWorker QThread wraps this class and emits signals
    for UI updates.

    Args:
        api_client: API client for LLM calls (per-step plan-and-decide).
        tool_registry: ToolRegistry instance for executing tool steps.
        settings: Optional settings object/dict for configuration values.
        max_iterations: Maximum number of PLAN iterations before ERROR.
        screenshot_fn: Callable that returns a base64-encoded image of the
            current desktop (no data: URI prefix). Required for vision mode.
    """

    def __init__(
        self,
        api_client: Any,
        tool_registry: Any,
        settings: Optional[Any] = None,
        max_iterations: int = 30,
        screenshot_fn: Optional[ScreenshotFn] = None,
        vision_executor: Optional[Any] = None,
        components: Optional[list[dict[str, Any]]] = None,
        vision_mode: bool = True,
    ) -> None:
        self.api_client = api_client
        self.tool_registry = tool_registry
        self.settings = settings
        self.max_iterations = max_iterations
        self.screenshot_fn = screenshot_fn
        self.vision_mode = vision_mode
        # vision_executor (EnhancedExecutor) executes vision actions
        # directly (click/type/scroll) — bypasses the tool registry which
        # only knows about generic tool names like 'uied'.
        self.vision_executor = vision_executor
        # Saved UIED template components — used in the system prompt so
        # the LLM can reference known element names (e.g. "Chrome")
        # even when the model can't process screenshots.
        self.components = components or []

        # State
        self.state = AgentState.IDLE
        self.plan: list[dict[str, Any]] = []
        self.current_step: int = 0
        self.iteration_count: int = 0
        self.results: list[dict[str, Any]] = []
        self.completed_steps: list[dict[str, Any]] = []  # history for next PLAN
        self.last_summary: str = ""  # populated when LLM says done: true

        # Subsystems
        self.doom_detector = DoomLoopDetector()
        self.permission_system = PermissionSystem(settings)
        self.compactor = SessionCompactor(
            api_client=api_client,
            threshold=settings.get("compaction_threshold", 0.8) if (hasattr(settings, "get") if settings else False) else 0.8,
            max_tokens=settings.get("compaction_max_tokens", 128000) if (hasattr(settings, "get") if settings else False) else 128000,
        )

        # Session & cost tracking (matches opencode's session hierarchy + cost propagation)
        self.session_service: Optional[Any] = None
        self._session_id: Optional[str] = None
        self.agent_type: str = "main"
        self.total_prompt_tokens: int = 0
        self.total_completion_tokens: int = 0
        self.total_cost: float = 0.0

        # Internal state
        self._on_step: Optional[Callable] = None  # callback for sub-agent step reporting
        self._error: Optional[str] = None
        self._paused_reason: Optional[str] = None
        self._sift_verify_data: Optional[dict[str, Any]] = None
        self._user_input: str = ""
        self._context: str = ""
        self._compacted_context: str = ""  # filled by SessionCompactor on overflow
        self._model_tier: str = "standard"  # "standard", "free", "claude", "gemini"

        # State dispatch table
        self._handlers = {
            AgentState.INIT: self._handle_init,
            AgentState.PLAN: self._handle_plan,
            AgentState.EXECUTE: self._handle_execute,
            AgentState.VERIFY: self._handle_verify,
            AgentState.COMPLETE: self._handle_complete,
            AgentState.ERROR: self._handle_error,
            AgentState.SIFT_VERIFY: self._handle_sift_verify,
        }

    def reset(self) -> None:
        """Reset all state to initial values.

        Returns the manager to IDLE state with no plan, results, or errors.
        """
        self.state = AgentState.IDLE
        self.plan = []
        self.current_step = 0
        self.iteration_count = 0
        self.results = []
        self.completed_steps = []
        self.last_summary = ""
        self._error = None
        self._paused_reason = None
        self._sift_verify_data = None
        self._user_input = ""
        self._context = ""
        self.doom_detector.clear()
        self.permission_system.clear_cache()
        self.compactor.reset()
        logger.info("[AgentManager] Reset to IDLE")

    async def run_to_completion_async(self) -> str:
        """Run the agent loop autonomously to completion (for sub-agents).

        Returns:
            The final summary text if successful, or an error string.
        """
        while self.state not in (AgentState.COMPLETE, AgentState.ERROR):
            if self.state == AgentState.PAUSED:
                self.state = AgentState.ERROR
                self._error = f"Sub-agent required user intervention (paused) and aborted: {self._error}"
                break

            state, event_data = await self.step()

            if event_data and event_data.get("event") == "execute_step":
                step_dict = event_data.get("step", {})
                tool_name = step_dict.get("tool")
                args = step_dict.get("args", {})

                # Report step to parent UI via callback
                if self._on_step:
                    self._on_step(tool_name, args, "started")

                try:
                    tool = self.tool_registry.get_tool(tool_name)
                    if not tool:
                        result = f"Error: Tool '{tool_name}' not found in registry."
                        success = False
                    elif not hasattr(tool, "execute"):
                        result = f"Error: Tool '{tool_name}' has no execute method."
                        success = False
                    else:
                        # Inject session context for sub-agent tool
                        if hasattr(tool, "api_client"):
                            tool.api_client = self.api_client
                        if hasattr(tool, "session_service"):
                            tool.session_service = self.session_service
                        if hasattr(tool, "parent_session_id"):
                            tool.parent_session_id = self._session_id

                        import inspect
                        if inspect.iscoroutinefunction(tool.execute):
                            result = await tool.execute(**args)
                        else:
                            result = tool.execute(**args)
                        result = str(result)
                        success = True
                except Exception as e:
                    result = f"Error executing {tool_name}: {e}"
                    success = False

                self.record_step_outcome(step_dict, result, success)

                # Report completion to parent UI
                if self._on_step:
                    self._on_step(tool_name, args, "completed" if success else "failed", result[:200])

        if self.state == AgentState.ERROR:
            return f"Error: {self._error}"

        return getattr(self, "last_summary", "Task completed without summary")

    async def step(self) -> tuple[AgentState, Optional[dict[str, Any]]]:
        """Execute one state transition.

        Dispatches to the appropriate handler based on current state.
        If in PAUSED state, returns immediately without transitioning.

        Returns:
            Tuple of (next_state, optional_output_dict). The output dict
            contains event-specific data (plan, step info, results, etc.).
        """
        if self.state == AgentState.PAUSED:
            return self.state, {"event": "paused", "reason": self._paused_reason}

        handler = self._handlers.get(self.state)
        if handler is None:
            # IDLE or unknown state — no transition
            return self.state, None

        return await handler()

    async def _handle_sift_verify(self) -> tuple[AgentState, Optional[dict[str, Any]]]:
        """Handle SIFT_VERIFY: LLM checks if the SIFT fallback location is correct.

        Flow:
          - LLM says yes → execute click at SIFT coords, go to VERIFY
          - LLM says no → fall back to original LLM coords, execute click there, go to VERIFY
          - Exception → fall back to LLM coords, go to VERIFY
        """
        logger.info("[AgentManager] LLM Verification for SIFT fallback started.")
        if not self._sift_verify_data:
            # No data — just replan
            self.state = AgentState.PLAN
            return self.state, {"event": "verify_replan"}

        data = self._sift_verify_data
        target_name = data.get("target_name", "unknown target")
        sift_x, sift_y = data.get("x", 0), data.get("y", 0)
        original_parsed = data.get("original_parsed", {})
        llm_x = original_parsed.get("x", 0)
        llm_y = original_parsed.get("y", 0)

        b64_image = None
        if self.screenshot_fn:
            b64_image = self.screenshot_fn()

            # Draw a red circle on the image at (sift_x, sift_y)
            try:
                import base64

                import cv2
                import numpy as np
                img_data = base64.b64decode(b64_image)
                nparr = np.frombuffer(img_data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                cv2.circle(img, (sift_x, sift_y), 20, (0, 0, 255), 3)
                _, buffer = cv2.imencode('.jpg', img)
                b64_image = base64.b64encode(buffer).decode('utf-8')
            except Exception as e:
                logger.error(f"[AgentManager] Failed to draw circle for SIFT verify: {e}")

        messages = [
            {"role": "user", "content": [
                {"type": "text", "text": f"SIFT fallback matched the target '{target_name}'. I drew a red circle at the matched location. Please verify if the red circle is exactly on the correct target. If YES, reply 'verified: true'. If NO, reply 'no template matching here'."}
            ]}
        ]

        if b64_image:
            messages[0]["content"].append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}})

        try:
            content = ""
            async for chunk in self.api_client.chat(messages):
                content += chunk
            logger.info(f"[AgentManager] SIFT verification LLM response: {content}")

            if "no template matching here" in content.lower() or "not on the correct target" in content.lower():
                # SIFT was wrong — fall back to LLM coordinates
                logger.info(f"[AgentManager] SIFT rejected. Falling back to LLM coords ({llm_x}, {llm_y}).")
                if self.vision_executor and llm_x != 0 and llm_y != 0:
                    fallback_parsed = dict(original_parsed)
                    fallback_parsed.pop("target_name", None)  # Don't re-trigger template matching
                    self.vision_executor.execute(fallback_parsed)
                    self.record_step_outcome(
                        self.plan[self.current_step],
                        f"SIFT rejected, clicked at LLM coords ({llm_x}, {llm_y})",
                        True,
                    )
                else:
                    self.record_step_outcome(
                        self.plan[self.current_step],
                        "SIFT rejected, no valid LLM fallback coords",
                        False,
                    )
                self.state = AgentState.PLAN
                self._sift_verify_data = None
                return self.state, {"event": "verify_replan"}

            elif re.search(r'\bverified:\s*true\b', content.lower()) or "correct target" in content.lower():
                # SIFT was correct — execute click at SIFT coords
                logger.info(f"[AgentManager] SIFT verified! Clicking at ({sift_x}, {sift_y}).")
                if self.vision_executor:
                    verified_parsed = dict(original_parsed)
                    verified_parsed["x"] = sift_x
                    verified_parsed["y"] = sift_y
                    verified_parsed["sift_verified"] = True
                    verified_parsed.pop("target_name", None)
                    self.vision_executor.execute(verified_parsed)
                self.record_step_outcome(
                    self.plan[self.current_step],
                    f"SIFT verified, clicked at ({sift_x}, {sift_y})",
                    True,
                )
                self.state = AgentState.PLAN
                self._sift_verify_data = None
                return self.state, {"event": "verify_replan"}

            else:
                # Ambiguous response — fall back to LLM coords
                logger.info(f"[AgentManager] SIFT ambiguous response. Falling back to LLM coords ({llm_x}, {llm_y}).")
                if self.vision_executor and llm_x != 0 and llm_y != 0:
                    fallback_parsed = dict(original_parsed)
                    fallback_parsed.pop("target_name", None)
                    self.vision_executor.execute(fallback_parsed)
                    self.record_step_outcome(
                        self.plan[self.current_step],
                        f"SIFT ambiguous, clicked at LLM coords ({llm_x}, {llm_y})",
                        True,
                    )
                else:
                    self.record_step_outcome(
                        self.plan[self.current_step],
                        "SIFT ambiguous, no valid LLM fallback coords",
                        False,
                    )
                self.state = AgentState.PLAN
                self._sift_verify_data = None
                return self.state, {"event": "verify_replan"}

        except Exception as e:
            logger.error(f"[AgentManager] SIFT verify LLM call failed: {e}")
            # On exception, just use LLM coords and continue
            if self.vision_executor and llm_x != 0 and llm_y != 0:
                fallback_parsed = dict(original_parsed)
                fallback_parsed.pop("target_name", None)
                self.vision_executor.execute(fallback_parsed)
            self.record_step_outcome(
                self.plan[self.current_step],
                f"SIFT verify failed ({e}), used LLM coords",
                True,
            )
            self.state = AgentState.PLAN
            self._sift_verify_data = None
            return self.state, {"event": "verify_replan"}

    async def _handle_init(self) -> tuple[AgentState, Optional[dict[str, Any]]]:
        """Handle INIT state: set up iteration count, transition to PLAN."""
        self.iteration_count = 0
        self.completed_steps = []
        self.state = AgentState.PLAN
        logger.debug("[AgentManager] INIT → PLAN")
        return self.state, {"event": "init_complete", "input": self._user_input}

    async def _handle_plan(self) -> tuple[AgentState, Optional[dict[str, Any]]]:
        """Handle PLAN state: take screenshot (if vision_mode), ask LLM for next action.

        This is the heart of the re-plan-per-step design. Each call:
        1. Increments the iteration counter
        2. Captures a fresh screenshot (if screenshot_fn is provided and vision_mode is True)
        3. Builds a system prompt (vision vs text-agent)
        4. Sends ONE LLM call
        5. Parses the response:
           - {done: true, summary: ...} → transition to COMPLETE
           - {action, target, ...} (vision) or {tool, args, ...} (text) → set plan = [single action], go to EXECUTE
           - parse failure → safe fallback action (return description only)
        """
        if self.iteration_count >= self.max_iterations:
            self.last_summary = self._synthesize_loop_summary()
            self.state = AgentState.COMPLETE
            logger.warning("[AgentManager] Max iterations (%s) — force-completing with gathered data", self.max_iterations)
            return self.state, {"event": "plan_done", "summary": self.last_summary}

        # Force-complete if stuck in a read-only loop (same tools, no progress)
        if self._is_stuck_in_readonly_loop():
            self.last_summary = self._synthesize_loop_summary()
            self.state = AgentState.COMPLETE
            logger.warning("[AgentManager] Read-only loop detected — force-completing with gathered data")
            return self.state, {"event": "plan_done", "summary": self.last_summary}

        self.iteration_count += 1

        # Rate-limit delay between PLAN iterations to avoid 429 on
        # providers with strict RPM limits (e.g. NVIDIA NIM).
        await self._apply_rate_limit_delay()

        # 1. Capture screenshot (only in vision mode)
        screenshot_b64 = None
        if self.vision_mode and self.screenshot_fn is not None:
            try:
                screenshot_b64 = self.screenshot_fn()
            except Exception as e:
                logger.warning("[AgentManager] Screenshot capture failed: %s", e)

        # 2. Build the per-turn LLM message
        history_block = self._format_step_history()

        skills_content = ""
        if hasattr(self, "settings") and self.settings:
            skills_path = self.settings.get("skills_md_path")
            if skills_path and os.path.exists(skills_path):
                try:
                    with open(skills_path, encoding="utf-8") as f:
                        skills_content = f.read()
                except Exception as e:
                    logger.warning(f"Failed to read skills file: {e}")

        model_id = ""
        if self.settings:
            if hasattr(self.settings, "get"):
                model_id = self.settings.get("model", "")
            elif isinstance(self.settings, dict):
                model_id = self.settings.get("model", "")

        # Detect model tier for per-model parsing tuning
        mid = model_id.lower()
        if any(tag in mid for tag in ("free", "mimo", "minimax", "nemotron")):
            self._model_tier = "free"
        elif "claude" in mid:
            self._model_tier = "claude"
        elif "gemini" in mid:
            self._model_tier = "gemini"
        else:
            self._model_tier = "standard"

        if self.vision_mode:
            try:
                sw, sh = self._get_screen_size()
            except Exception:
                sw, sh = 1920, 1080

            system_prompt = build_system_prompt(
                screen_width=sw,
                screen_height=sh,
                components=self.components,
                vision_mode=True,
                skills_content=skills_content,
                agent_type=self.agent_type,
                model_id=model_id,
            )

            user_text = self._build_user_prompt(history_block)

            bg_results_block = self._check_background_tasks()
            if bg_results_block:
                user_text += bg_results_block

            if screenshot_b64:
                user_content = [
                    {"type": "text", "text": user_text},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{screenshot_b64}",
                        },
                    },
                ]
            else:
                user_content = user_text
        else:
            # Normal/Sub-agent mode: no screenshots, use text prompt
            tool_defs = self.tool_registry.get_definitions(agent_type=self.agent_type)

            # Check if this provider supports native OpenAI-compatible function calling
            uses_native_tc = hasattr(self.api_client, "supports_tool_calling") and self.api_client.supports_tool_calling()

            if uses_native_tc:
                # Native tool calling mode (opencode-style): tools defined via API
                system_prompt = build_system_prompt(
                    vision_mode=False,
                    skills_content=skills_content,
                    text_agent=True,
                    tool_definitions=tool_defs,
                    agent_type=self.agent_type,
                    model_id=model_id,
                    native_tool_calling=True,
                )
                bg_results_block = self._check_background_tasks()
                user_content = (
                    f"USER TASK: {self._user_input}\n\n"
                    f"STEPS COMPLETED SO FAR:\n{history_block}"
                    f"{bg_results_block}"
                )
            else:
                # JSON-in-text mode (fallback for providers without native tool calling)
                system_prompt = build_system_prompt(
                    vision_mode=False,
                    skills_content=skills_content,
                    text_agent=self.agent_type == "main",
                    tool_definitions=tool_defs,
                    agent_type=self.agent_type,
                    model_id=model_id,
                    native_tool_calling=False,
                )
                bg_results_block = self._check_background_tasks()
                user_content = (
                    f"USER TASK: {self._user_input}\n\n"
                    f"STEPS COMPLETED SO FAR:\n{history_block}\n\n"
                    "Reply with a JSON tool call or {\"done\": true, \"summary\": \"...\"} if complete."
                    f"{bg_results_block}"
                )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        # 3. ONE LLM call for decide + verify (the next screenshot IS the verify)
        full_response = ""
        prompt_text = json.dumps(messages)

        if not self.vision_mode and uses_native_tc:
            # Native tool calling path (opencode-style)
            tool_calls_received = []
            try:
                async for event in self.api_client.chat_with_tools(messages, tool_defs):
                    if event["type"] == "text":
                        full_response += event["content"]
                    elif event["type"] == "tool_call":
                        tool_calls_received.append(event)
                    elif event["type"] == "error":
                        full_response += event["content"]
            except AttributeError:
                # Fallback: api_client doesn't have chat_with_tools
                async for chunk in self.api_client.send_message(user_content, []):
                    full_response += chunk
            except Exception as e:
                logger.error("[AgentManager] LLM call failed: %s", e, exc_info=True)
                self.state = AgentState.ERROR
                self._error = f"LLM call failed: {e}"
                return self.state, {"event": "error", "message": self._error}

            # Track estimated token usage
            self._track_usage(prompt_text, full_response)

            if tool_calls_received:
                # Build plan from native tool calls
                plan = []
                for tc in tool_calls_received:
                    tool_name = tc["name"]
                    step_desc = f"native_call: {tool_name}"
                    args = tc["arguments"]
                    plan.append({
                        "step": step_desc,
                        "tool": tool_name,
                        "args": args,
                    })

                self.plan = plan
                self.current_step = 0
                self.state = AgentState.EXECUTE
                logger.info(
                    "[AgentManager] Native tool calls: %s",
                    [p["tool"] for p in plan],
                )
                return self.state, {"event": "plan_created", "plan": self.plan}

            # No tool calls — check if text contains done signal or is a real response
            actions = self._parse_action_response(full_response)
            for action in actions:
                if action.get("done") is True:
                    self.last_summary = action.get("summary", "Task completed") or full_response.strip()
                    self.state = AgentState.COMPLETE
                    self.results.append({
                        "step": "summary",
                        "tool": "done",
                        "result": self.last_summary,
                        "index": len(self.completed_steps),
                    })
                    logger.info("[AgentManager] LLM declared task done: %s", self.last_summary)
                    return self.state, {"event": "plan_done", "summary": self.last_summary}

            # Text response with no tool calls and no done — treat as simple task complete
            if full_response.strip():
                self.last_summary = full_response.strip()
                self.state = AgentState.COMPLETE
                self.results.append({
                    "step": "summary",
                    "tool": "done",
                    "result": self.last_summary,
                    "index": len(self.completed_steps),
                })
                logger.info("[AgentManager] Text-only response — task done: %s", self.last_summary[:80])
                return self.state, {"event": "plan_done", "summary": self.last_summary}
        else:
            # JSON-in-text path (vision mode or fallback for non-tool-calling providers)
            try:
                if self.vision_mode:
                    async for chunk in self.api_client.chat(messages):
                        full_response += chunk
                else:
                    async for chunk in self.api_client.chat(messages):
                        full_response += chunk
            except AttributeError:
                if isinstance(user_content, str):
                    async for chunk in self.api_client.send_message(user_content, []):
                        full_response += chunk
                else:
                    async for chunk in self.api_client.send_message("", []):
                        full_response += chunk
            except Exception as e:
                logger.error("[AgentManager] LLM call failed: %s", e, exc_info=True)
                self.state = AgentState.ERROR
                self._error = f"LLM call failed: {e}"
                return self.state, {"event": "error", "message": self._error}

            # Track estimated token usage
            self._track_usage(prompt_text, full_response)

            # Parse JSON from text (existing logic)
            actions = self._parse_action_response(full_response)

            # Check if ANY action declares done
            for action in actions:
                if action.get("done") is True:
                    self.last_summary = action.get("summary", "Task completed")
                    self.state = AgentState.COMPLETE
                    self.results.append({
                        "step": "summary",
                        "tool": "done",
                        "result": self.last_summary,
                        "index": len(self.completed_steps),
                    })
                    logger.info("[AgentManager] LLM declared task done: %s", self.last_summary)
                    return self.state, {"event": "plan_done", "summary": self.last_summary}

            # Build multi-step plan from all actions
            plan = []
            for action in actions:
                if self.vision_mode:
                    tool_name = "vision"
                    step_desc = action.get("description", "next action")
                    args = action
                else:
                    tool_name = action.get("tool", "")
                    step_desc = action.get("description", "next action")
                    args = action.get("args", {})
                plan.append({
                    "step": step_desc,
                    "tool": tool_name,
                    "args": args,
                })

            self.plan = plan
            self.current_step = 0
            self.state = AgentState.EXECUTE
        logger.info(
            "[AgentManager] Plan has %d step(s) (iteration %d): %s",
            len(plan),
            self.iteration_count,
            [p["step"] for p in plan],
        )
        return self.state, {
            "event": "plan_created",
            "plan": self.plan,
        }

    async def _handle_execute(
        self,
    ) -> tuple[AgentState, Optional[dict[str, Any]]]:
        """Handle EXECUTE state: hand the current step to the worker.

        In opencode-style execution, the plan may contain multiple steps.
        The worker executes them one-by-one via record_step_outcome + step()
        until all steps are consumed, then transitions to VERIFY → PLAN.
        """
        if self.current_step >= len(self.plan):
            # Defensive: shouldn't happen in re-plan design
            self.state = AgentState.PLAN
            return self.state, {"event": "all_steps_completed"}

        step = self.plan[self.current_step]
        logger.debug(
            "[AgentManager] Executing: %s",
            step.get("step", "?"),
        )
        return self.state, {
            "event": "execute_step",
            "step": step,
            "index": self.current_step,
        }

    async def _handle_verify(
        self,
    ) -> tuple[AgentState, Optional[dict[str, Any]]]:
        """Handle VERIFY state: no LLM call, transition back to PLAN.

        Verification is implicit: the next PLAN call will take a fresh
        screenshot and the LLM will see the result of the last action.
        If the action didn't work, the LLM will choose a different
        action on its own. This saves 1 LLM call per step.
        """
        self.current_step = 0
        self.plan = []
        self.state = AgentState.PLAN
        logger.debug("[AgentManager] VERIFY → PLAN (re-plan with new screenshot)")
        return self.state, {"event": "verify_replan"}

    async def _handle_complete(
        self,
    ) -> tuple[AgentState, Optional[dict[str, Any]]]:
        """Handle COMPLETE state: return final results + summary."""
        return self.state, {
            "event": "completed",
            "results": self.results,
            "summary": self.last_summary,
        }

    async def _handle_error(
        self,
    ) -> tuple[AgentState, Optional[dict[str, Any]]]:
        """Handle ERROR state: return error message."""
        error_msg = getattr(self, "_error", "Unknown error")
        return self.state, {"event": "error", "message": error_msg, "error": error_msg}

    def _check_background_tasks(self) -> str:
        """Check for completed background sub-agent tasks and inject results.

        Reads from AgentTool's module-level _background_results dict.
        Once read, results are removed so they're only injected once.

        Returns:
            A formatted string of completed background tasks, or empty string.
        """
        try:
            from vda.core.tool_registry.tools.agent import _background_results as bg_results
        except ImportError:
            return ""

        if not bg_results:
            return ""

        lines = ["\n\n--- COMPLETED BACKGROUND TASKS ---"]
        task_ids = list(bg_results.keys())
        for tid in task_ids:
            result = bg_results.pop(tid, None)
            if result:
                lines.append(f'\n<task id="{tid}" state="completed">\n{result}\n</task>')

        return "\n".join(lines)

    def _is_stuck_in_readonly_loop(self) -> bool:
        """Detect if the agent is stuck re-listing/re-reading the same files.

        Returns True when the last N completed steps only contain read-only
        tools (file_glob, file_read, dir_list, terminal with list commands)
        and no write/action tools, indicating the model will never declare done.
        """
        read_only_tools = {"file_glob", "file_read", "dir_list"}
        recent = self.completed_steps[-8:]
        if len(recent) < 4:
            return False
        # All recent steps are read-only
        for s in recent:
            action = s.get("action", "")
            if action not in read_only_tools and "list" not in action.lower() and "glob" not in action.lower():
                return False
        # Has done at least one full cycle (same tool used 3+ times with different args)
        tool_counts: dict[str, int] = {}
        for s in recent:
            t = s.get("action", "")
            tool_counts[t] = tool_counts.get(t, 0) + 1
        return any(c >= 3 for c in tool_counts.values())

    def _synthesize_loop_summary(self) -> str:
        """Build a summary from completed steps when the agent can't finish."""
        read_files = []
        dirs_explored = set()
        for s in self.completed_steps:
            action = s.get("action", "")
            target = s.get("target_name", "") or ""
            if action == "file_read" and target:
                read_files.append(target)
            elif action == "dir_list" and target:
                dirs_explored.add(target)
            elif action == "file_glob" and target:
                dirs_explored.add(target)

        lines = ["[Auto-summary: agent reached iteration limit]"]
        if dirs_explored:
            lines.append("Directories explored:")
            for d in sorted(dirs_explored):
                lines.append(f"  - {d}")
        if read_files:
            lines.append(f"\nFiles read ({len(read_files)}):")
            for f in read_files[:15]:
                lines.append(f"  - {f}")
            if len(read_files) > 15:
                lines.append(f"  ... and {len(read_files) - 15} more")
        lines.append(f"\nTotal steps completed: {len(self.completed_steps)}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def record_step_outcome(
        self, step: dict[str, Any], result: str, success: bool
    ) -> None:
        """Called by the worker after a step has been executed.

        Appends the outcome to self.completed_steps so the next PLAN call
        can reference it when re-prompting the LLM. Also advances
        current_step so the next step() call sees the plan as exhausted
        and transitions to VERIFY → PLAN (re-plan loop).

        Args:
            step: The step dict that was executed (with tool, args, etc.).
            result: The execution result text.
            success: True if the tool ran without raising.
        """
        action_name = step.get("args", {}).get("action", "?") if self.vision_mode else step.get("tool", "?")
        self.completed_steps.append({
            "step": step.get("step", "?"),
            "action": action_name,
            "target_name": step.get("args", {}).get("target_name"),
            "x": step.get("args", {}).get("x"),
            "y": step.get("args", {}).get("y"),
            "result": result,
            "success": success,
        })
        # Keep only the most recent N steps in history to bound token usage
        max_history = 15 if self.vision_mode else 8
        if len(self.completed_steps) > max_history:
            self.completed_steps = self.completed_steps[-max_history:]
        # Advance step pointer so the state machine progresses
        self.current_step += 1

    def _format_step_history(self) -> str:
        """Format the completed-steps history for the next LLM prompt.

        Formats each completed step as a structured tool-result block so
        the LLM can clearly see what was called, what arguments were used,
        and what was returned. Matches opencode's tool-result style.

        Example:
            Tool Calls:
            [1] web_search({"query": "latest AI papers 2026"}) → ✓
                Result: Found papers on transformers...

            [2] web_fetch({"url": "https://arxiv.org/..."}) → ✗
                Error: HTTP 500
        """
        if not self.completed_steps:
            return "(none — this is the first step)"

        lines = []
        last_action = None
        for i, s in enumerate(self.completed_steps, start=1):
            mark = "✓" if s.get("success") else "✗"
            action = s.get("action", "?")
            result = (s.get("result") or "")[:200]

            # Build args summary from the stored step data
            step_dict = s.get("step", "")
            target = s.get("target_name", "")
            x, y = s.get("x"), s.get("y")
            args_parts = []
            if target:
                args_parts.append(f'"{target}"')
            if x is not None and y is not None:
                args_parts.append(f"({x},{y})")
            args_summary = f" {''.join(args_parts)}" if args_parts else ""

            # Detect consecutive repeat
            repeat_note = ""
            if last_action is not None and action == last_action and not target:
                repeat_note = " (REPEAT)"
            last_action = action

            lines.append(f"[{i}] {action}{args_summary} {mark}{repeat_note}")
            lines.append(f"    Result: {result}")

        return "\n".join(lines)

    def _build_user_prompt(self, history_block: str) -> str:
        """Compose the per-turn user prompt (text only, image is separate)."""
        # Count consecutive recent failures to warn the LLM
        recent_fails = 0
        for s in reversed(self.completed_steps[-5:]):
            if not s.get("success"):
                recent_fails += 1
            else:
                break

        fail_hint = ""
        if recent_fails >= 2:
            fail_hint = (
                f"\n\nURGENT WARNING: Your last {recent_fails} steps FAILED. "
                "You MUST change your strategy completely. Do NOT repeat the same action. "
                "Use keyboard shortcuts (ctrl+l, ctrl+t, Tab, Enter) instead of mouse clicks. "
                "If you are stuck, try a completely different approach.\n"
            )

        return (
            f"USER TASK: {self._user_input}\n\n"
            f"STEPS COMPLETED SO FAR:\n{history_block}\n\n"
            "RULES:\n"
            "- The SCREENSHOT is absolute ground truth. If it hasn't changed, your last action FAILED.\n"
            "- After typing a URL or search query, you MUST press Enter on the NEXT step. NEVER forget Enter.\n"
            "- Use ctrl+l to focus the URL bar (NEVER click the URL bar with mouse).\n"
            "- If Chrome autofill dropdown appears, press Enter to submit. Do NOT click dropdown items.\n"
            "- If a click fails with 'strictly disabled', switch to keyboard shortcuts immediately.\n"
            "- Do NOT repeat the same failed action. Try a different approach.\n"
            f"{fail_hint}\n"
            "Decide the NEXT single action, or reply done: true if complete."
        )

    def _get_screen_size(self) -> tuple[int, int]:
        """Return the current screen size in pixels."""
        try:
            import pyautogui
            w, h = pyautogui.size()
            return int(w), int(h)
        except Exception:
            return 1920, 1080

    def _parse_action_response(self, response_text: str) -> list[dict[str, Any]]:
        """Parse the LLM's JSON response into a list of action dicts.

        Accepts both single JSON objects and JSON arrays — opencode style.
        Returns a list so callers can build multi-step plans.

        Handles thinking models gracefully: if the entire response is
        wrapped in <think> tags, the thinking content is preserved and
        the model is kept in the thinking loop rather than forced to
        produce a JSON response it hasn't formulated yet.
        """
        if not response_text or not response_text.strip():
            return [{
                "action": "wait",
                "target_name": None,
                "target": None,
                "description": "(empty LLM response — try again)",
            }]

        import re

        # Strip <think> tags and extract thinking content
        thinking_content = ""
        think_pattern = re.compile(r"<think>(.*?)</think>", re.DOTALL)
        clean_text = think_pattern.sub("", response_text).strip()

        # Collect all thinking fragments for context
        think_fragments = think_pattern.findall(response_text)
        if think_fragments:
            thinking_content = " ".join(t.strip() for t in think_fragments if t.strip())

        # If after stripping think tags nothing useful remains, the model
        # is still in a thinking state. Return a wait action with the
        # thinking content as description so the model context grows.
        if not clean_text or not clean_text.strip():
            context = thinking_content[:300] if thinking_content else "(still thinking)"
            logger.info(
                "[AgentManager] LLM returned only thinking tags (%d chars)",
                len(response_text),
            )
            return [{
                "action": "wait",
                "target_name": None,
                "target": None,
                "description": f"(model thinking: {context})",
            }]

        # Collect JSON candidates from the text in priority order
        json_candidates: list[str] = []

        # 1. Markdown code block content
        code_match = re.search(r"```(?:json)?\s*(.+?)\s*```", clean_text, re.DOTALL | re.IGNORECASE)
        if code_match:
            json_candidates.append(code_match.group(1))

        # 2. First { to last } (handles chatty models without markdown)
        s = clean_text.find("{")
        e = clean_text.rfind("}")
        if s != -1 and e != -1 and e > s:
            json_candidates.append(clean_text[s : e + 1])

        # 3. First [ to last ] (handles json arrays without markdown)
        s = clean_text.find("[")
        e = clean_text.rfind("]")
        if s != -1 and e != -1 and e > s:
            json_candidates.append(clean_text[s : e + 1])

        for candidate in json_candidates:
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, dict):
                    return [parsed]
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                continue

        # For free/weak models: try lenient regex-based extraction before giving up
        if getattr(self, "_model_tier", None) == "free" and clean_text:
            # Try to extract tool name and args from non-JSON text
            import re as regex
            tool_match = regex.search(r'(?:tool|action)[:\s]*["\']?(\w+)["\']?', clean_text, regex.IGNORECASE)
            done_match = regex.search(r'(?:done|complete|finished)[:\s]*(true|yes)', clean_text, regex.IGNORECASE)
            if done_match:
                summary_match = regex.search(r'(?:summary|result)[:\s]*["\'](.+?)["\']', clean_text, regex.DOTALL)
                return [{
                    "done": True,
                    "summary": summary_match.group(1)[:200] if summary_match else clean_text.strip()[:200],
                }]
            if tool_match:
                return [{
                    "tool": tool_match.group(1),
                    "args": {},
                    "description": clean_text.strip()[:100],
                }]

        # Non-JSON response — include the thinking context in the
        # wait action so the next PLAN turn has richer context.
        context = thinking_content[:200] if thinking_content else response_text[:200].strip()
        logger.warning(
            "[AgentManager] Could not parse JSON from LLM response (think=%d chars): %s",
            len(thinking_content),
            response_text[:100],
        )
        return [{
            "action": "wait",
            "target_name": None,
            "target": None,
            "description": context or "(no response)",
        }]

    async def _apply_rate_limit_delay(self) -> None:
        """Enforce minimum delay between consecutive LLM calls.

        Reads the provider's ``rate_limit.min_request_interval`` from the
        PROVIDERS config and sleeps if the previous LLM call was too
        recent. This prevents burst API calls that trigger 429 on
        providers with strict RPM limits (e.g. NVIDIA NIM free tier).
        """
        if not hasattr(self, "_last_llm_call_time"):
            self._last_llm_call_time = 0.0

        # Determine the provider's rate limit config
        provider_id = ""
        if self.settings:
            if hasattr(self.settings, "get"):
                provider_id = self.settings.get("provider", "")
            elif isinstance(self.settings, dict):
                provider_id = self.settings.get("provider", "")

        provider_info = PROVIDERS.get(provider_id, {})
        rl = provider_info.get("rate_limit", {"min_request_interval": 1.0})
        min_interval = rl.get("min_request_interval", 1.0)

        elapsed = time.monotonic() - self._last_llm_call_time
        if elapsed < min_interval:
            wait = min_interval - elapsed
            logger.info(
                "[AgentManager] Rate-limit throttle: waiting %.1fs before next LLM call",
                wait,
            )
            await asyncio.sleep(wait)

        self._last_llm_call_time = time.monotonic()


    def _track_usage(self, prompt_text: str = "", response_text: str = "", prompt_tokens: int = 0, completion_tokens: int = 0) -> None:
        """Track token usage from an LLM call.

        Uses real token counts from the API when available (non-zero values),
        otherwise falls back to a 4-char-per-token estimate.

        Args:
            prompt_text: The prompt text sent (for fallback estimation).
            response_text: The response text received (for fallback estimation).
            prompt_tokens: Real prompt token count from API (0 = use estimate).
            completion_tokens: Real completion token count from API (0 = use estimate).
        """
        if prompt_tokens > 0 and completion_tokens > 0:
            self.total_prompt_tokens += prompt_tokens
            self.total_completion_tokens += completion_tokens
        else:
            prompt_tokens = len(prompt_text) // 4
            completion_tokens = len(response_text) // 4
            self.total_prompt_tokens += prompt_tokens
            self.total_completion_tokens += completion_tokens
        self.total_cost += (prompt_tokens * 0.000002) + (completion_tokens * 0.00001)

    def pause(self, reason: str) -> None:
        """Pause execution for user intervention (doom loop, permission).

        Sets state to PAUSED and stores the reason. The step() method
        will return immediately while paused.

        Args:
            reason: Human-readable description of why execution was paused.
        """
        self._paused_reason = reason
        self.state = AgentState.PAUSED
        logger.info("[AgentManager] Paused: %s", reason)

    def resume(self) -> None:
        """Resume execution after user intervention.

        Restores to PLAN state so the agent re-plans with a fresh
        screenshot of whatever the user changed while paused.
        """
        self._paused_reason = None
        self.state = AgentState.PLAN
        logger.info("[AgentManager] Resumed")

    def abort(self) -> None:
        """Abort the entire agent run. Sets state to COMPLETE."""
        self.state = AgentState.COMPLETE
        logger.info("[AgentManager] Aborted")
