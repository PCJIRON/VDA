"""Tests for the re-plan-per-step agent design.

Covers the new flow:
  - _handle_plan: take screenshot, LLM call, parse action
  - _handle_verify: no-op transition back to PLAN
  - screenshot_fn injection
  - done: true signal handling
  - completed_steps history for the LLM
"""

import asyncio
import json
from unittest.mock import MagicMock

import pytest

from vda.core.agent_manager import AgentManager, AgentState


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

class ScriptedAPI:
    """Mock API that returns a sequence of responses.

    Each call to send_message pops the next response from the queue and
    yields it as a single chunk (the real client streams, but for tests
    one-chunk is fine).
    """

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    async def send_message(self, messages, history, **kwargs):
        self.calls.append(messages)
        if not self._responses:
            # Default fallback: declare done
            yield json.dumps({"done": True, "summary": "no more responses"})
            return
        response = self._responses.pop(0)
        if isinstance(response, str):
            yield response
        else:
            yield json.dumps(response)

    async def chat(self, messages, **kwargs):
        # Same as send_message but for the .chat(messages) interface used
        # by AgentManager (preserves system + user as separate roles).
        async for chunk in self.send_message(messages, []):
            yield chunk


@pytest.fixture
def mock_registry():
    return MagicMock()


# ---------------------------------------------------------------------------
# Screenshot injection
# ---------------------------------------------------------------------------

def test_screenshot_fn_injection_and_usage(mock_registry):
    """screenshot_fn is called during _handle_plan and passed in the LLM call."""
    captured_screenshots = []

    def fake_screenshot():
        captured_screenshots.append(1)
        return "BASE64DATA"

    api = ScriptedAPI([{"action": "click", "target": [10, 20], "description": "test"}])
    manager = AgentManager(
        api_client=api,
        tool_registry=mock_registry,
        screenshot_fn=fake_screenshot,
    )
    manager._user_input = "test task"
    manager.state = AgentState.PLAN

    async def run():
        return await manager._handle_plan()

    state, output = asyncio.run(run())
    assert len(captured_screenshots) == 1
    assert state == AgentState.EXECUTE
    # The LLM call should have included an image_url block in the user content
    assert len(api.calls) == 1
    messages = api.calls[0]  # chat(messages) -> send_message(messages, [])
    # Regression: system and user must be SEPARATE messages, not nested.
    # Previously we passed the full messages list as the first arg to
    # send_message, which caused the system prompt to be nested inside
    # the user content. That made minimax-m3-free respond as if the
    # system prompt was a user message ("No task was provided").
    assert len(messages) == 2, f"Expected [system, user] but got {len(messages)} messages"
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    user_msg = messages[1]  # [system, user]
    user_content = user_msg["content"]
    assert any(
        isinstance(block, dict) and block.get("type") == "image_url"
        for block in user_content
    )


def test_user_task_reaches_llm_prompt(mock_registry):
    """Regression: the user_input must end up in the LLM's user prompt.
    Previously _create_worker dropped the user text when vision mode
    passed a content-payload list instead of a plain string, so the
    LLM saw 'USER TASK: ' (empty) and replied 'No user task was
    provided'. Verify the task string is present in the prompt.
    """
    api = ScriptedAPI([{"done": True, "summary": "ok"}])
    manager = AgentManager(api_client=api, tool_registry=mock_registry)
    manager._user_input = "open chrome and click on new tab"
    manager.state = AgentState.PLAN

    async def run():
        return await manager._handle_plan()

    asyncio.run(run())
    # The LLM was called with a messages list
    assert len(api.calls) == 1
    messages = api.calls[0]
    # Find the user message
    user_msgs = [m for m in messages if m.get("role") == "user"]
    assert user_msgs, "Expected a user-role message"
    user_content = user_msgs[-1]["content"]
    # The user content should mention the actual task
    if isinstance(user_content, str):
        assert "open chrome" in user_content
    else:
        # Multi-block content (text + image). The first text block
        # should contain the task description.
        text_blocks = [b for b in user_content if b.get("type") == "text"]
        assert text_blocks
        assert "open chrome" in text_blocks[0]["text"]


