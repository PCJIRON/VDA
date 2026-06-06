"""AgentManager — state machine driving the Antigravity-style agent loop.

The state machine transitions through IDLE → INIT → PLAN → EXECUTE → VERIFY
→ ITERATE → COMPLETE / ERROR, with a PAUSED state for user intervention
(doom loop detection, permission requests).

Each state is handled by a dedicated async method, dispatched via a dict
mapping states to handlers.
"""

import enum
import logging
from typing import Any, Optional

from qwen_desktop.core.agent_manager.doom_detector import DoomLoopDetector
from qwen_desktop.core.agent_manager.permission_system import PermissionSystem

logger = logging.getLogger(__name__)


class AgentState(enum.Enum):
    """Agent lifecycle states.

    States:
        IDLE: Initial state before any task is started.
        INIT: Collecting user input and setting up context.
        PLAN: Decomposing task into steps via LLM.
        EXECUTE: Executing the current step with a tool call.
        VERIFY: Checking if step outcome matches expected result.
        ITERATE: Deciding whether to retry or abort after verification failure.
        COMPLETE: Task finished successfully or aborted.
        ERROR: Unrecoverable error (e.g., max iterations exceeded).
        PAUSED: Suspended waiting for user intervention.
    """

    IDLE = "idle"
    INIT = "init"
    PLAN = "plan"
    EXECUTE = "execute"
    VERIFY = "verify"
    ITERATE = "iterate"
    COMPLETE = "complete"
    ERROR = "error"
    PAUSED = "paused"


