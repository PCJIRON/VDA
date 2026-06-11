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
import io
import json
import logging
import re
import time
import os
from typing import Any, Callable, Optional

from vda.config.defaults import PROVIDERS
from vda.core.agent_manager.doom_detector import DoomLoopDetector
from vda.core.agent_manager.permission_system import PermissionSystem
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
    ) -> None:
        self.api_client = api_client
        self.tool_registry = tool_registry
        self.settings = settings
        self.max_iterations = max_iterations
        self.screenshot_fn = screenshot_fn
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

        # Internal state
        self._error: Optional[str] = None
        self._paused_reason: Optional[str] = None
        self._sift_verify_data: Optional[dict[str, Any]] = None
        self._user_input: str = ""
        self._context: str = ""

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
        logger.info("[AgentManager] Reset to IDLE")

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
                import cv2
                import base64
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
        """Handle PLAN state: take screenshot, ask LLM for next action.

        This is the heart of the re-plan-per-step design. Each call:
        1. Increments the iteration counter
        2. Captures a fresh screenshot (if screenshot_fn is provided)
        3. Builds a vision-mode prompt: task + history + screenshot
        4. Sends ONE LLM call
        5. Parses the response:
           - {done: true, summary: ...} → transition to COMPLETE
           - {action, target, ...} → set plan = [single action], go to EXECUTE
           - parse failure → safe fallback action (return description only)
        """
        if self.iteration_count >= self.max_iterations:
            self.state = AgentState.ERROR
            self._error = f"Max iterations ({self.max_iterations}) exceeded"
            logger.error("[AgentManager] %s", self._error)
            return self.state, {"event": "max_iterations_exceeded"}

        self.iteration_count += 1

        # Rate-limit delay between PLAN iterations to avoid 429 on
        # providers with strict RPM limits (e.g. NVIDIA NIM).
        await self._apply_rate_limit_delay()

        # 1. Capture screenshot
        screenshot_b64 = None
        if self.screenshot_fn is not None:
            try:
                screenshot_b64 = self.screenshot_fn()
            except Exception as e:
                logger.warning("[AgentManager] Screenshot capture failed: %s", e)

        # 2. Build the per-turn LLM message
        history_block = self._format_step_history()
        try:
            sw, sh = self._get_screen_size()
        except Exception:
            sw, sh = 1920, 1080

        skills_content = ""
        if hasattr(self, "settings") and self.settings:
            skills_path = self.settings.get("skills_md_path")
            if skills_path and os.path.exists(skills_path):
                try:
                    with open(skills_path, "r", encoding="utf-8") as f:
                        skills_content = f.read()
                except Exception as e:
                    logger.warning(f"Failed to read skills file: {e}")

        system_prompt = build_system_prompt(
            screen_width=sw,
            screen_height=sh,
            components=self.components,
            vision_mode=True,
            skills_content=skills_content,
        )

        user_text = self._build_user_prompt(history_block)

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

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        # 3. ONE LLM call for decide + verify (the next screenshot IS the verify)
        # Use chat(messages) so the full messages list (system + user with
        # image) is preserved correctly. send_message(message, history)
        # would treat our full list as the user text and nest the system
        # prompt inside the user content (a bug we hit on minimax-m3-free).
        full_response = ""
        try:
            async for chunk in self.api_client.chat(messages):
                full_response += chunk
        except AttributeError:
            # Fallback for clients that only have send_message: pass the
            # user content only and let the client inject the system prompt.
            async for chunk in self.api_client.send_message(user_content, []):
                full_response += chunk
        except Exception as e:
            logger.error("[AgentManager] LLM call failed: %s", e, exc_info=True)
            self.state = AgentState.ERROR
            self._error = f"LLM call failed: {e}"
            return self.state, {"event": "error", "message": self._error}

        # 4. Parse the response
        action = self._parse_action_response(full_response)

        # 5a. Done? → COMPLETE
        if action.get("done") is True:
            self.last_summary = action.get("summary", "Task completed")
            self.state = AgentState.COMPLETE
            self.results.append({
                "step": "summary",
                "tool": "done",
                "result": self.last_summary,
                "index": len(self.completed_steps),
            })
            logger.info(
                "[AgentManager] LLM declared task done: %s", self.last_summary
            )
            return self.state, {
                "event": "plan_done",
                "summary": self.last_summary,
            }

        # 5b. Next action → wrap in a single-step plan
        # tool="vision" routes the step to the EnhancedExecutor (via the
        # worker) instead of the generic tool registry. This is what
        # makes click/type/scroll actually do something on the desktop.
        self.plan = [{
            "step": action.get("description", "next action"),
            "tool": "vision",
            "args": action,
        }]
        self.current_step = 0
        self.state = AgentState.EXECUTE
        logger.info(
            "[AgentManager] Plan step %d: %s",
            self.iteration_count,
            action.get("action", "?"),
        )
        return self.state, {
            "event": "plan_created",
            "plan": self.plan,
        }

    async def _handle_execute(
        self,
    ) -> tuple[AgentState, Optional[dict[str, Any]]]:
        """Handle EXECUTE state: hand the current step to the worker.

        In the re-plan design, the plan is always length 1. The worker
        executes the step, appends the result to self.results AND to
        self.completed_steps (for history), then transitions to VERIFY.
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
        self.completed_steps.append({
            "step": step.get("step", "?"),
            "action": step.get("args", {}).get("action", "?"),
            "target_name": step.get("args", {}).get("target_name"),
            "x": step.get("args", {}).get("x"),
            "y": step.get("args", {}).get("y"),
            "result": result,
            "success": success,
        })
        # Keep only the most recent N steps in history to bound token usage
        max_history = 15
        if len(self.completed_steps) > max_history:
            self.completed_steps = self.completed_steps[-max_history:]
        # Advance step pointer so the state machine progresses
        self.current_step += 1

    def _format_step_history(self) -> str:
        """Format the completed-steps history for the next LLM prompt.

        Returns a compact, single-line-per-step summary the LLM can scan
        quickly. Example:
            1. ✓ clicked Chrome icon at (32, 32) — Chrome opened
            2. ✗ typed "google.com" — focused on wrong field
            3. ✓ pressed Tab — moved focus to URL bar
        """
        if not self.completed_steps:
            return "(none — this is the first step)"

        lines = []
        for i, s in enumerate(self.completed_steps, start=1):
            mark = "✓" if s.get("success") else "✗"
            action = s.get("action", "?")
            target = s.get("target_name") or ""
            x = s.get("x")
            y = s.get("y")
            
            coord_str = f" at ({x},{y})" if x is not None and y is not None else ""
            result = (s.get("result") or "")[:80]
            line = f"{i}. {mark} {action}"
            if target:
                line += f" {target}"
            line += f"{coord_str} — {result}"
            lines.append(line)
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

    def _parse_action_response(self, response_text: str) -> dict[str, Any]:
        """Parse the LLM's JSON response into an action dict."""
        if not response_text or not response_text.strip():
            return {
                "action": "wait",
                "target_name": None,
                "target": None,
                "description": "(empty LLM response — try again)",
            }

        # Strip all <think>...</think> tags FIRST so they don't corrupt JSON parsing
        import re
        clean_text = re.sub(r"<think>.*?</think>", "", response_text, flags=re.DOTALL).strip()
        if not clean_text:
            clean_text = response_text # Fallback if everything was stripped

        # 1. Try to find a markdown json block (non-greedy)
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean_text, re.DOTALL | re.IGNORECASE)
        if json_match:
            try:
                parsed = json.loads(json_match.group(1))
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass

        # 2. Try to find the first { and last } (handles chatty models without markdown)
        start_idx = clean_text.find('{')
        end_idx = clean_text.rfind('}')
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            try:
                parsed = json.loads(clean_text[start_idx:end_idx+1])
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass

        # Non-JSON response: treat as a failed parse and wait.
        # Previously this used a prose heuristic that would falsely mark
        # tasks as done when the LLM responded with conversational text
        # instead of JSON. This caused premature task completion.

        logger.warning(
            "[AgentManager] Could not parse JSON from LLM response: %s",
            response_text[:200],
        )
        # Safe fallback: wait, surface the raw text as description so the
        # user can see what the model tried to say.
        return {
            "action": "wait",
            "target_name": None,
            "target": None,
            "description": response_text[:200].strip() or "(no response)",
        }

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