def test_screenshot_failure_does_not_crash(mock_registry):
    """If screenshot_fn raises, _handle_plan continues with text-only prompt."""
    def broken_screenshot():
        raise RuntimeError("screen capture unavailable")

    api = ScriptedAPI([{"action": "click", "target": [10, 20], "description": "test"}])
    manager = AgentManager(
        api_client=api,
        tool_registry=mock_registry,
        screenshot_fn=broken_screenshot,
    )
    manager._user_input = "test"
    manager.state = AgentState.PLAN

    async def run():
        return await manager._handle_plan()

    state, output = asyncio.run(run())
    assert state == AgentState.EXECUTE
    # Prompt should be plain string (no image), since screenshot failed
    assert len(api.calls) == 1
    messages = api.calls[0]
    user_msg = messages[1]
    user_content = user_msg["content"]
    # content is a plain string, not a list of blocks
    assert isinstance(user_content, str)


# ---------------------------------------------------------------------------
# done: true handling
# ---------------------------------------------------------------------------

def test_done_true_transitions_to_complete(mock_registry):
    """When LLM returns {done: true, summary: ...}, state goes to COMPLETE."""
    api = ScriptedAPI([{"done": True, "summary": "Task is done"}])
    manager = AgentManager(api_client=api, tool_registry=mock_registry)
    manager._user_input = "test"
    manager.state = AgentState.PLAN

    async def run():
        return await manager._handle_plan()

    state, output = asyncio.run(run())
    assert state == AgentState.COMPLETE
    assert output["event"] == "plan_done"
    assert output["summary"] == "Task is done"
    assert manager.last_summary == "Task is done"


def test_action_response_creates_single_step_plan(mock_registry):
    """When LLM returns an action, plan has length 1 and state goes to EXECUTE."""
    api = ScriptedAPI([{
        "action": "click",
        "target_name": "search",
        "target": [450, 320],
        "description": "Click search box",
    }])
    manager = AgentManager(api_client=api, tool_registry=mock_registry)
    manager._user_input = "search for cats"
    manager.state = AgentState.PLAN

    async def run():
        return await manager._handle_plan()

    state, output = asyncio.run(run())
    assert state == AgentState.EXECUTE
    assert output["event"] == "plan_created"
    assert len(manager.plan) == 1
    assert manager.plan[0]["args"]["action"] == "click"
    assert manager.plan[0]["args"]["target_name"] == "search"


# ---------------------------------------------------------------------------
# Re-plan flow
# ---------------------------------------------------------------------------

def test_verify_transitions_back_to_plan(mock_registry):
    """_handle_verify should set state=PLAN (re-plan with new screenshot)."""
    manager = AgentManager(api_client=MagicMock(), tool_registry=mock_registry)
    manager.state = AgentState.VERIFY
    manager.plan = [{"step": "x", "tool": "uied", "args": {}}]
    manager.current_step = 0

    async def run():
        return await manager._handle_verify()

    state, output = asyncio.run(run())
    assert state == AgentState.PLAN
    assert output["event"] == "verify_replan"
    # Plan cleared so the next PLAN starts fresh
    assert manager.plan == []
    assert manager.current_step == 0


def test_re_plan_increments_iteration_count(mock_registry):
    """Each call to _handle_plan bumps the iteration_count."""
    api = ScriptedAPI([
        {"action": "click", "target": [10, 10], "description": "step 1"},
        {"action": "type", "text": "hello", "description": "step 2"},
        {"done": True, "summary": "all done"},
    ])
    manager = AgentManager(api_client=api, tool_registry=mock_registry)
    manager._user_input = "test"
    manager.state = AgentState.PLAN

    async def run():
        states = []
        for _ in range(3):
            manager.state = AgentState.PLAN
            state, _ = await manager._handle_plan()
            states.append(state)
        return states

    states = asyncio.run(run())
    assert states == [
        AgentState.EXECUTE,  # step 1
        AgentState.EXECUTE,  # step 2
        AgentState.COMPLETE, # done
    ]
    assert manager.iteration_count == 3


# ---------------------------------------------------------------------------
# Completed steps history
# ---------------------------------------------------------------------------

def test_record_step_outcome_appends_to_history(mock_registry):
    manager = AgentManager(api_client=MagicMock(), tool_registry=mock_registry)
    step = {
        "step": "click",
        "args": {"action": "click", "target_name": "search"},
    }
    manager.record_step_outcome(step, "clicked successfully", True)
    assert len(manager.completed_steps) == 1
    entry = manager.completed_steps[0]
    assert entry["action"] == "click"
    assert entry["target_name"] == "search"
    assert entry["success"] is True