class AgentManager:
    """State machine driving the Antigravity loop.

    The AgentManager is a pure state machine — it does NOT extend QThread.
    It accepts an API client, tool registry, and optional settings,
    and returns results via its step() method. The AgentWorker QThread
    (created in Plan 04) wraps this class and emits signals for UI updates.

    Args:
        api_client: API client for LLM calls (planning, verification).
        tool_registry: ToolRegistry instance for executing tool steps.
        settings: Optional settings object/dict for configuration values.
        max_iterations: Maximum number of loop iterations before ERROR.
    """

    def __init__(
        self,
        api_client: Any,
        tool_registry: Any,
        settings: Optional[Any] = None,
        max_iterations: int = 10,
    ) -> None:
        self.api_client = api_client
        self.tool_registry = tool_registry
        self.settings = settings
        self.max_iterations = max_iterations

        # State
        self.state = AgentState.IDLE
        self.plan: list[dict[str, Any]] = []
        self.current_step: int = 0
        self.iteration_count: int = 0
        self.results: list[dict[str, Any]] = []

        # Subsystems
        self.doom_detector = DoomLoopDetector()
        self.permission_system = PermissionSystem(settings)

        # Internal state
        self._error: Optional[str] = None
        self._paused_reason: Optional[str] = None
        self._user_input: str = ""
        self._context: str = ""

        # State dispatch table
        self._handlers = {
            AgentState.INIT: self._handle_init,
            AgentState.PLAN: self._handle_plan,
            AgentState.EXECUTE: self._handle_execute,
            AgentState.VERIFY: self._handle_verify,
            AgentState.ITERATE: self._handle_iterate,
            AgentState.COMPLETE: self._handle_complete,
            AgentState.ERROR: self._handle_error,
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
        self._error = None
        self._paused_reason = None
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

    async def _handle_init(self) -> tuple[AgentState, Optional[dict[str, Any]]]:
        """Handle INIT state: set up iteration count, transition to PLAN."""
        self.iteration_count = 0
        self.state = AgentState.PLAN
        logger.debug("[AgentManager] INIT → PLAN")
        return self.state, {"event": "init_complete", "input": self._user_input}

    async def _handle_plan(self) -> tuple[AgentState, Optional[dict[str, Any]]]:
        """Handle PLAN state: decompose task into steps via LLM."""
        self.plan = await self._create_plan(self._user_input, self._context)
        self.current_step = 0
        self.iteration_count += 1
        self.state = AgentState.EXECUTE
        logger.info(
            "[AgentManager] Created plan with %d steps (iteration %d)",
            len(self.plan),
            self.iteration_count,
        )
        return self.state, {"event": "plan_created", "plan": self.plan}

    async def _handle_execute(
        self,
    ) -> tuple[AgentState, Optional[dict[str, Any]]]:
        """Handle EXECUTE state: run current step or transition to VERIFY.

        If all steps are done, transitions to VERIFY.
        Otherwise returns the current step for execution.
        """
        if self.current_step >= len(self.plan):
            self.state = AgentState.VERIFY
            return self.state, {"event": "all_steps_completed"}

        step = self.plan[self.current_step]
        logger.debug(
            "[AgentManager] Executing step %d/%d: %s",
            self.current_step + 1,
            len(self.plan),
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
        """Handle VERIFY state: check if last result matches expectations.

        On success: advance to next step (or COMPLETE if all done).
        On failure: transition to ITERATE for retry.
        """
        last_result = self.results[-1] if self.results else {}
        verified = await self._verify_result(last_result)

        # Check for doom loop after verification
        loop_info = self.doom_detector.check_loop()
        if loop_info:
            # Emit doom loop event via logging; UI will be notified via AgentWorker signal
            logger.warning(
                "[AgentManager] Doom loop detected during verification: %s", loop_info["tool"]
            )
            self.pause(f"Doom loop detected: {loop_info['tool']}")
            # State is set to PAUSED inside pause()
            return self.state, {"event": "doom_loop", "info": loop_info}

        if verified.get("success"):
            self.current_step += 1
            if self.current_step >= len(self.plan):
                self.state = AgentState.COMPLETE
                logger.info("[AgentManager] All steps completed")
            else:
                self.state = AgentState.EXECUTE
                logger.debug(
                    "[AgentManager] Step verified, advancing to %d/%d",
                    self.current_step + 1,
                    len(self.plan),
                )
        else:
            self.state = AgentState.ITERATE
            logger.warning(
                "[AgentManager] Step %d verification failed: %s",
                self.current_step,
                verified.get("reason", "unknown"),
            )

        return self.state, {"event": "verification", "result": verified}

    async def _handle_iterate(
        self,
    ) -> tuple[AgentState, Optional[dict[str, Any]]]:
        """Handle ITERATE state: check iteration limit, retry or error.

        If max_iterations exceeded, transition to ERROR.
        Otherwise increment iteration count and retry the current step.
        """
        if self.iteration_count >= self.max_iterations:
            self.state = AgentState.ERROR
            self._error = f"Max iterations ({self.max_iterations}) exceeded"
            logger.error("[AgentManager] %s", self._error)
            return self.state, {"event": "max_iterations_exceeded"}

        self.iteration_count += 1
        self.state = AgentState.EXECUTE
        logger.debug(
            "[AgentManager] Retrying step %d (iteration %d/%d)",
            self.current_step,
            self.iteration_count,
            self.max_iterations,
        )
        return self.state, {
            "event": "retry_step",
            "step_index": self.current_step,
        }

    async def _handle_complete(
        self,
    ) -> tuple[AgentState, Optional[dict[str, Any]]]:
        """Handle COMPLETE state: return final results."""
        return self.state, {"event": "completed", "results": self.results}

    async def _handle_error(
        self,
    ) -> tuple[AgentState, Optional[dict[str, Any]]]:
        """Handle ERROR state: return error message."""
        return self.state, {"event": "error", "message": self._error}

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

        Restores to EXECUTE state and clears the pause reason.
        """
        self._paused_reason = None
        self.state = AgentState.EXECUTE
        logger.info("[AgentManager] Resumed")

    def abort(self) -> None:
        """Abort the entire agent run. Sets state to COMPLETE."""
        self.state = AgentState.COMPLETE
        logger.info("[AgentManager] Aborted")

    async def _create_plan(
        self, task: str, context: str
    ) -> list[dict[str, Any]]:
        """Decompose task into steps using LLM.

        Calls the API client with a planning prompt and parses the
        response into a structured plan. Reuses the existing
        TaskDecomposer prompt pattern.

        Args:
            task: The user's task description.
            context: Additional context from previous steps or memory.

        Returns:
            List of step dicts, each with keys: step, tool, args, expected.
        """
        prompt = (
            "You are an autonomous desktop agent. Break the following task "
            "into sequential steps.\n\n"
            f"Task: {task}\n"
            f"Context: {context}\n\n"
            "Return a JSON array of steps. Each step has:\n"
            '- "step": short action description\n'
            '- "tool": the tool to use (e.g., web_search, terminal, file_read)\n'
            '- "args": dict of arguments for the tool\n'
            '- "expected": what should happen after this step\n\n'
            "Return ONLY valid JSON, no other text."
        )

        full_response = ""
        async for chunk in self.api_client.send_message(prompt, []):
            full_response += chunk

        # Parse JSON from response
        import json
        import re

        json_match = re.search(r"\[.*?\]", full_response, re.DOTALL)
        if json_match:
            try:
                plan = json.loads(json_match.group(0))
                if isinstance(plan, list):
                    logger.info(
                        "[AgentManager] Plan created: %d steps", len(plan)
                    )
                    return plan
            except json.JSONDecodeError:
                pass

        logger.warning("[AgentManager] Failed to parse plan from LLM response")
        return [
            {
                "step": task[:100],
                "tool": "",
                "args": {},
                "expected": "Task completed",
            }
        ]

    async def _verify_result(
        self, result: dict[str, Any]
    ) -> dict[str, Any]:
        """Check if step outcome matches expected result.

        Args:
            result: The execution result from the last step.

        Returns:
            Dict with keys: success (bool), reason (str).
        """
        prompt = (
            "Verify whether the following step execution was successful.\n\n"
            f"Result: {result}\n\n"
            'Return JSON: {"success": true/false, "reason": "..."}\n'
            "Return ONLY valid JSON, no other text."
        )

        full_response = ""
        async for chunk in self.api_client.send_message(prompt, []):
            full_response += chunk

        import json
        import re

        json_match = re.search(r"\{.*?\}", full_response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        return {"success": True, "reason": "Verification skipped — parse failed"}
