"""AgentWorker — QThread wrapper for AgentManager state machine.

Drives the Antigravity-style agent loop in a background thread, emitting
pyqtSignal events for the UI layer (ThinkingPanel, FloatingAssistant).

Following the existing APIServerWorker pattern from ui/assistant/worker.py:
- Uses asyncio.run() inside QThread.run()
- All UI updates via pyqtSignal (thread-safe)
"""

import asyncio
import json
import logging

from PyQt6.QtCore import QThread, pyqtSignal

from vda.core.agent_manager.agent_manager import AgentManager, AgentState
from vda.core.agent_manager.permission_system import PermissionDecision

logger = logging.getLogger(__name__)


class AgentWorker(QThread):
    """QThread wrapper that drives AgentManager and emits UI signals.

    Owns the async agent loop, executing each step via ToolRegistry and
    emitting signals for state transitions, step progress, doom loop
    detection, permission requests, and compaction needs.

    Signals:
        step_started: (step_label, tool_description)
        step_completed: (step_label, status, result_preview)
        step_failed: (step_label, error_message)
        plan_created: (list of step dicts)
        status_changed: (state name string)
        finished: (final result object)
        doom_loop_detected: (tool_name, args_summary)
        permission_required: (tool_name, args, agent_type)
        compaction_needed: (current_tokens, max_tokens)
        error_occurred: (error message)
    """

    # Step-level updates
    step_started = pyqtSignal(str, str)        # (step_label, tool_description)
    step_completed = pyqtSignal(str, str, str)  # (step_label, status, result_preview)
    step_failed = pyqtSignal(str, str)          # (step_label, error_message)

    # Plan-level
    plan_created = pyqtSignal(list)              # full plan steps
    status_changed = pyqtSignal(str)             # current state name
    finished = pyqtSignal(object)                # final result

    # Doom loop (per D-04)
    doom_loop_detected = pyqtSignal(str, str)    # (tool_name, args_summary)

    # Permission (for ASK decisions)
    permission_required = pyqtSignal(str, str, str)  # (tool_name, args, agent_type)
    tool_executed = pyqtSignal(str, dict, str, bool)  # (tool_name, args, result, success)

    # Compaction
    compaction_needed = pyqtSignal(int, int)     # (current_tokens, max_tokens)

    # Errors
    error_occurred = pyqtSignal(str)

    def __init__(
        self,
        agent_manager: AgentManager,
        user_input: str,
        context: str = "",
    ) -> None:
        """Initialize AgentWorker.

        Args:
            agent_manager: AgentManager instance to drive.
            user_input: The user's task/query text.
            context: Optional context string for initial setup.
        """
        super().__init__()
        self._agent_manager = agent_manager
        self._user_input = user_input
        self._context = context
        self._paused = False

    def run(self) -> None:
        """QThread entry point — runs the async agent loop.

        Follows the existing APIServerWorker pattern: wraps the async
        loop in asyncio.run() and catches fatal exceptions.
        """
        try:
            asyncio.run(self._run_loop())
        except Exception as e:
            logger.error(f"[AgentWorker] Fatal error: {e}", exc_info=True)
            self.error_occurred.emit(str(e))

    async def _run_loop(self) -> None:
        """Main agent loop — drives AgentManager step() until completion.

        Flow per state machine (re-plan-per-step design):
            1. Set state to INIT and call step()
            2. AgentManager transitions INIT → PLAN (1 LLM call + screenshot)
            3. PLAN returns either done → COMPLETE, or 1-action plan → EXECUTE
            4. EXECUTE: worker runs the single step via ToolRegistry
            5. VERIFY: no LLM call — just transition back to PLAN (re-plan)
            6. Repeat until COMPLETE or ERROR
        """
        # Initialize agent manager with user input
        self._agent_manager._user_input = self._user_input
        self._agent_manager._context = self._context
        self._agent_manager.state = AgentState.INIT

        logger.info(
            "[AgentWorker] Starting agent loop for: %s",
            self._user_input[:80],
        )

        SAFETY_LIMIT = 500
        iteration_count = 0

        while iteration_count < SAFETY_LIMIT:
            iteration_count += 1

            # Call step() — AgentManager dispatches based on current state
            state, output = await self._agent_manager.step()
            event = output.get("event") if output else ""

            # --- Terminal states ---
            if state == AgentState.COMPLETE:
                final_output = output if output else {}
                self.finished.emit(final_output)
                self.status_changed.emit("complete")
                logger.info(
                    "[AgentWorker] Agent loop completed in %d steps",
                    len(self._agent_manager.completed_steps),
                )
                break

            if state == AgentState.ERROR:
                if output:
                    message = output.get("message") or output.get("error") or "Unknown error"
                else:
                    message = "Unknown error"
                self.error_occurred.emit(message)
                self.status_changed.emit("error")
                logger.error("[AgentWorker] Agent loop error: %s", message)
                break

            # --- Paused state (doom loop / permission wait) ---
            if state == AgentState.PAUSED or self._paused:
                self.status_changed.emit("paused")
                while self._paused and self._agent_manager.state == AgentState.PAUSED:
                    await asyncio.sleep(0.1)
                # Check if we were aborted while paused
                if self._agent_manager.state in (AgentState.COMPLETE, AgentState.ERROR):
                    break
                continue

            # --- Event-specific handling ---

            if event == "init_complete":
                self.status_changed.emit("init")

            elif event == "plan_created":
                plan = output.get("plan", [])
                self.status_changed.emit("plan")
                self.plan_created.emit(plan)
                logger.info(
                    "[AgentWorker] Plan step %d created: %d action(s)",
                    self._agent_manager.iteration_count,
                    len(plan),
                )

            elif event == "plan_done":
                # LLM declared task done in PLAN — transition handled by
                # AgentManager (state is already COMPLETE), the terminal
                # branch above will fire on the next loop iteration.
                pass

            elif event == "execute_step":
                await self._handle_execute_step(output)

            elif event == "all_steps_completed":
                # Should not fire in re-plan design (plan is always 1),
                # but handle defensively.
                self.status_changed.emit("verify")

            elif event == "verify_replan":
                # Re-plan with a fresh screenshot — AgentManager already
                # transitioned state back to PLAN.
                self.status_changed.emit("replan")
                logger.debug("[AgentWorker] Re-planning with fresh screenshot")

            elif event == "verification":
                # Legacy event from old design — kept for back-compat, ignored.
                pass

            elif event == "retry_step":
                self.status_changed.emit("iterate")

            elif event == "max_iterations_exceeded":
                self.status_changed.emit("error")
                self.error_occurred.emit("Max iterations exceeded")
                break

        else:
            # Safety limit hit (while-else: runs when loop exits naturally, not break)
            logger.error("[AgentWorker] Safety iteration limit reached")
            self.error_occurred.emit("Agent loop safety limit reached")
            self._agent_manager.state = AgentState.ERROR

    async def _handle_execute_step(
        self, output: dict
    ) -> None:
        """Execute a single step from the plan.

        Args:
            output: Step output dict from AgentManager with keys:
                step, tool, args, index.
        """
        step = output.get("step", {})
        step_label = step.get("step", "Execute step")
        tool_name = step.get("tool", "")
        args = step.get("args", {})
        tool_description = (
            f"Using {tool_name}" if tool_name else "Processing..."
        )

        self.step_started.emit(step_label, tool_description)

        # Execute the tool via ToolRegistry (or vision_executor for vision
        # actions like click/type/scroll)
        result_str = ""
        error_str = None
        success = False
        try:
            if tool_name != "vision" and tool_name:
                from vda.core.agent_manager.permission_system import PermissionDecision
                agent_type = getattr(self._agent_manager, "agent_type", "main")
                decision = self._agent_manager.permission_system.check_permission(
                    tool_name, agent_type, args
                )
                if decision == PermissionDecision.DENY:
                    result_str = f"Permission denied for tool '{tool_name}'"
                    logger.warning("[AgentWorker] Permission denied for tool '%s'", tool_name)
                    self._agent_manager.results.append({
                        "step": step,
                        "tool": tool_name,
                        "error": result_str,
                        "index": output.get("index", 0),
                    })
                    self._agent_manager.record_step_outcome(step, result_str, False)
                    self.step_failed.emit(step_label, result_str)
                    self.tool_executed.emit(tool_name, args, result_str, False)
                    return
                elif decision == PermissionDecision.ASK:
                    self.permission_required.emit(tool_name, json.dumps(args), agent_type)
                    self._agent_manager.pause(f"Permission required for: {tool_name}")
                    self._paused = True
                    
                    # Wait for user input
                    while self._paused and self._agent_manager.state == AgentState.PAUSED:
                        await asyncio.sleep(0.1)
                        
                    if self._agent_manager.state in (AgentState.COMPLETE, AgentState.ERROR):
                        return
                        
                    # Recheck decision
                    new_decision = self._agent_manager.permission_system.check_permission(
                        tool_name, agent_type, args
                    )
                    if new_decision != PermissionDecision.ALLOW:
                        result_str = f"Permission denied by user for tool '{tool_name}'"
                        self._agent_manager.results.append({
                            "step": step,
                            "tool": tool_name,
                            "error": result_str,
                            "index": output.get("index", 0),
                        })
                        self._agent_manager.record_step_outcome(step, result_str, False)
                        self.step_failed.emit(step_label, result_str)
                        self.tool_executed.emit(tool_name, args, result_str, False)
                        return

            if tool_name == "vision":
                # Direct vision action execution (click, type, scroll, etc.)
                vision_executor = self._agent_manager.vision_executor
                if vision_executor is None:
                    result_str = "No vision executor configured"
                    logger.warning("[AgentWorker] No vision_executor on AgentManager")
                else:
                    # EnhancedExecutor.execute(parsed) expects {action, x, y, text}
                    # Our action dict has {action, target: [x, y], text}
                    parsed = dict(args)
                    if "target" in parsed and isinstance(parsed["target"], (list, tuple)):
                        parsed["x"], parsed["y"] = parsed["target"][0], parsed["target"][1]
                    ok = vision_executor.execute(parsed)
                    if isinstance(ok, dict) and ok.get("action") == "sift_verify":
                        self._agent_manager.state = AgentState.SIFT_VERIFY
                        self._agent_manager._sift_verify_data = ok
                        return
                    elif isinstance(ok, str):
                        result_str = ok
                        success = False
                        logger.error(f"[AgentWorker] Vision executor returned error: {ok}")
                    else:
                        result_str = f"Vision action '{parsed.get('action', '?')}' -> {ok}"
                        success = bool(ok)
            elif tool_name:
                tool = self._agent_manager.tool_registry.get_tool(tool_name)
                if tool:
                    # Inject api_client if the tool needs it (e.g. AgentTool)
                    if hasattr(tool, "api_client"):
                        tool.api_client = getattr(self._agent_manager, "api_client", None)
                        
                    raw_result = await tool.execute(**args)
                    result_str = (
                        json.dumps(raw_result)[:500]
                        if isinstance(raw_result, dict)
                        else str(raw_result)[:500]
                    )
                    success = True
                    self.tool_executed.emit(tool_name, args, result_str, True)
                else:
                    result_str = f"Tool '{tool_name}' not found"
                    self.tool_executed.emit(tool_name, args, result_str, False)
                    logger.warning(
                        "[AgentWorker] Tool '%s' not in registry", tool_name
                    )
            else:
                result_str = "No tool specified for this step"

            # Push result to agent manager for verification
            self._agent_manager.results.append({
                "step": step,
                "tool": tool_name,
                "result": result_str,
                "index": output.get("index", 0),
            })

            # Record this step in completed_steps so the next PLAN can
            # include it in the LLM's history context. record_step_outcome
            # also advances current_step.
            self._agent_manager.record_step_outcome(step, result_str, success)

            # Doom loop detection
            self._agent_manager.doom_detector.record_call(
                tool_name, args, result_str
            )
            loop_info = self._agent_manager.doom_detector.check_loop()
            if loop_info:
                args_summary = json.dumps(args)[:100] if args else "{}"
                self.doom_loop_detected.emit(tool_name, args_summary)
                self._agent_manager.pause(f"Doom loop detected: {tool_name}")
                self._paused = True
                logger.warning("[AgentWorker] Doom loop detected: %s", tool_name)
                # Wait — will be resumed by resume_from_doom_loop()
                return

            # Success — record_step_outcome already advanced current_step
            self.step_completed.emit(step_label, "success", result_str)

        except Exception as e:
            error_str = str(e)
            logger.error(
                "[AgentWorker] Tool execution failed: %s", error_str,
                exc_info=True,
            )
            self._agent_manager.results.append({
                "step": step,
                "tool": tool_name,
                "error": error_str,
                "index": output.get("index", 0),
            })
            # Record the failed step in history (also advances current_step)
            self._agent_manager.record_step_outcome(step, error_str, False)
            self.step_failed.emit(step_label, error_str)
            self.tool_executed.emit(tool_name, args, error_str, False)

        # Check compaction after each step
        await self._check_compaction()

    async def _check_compaction(self) -> None:
        """Check if conversation needs compaction and emit signal.

        Checks the SessionCompactor (if available on the agent manager)
        to see if token usage exceeds the compaction threshold.
        """
        try:
            compactor = getattr(self._agent_manager, "compactor", None)
            if compactor is None:
                return
            session_service = getattr(self._agent_manager, "session_service", None)
            if session_service is None:
                return
            session_id = getattr(self._agent_manager, "_session_id", None)
            if not session_id:
                return

            messages = session_service.get_conversation(session_id)
            if await compactor.needs_compaction(messages):
                estimated = compactor.estimate_tokens(messages)
                self.compaction_needed.emit(estimated, compactor.max_tokens)
        except Exception as e:
            logger.debug("[AgentWorker] Compaction check skipped: %s", e)

    def resume_from_doom_loop(self) -> None:
        """Resume agent execution after doom loop pause.

        Called from the UI thread when user clicks Resume.
        Restores the agent to EXECUTE state and clears the pause flag.
        """
        logger.info("[AgentWorker] Resume from doom loop requested")
        self._agent_manager.resume()
        self._paused = False

    def abort_agent(self) -> None:
        """Abort the entire agent execution.

        Called from the UI thread when user clicks Abort.
        Sets the agent state to COMPLETE and clears the pause flag.
        """
        logger.info("[AgentWorker] Abort requested")
        self._agent_manager.abort()
        self._paused = False

    def handle_permission_response(
        self, tool_name: str, allowed: bool
    ) -> None:
        """Handle user permission allow/deny response.

        Caches the decision in the permission system so the same tool
        call is not re-prompted in the same session.

        Args:
            tool_name: Name of the tool.
            allowed: True to allow, False to deny.
        """
        decision = (
            PermissionDecision.ALLOW if allowed else PermissionDecision.DENY
        )
        
        # Retrieve active step arguments to cache correctly
        args = {}
        plan = self._agent_manager.plan
        curr = self._agent_manager.current_step
        if curr < len(plan):
            args = plan[curr].get("args", {})

        agent_type = getattr(self._agent_manager, "agent_type", "main")
        self._agent_manager.permission_system.cache_decision(
            tool_name, agent_type, args, decision
        )
        logger.info(
            "[AgentWorker] Permission response for '%s' (args: %s): %s",
            tool_name, args, decision.value,
        )
        
        # Resume the agent execution
        self._agent_manager.resume()
        self._paused = False
