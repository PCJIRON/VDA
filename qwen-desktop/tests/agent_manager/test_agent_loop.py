import asyncio
import pytest
from qwen_desktop.core.agent_manager.agent_manager import AgentManager, AgentState


class DummyAPI:
    async def send_message(self, prompt, msgs):
        # Return a minimal JSON plan with two steps
        dummy_plan = "[{'step':'Step 1','tool':'dummy','args':{}},{'step':'Step 2','tool':'dummy','args':{}}]"
        yield dummy_plan


def test_doom_loop_detection_and_pause(monkeypatch):
    """Test that identical tool calls trigger doom loop detection and pause.

    The AgentManager should pause execution when DoomLoopDetector reports a loop.
    """
    dummy_api = DummyAPI()
    dummy_registry = type("DummyRegistry", (), {"get_tool": lambda self, name: None})()

    manager = AgentManager(api_client=dummy_api, tool_registry=dummy_registry, max_iterations=5)
    # Define plan directly
    manager.plan = [
        {"step": "Step 1", "tool": "dummy", "args": {}},
        {"step": "Step 2", "tool": "dummy", "args": {}},
    ]
    # Monkeypatch _create_plan to return our predefined plan
    async def fake_create_plan(self, task, context):
        return self.plan
    monkeypatch.setattr(AgentManager, "_create_plan", fake_create_plan)

    manager.state = AgentState.INIT
    manager._user_input = "test"
    manager._context = ""

    # Monkeypatch verification to always succeed
    async def always_success(_self, _result):
        return {"success": True, "reason": ""}
    monkeypatch.setattr(AgentManager, "_verify_result", always_success)

    async def inner():
        await manager.step()  # INIT -> PLAN (patched)
        await manager.step()  # PLAN -> EXECUTE
        for _ in range(3):
            manager.results.append({"step": {}, "tool": "dummy", "result": "same", "index": 0})
            manager.doom_detector.record_call("dummy", {}, "same")
            state, out = await manager._handle_verify()
            if state == AgentState.PAUSED:
                return state, out
        return None, None

    state, out = asyncio.run(inner())
    assert state == AgentState.PAUSED, "AgentManager should pause on doom loop detection"
    assert out["event"] == "doom_loop"
    assert out["info"]["tool"] == "dummy"
