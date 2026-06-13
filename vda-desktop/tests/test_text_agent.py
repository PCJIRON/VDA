import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from vda.core.agent_manager import AgentManager, AgentState
from vda.core.agent_manager.agent_worker import AgentWorker


class ScriptedAPI:
    """Mock API that yields a pre-scripted response sequence."""

    def __init__(self, responses):
        self.responses = responses
        self.call_count = 0

    async def chat(self, messages):
        resp = self.responses[self.call_count]
        self.call_count += 1
        yield resp

    async def send_message(self, prompt, msgs):
        resp = self.responses[self.call_count]
        self.call_count += 1
        yield resp


class DummyTool:
    def __init__(self):
        self.execute = AsyncMock(return_value="tool_result_ok")


@pytest.fixture
def mock_registry():
    """Create a mock tool registry with a dummy terminal tool."""
    registry = MagicMock()
    # Mock get_definitions
    registry.get_definitions.return_value = [
        {"name": "terminal", "description": "Run shell command"}
    ]
    # Mock get_tool
    dummy_tool = DummyTool()
    registry.get_tool.return_value = dummy_tool
    registry.dummy_tool = dummy_tool
    return registry


def test_text_agent_skips_screenshots(mock_registry):
    # LLM response that calls terminal tool
    llm_resp = '```json\n{"tool": "terminal", "args": {"command": "echo hello"}, "description": "run echo"}\n```'
    api = ScriptedAPI([llm_resp])
    screenshot_fn = MagicMock(return_value="fake_b64_img")

    manager = AgentManager(
        api_client=api,
        tool_registry=mock_registry,
        screenshot_fn=screenshot_fn,
        vision_mode=False,
    )
    manager._user_input = "run terminal command"
    manager.state = AgentState.PLAN

    async def run():
        return await manager.step()

    next_state, output = asyncio.run(run())

    assert next_state == AgentState.EXECUTE
    assert len(manager.plan) == 1
    assert manager.plan[0]["tool"] == "terminal"
    assert manager.plan[0]["args"] == {"command": "echo hello"}
    assert manager.plan[0]["step"] == "run echo"

    # Verify screenshot was never taken
    screenshot_fn.assert_not_called()


def test_text_agent_executes_tool_via_worker(mock_registry):
    # Setup worker and manager
    manager = AgentManager(
        api_client=MagicMock(),
        tool_registry=mock_registry,
        vision_mode=False,
    )

    # Cache ALLOW decision for terminal tool to bypass the ASK prompt
    from vda.core.agent_manager.permission_system import PermissionDecision
    manager.permission_system.cache_decision(
        "terminal", "main", {"command": "echo test"}, PermissionDecision.ALLOW
    )

    # We simulate a plan containing a tool call
    manager.plan = [{
        "step": "Run shell test",
        "tool": "terminal",
        "args": {"command": "echo test"},
    }]
    manager.current_step = 0
    manager.state = AgentState.EXECUTE

    worker = AgentWorker(manager, "run echo")

    async def run_execution():
        # Trigger execute_step manually on worker
        await worker._handle_execute_step({
            "step": manager.plan[0],
            "index": 0,
        })

    asyncio.run(run_execution())

    # Verify tool registry was queried and mock tool executed
    mock_registry.get_tool.assert_called_with("terminal")
    mock_registry.dummy_tool.execute.assert_called_with(command="echo test")

    # Verify outcome was recorded
    assert len(manager.completed_steps) == 1
    assert manager.completed_steps[0]["action"] == "terminal"
    assert manager.completed_steps[0]["result"] == "tool_result_ok"
    assert manager.completed_steps[0]["success"] is True