def test_record_step_outcome_advances_current_step(mock_registry):
    """Regression: record_step_outcome must bump current_step so the
    state machine progresses to VERIFY after a single execute call.

    Without this, EXECUTE→VERIFY transition requires manual increment
    by the worker, which is easy to forget and produces an infinite
    EXECUTE loop in the smoke harness.
    """
    manager = AgentManager(api_client=MagicMock(), tool_registry=mock_registry)
    step = {
        "step": 1,
        "args": {"action": "click", "target_name": "button"},
    }
    assert manager.current_step == 0
    manager.record_step_outcome(step, "ok", True)
    assert manager.current_step == 1
    manager.record_step_outcome(step, "ok", True)
    assert manager.current_step == 2


def test_completed_steps_capped_at_max_history(mock_registry):
    manager = AgentManager(api_client=MagicMock(), tool_registry=mock_registry)
    step = {"step": "x", "args": {"action": "click"}}
    for i in range(20):
        manager.record_step_outcome(step, f"step {i}", True)
    # The implementation caps at 8 most recent steps
    assert len(manager.completed_steps) <= 8
    # And the most recent step is preserved
    assert "step 19" in manager.completed_steps[-1]["result"]


def test_step_history_format_includes_marks_and_results(mock_registry):
    manager = AgentManager(api_client=MagicMock(), tool_registry=mock_registry)
    manager.record_step_outcome(
        {"step": "Click X", "args": {"action": "click", "target_name": "X"}},
        "X was clicked", True,
    )
    manager.record_step_outcome(
        {"step": "Type Y", "args": {"action": "type", "target_name": None}},
        "focused on wrong field", False,
    )
    history = manager._format_step_history()
    assert "✓" in history
    assert "✗" in history
    assert "click" in history
    assert "X was clicked" in history
    assert "focused on wrong field" in history


def test_step_history_empty_returns_sentinel(mock_registry):
    manager = AgentManager(api_client=MagicMock(), tool_registry=mock_registry)
    assert "first step" in manager._format_step_history()


# ---------------------------------------------------------------------------
# Max iterations
# ---------------------------------------------------------------------------

def test_max_iterations_triggers_error_state(mock_registry):
    api = ScriptedAPI([{"action": "click", "target": [1, 1], "description": "x"}] * 100)
    manager = AgentManager(
        api_client=api,
        tool_registry=mock_registry,
        max_iterations=2,
    )
    manager._user_input = "test"
    manager.state = AgentState.PLAN
    # iteration_count must be >= max_iterations for the check to fire
    manager.iteration_count = 2

    async def run():
        state, out = await manager._handle_plan()
        return state, out

    state, output = asyncio.run(run())
    assert state == AgentState.ERROR
    assert output["event"] == "max_iterations_exceeded"
    assert manager._error is not None
    assert "Max iterations" in manager._error


# ---------------------------------------------------------------------------
# JSON parse failure
# ---------------------------------------------------------------------------

def test_malformed_json_falls_back_to_wait(mock_registry):
    """If LLM returns non-JSON garbage like 'null', _handle_plan returns
    a safe 'wait' action so the agent doesn't loop forever.
    """
    api = ScriptedAPI(["null"])
    manager = AgentManager(api_client=api, tool_registry=mock_registry)
    manager._user_input = "test"
    manager.state = AgentState.PLAN

    async def run():
        return await manager._handle_plan()

    state, output = asyncio.run(run())
    assert state == AgentState.EXECUTE
    assert len(manager.plan) == 1
    # Fallback action should be a wait with the raw text in description
    assert manager.plan[0]["args"]["action"] == "wait"


def test_conversational_response_treated_as_done(mock_registry):
    """If LLM returns free-form text (no JSON), treat it as done: true
    with the text as summary. Prevents infinite re-plan loops when the
    model is just being conversational instead of action-oriented.
    """
    api = ScriptedAPI(["Hey! What can I help you with?"])
    manager = AgentManager(api_client=api, tool_registry=mock_registry)
    manager._user_input = "hi"
    manager.state = AgentState.PLAN

    async def run():
        return await manager._handle_plan()

    state, output = asyncio.run(run())
    assert state == AgentState.COMPLETE
    assert "Hey" in manager.last_summary


def test_partial_json_extraction_works(mock_registry):
    """If the LLM wraps JSON in prose, regex extracts the JSON object."""
    api = ScriptedAPI([
        'Here is my decision: {"action": "type", "text": "hello"} -- end',
    ])
    manager = AgentManager(api_client=api, tool_registry=mock_registry)
    manager._user_input = "test"
    manager.state = AgentState.PLAN

    async def run():
        return await manager._handle_plan()

    state, output = asyncio.run(run())
    assert state == AgentState.EXECUTE
    assert manager.plan[0]["args"]["action"] == "type"
    assert manager.plan[0]["args"]["text"] == "hello"
