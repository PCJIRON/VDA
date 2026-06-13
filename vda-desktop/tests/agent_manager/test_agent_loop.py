from vda.core.agent_manager.agent_manager import AgentManager, AgentState
from vda.core.agent_manager.doom_detector import DoomLoopDetector


class DummyAPI:
    async def send_message(self, prompt, msgs):
        # Used by _handle_plan — not needed for doom-loop test.
        if False:
            yield "{}"


def test_doom_loop_detection_and_pause():
    """Test that identical tool calls trigger doom loop detection.

    In the re-plan-per-step design, doom-loop detection lives in the
    DoomLoopDetector (called by AgentWorker after each step). The manager
    is paused explicitly when the worker detects a loop. This test
    verifies the detector itself, and that AgentManager.pause() flips
    the state to PAUSED.
    """
    detector = DoomLoopDetector()
    # Three identical calls should be flagged as a doom loop
    for _ in range(3):
        detector.record_call("dummy", {"x": 1}, "same result")
    info = detector.check_loop()
    assert info is not None, "DoomLoopDetector should report a loop after 3 identical calls"
    assert info["tool"] == "dummy"

    # And AgentManager.pause() should flip the state
    dummy_api = DummyAPI()
    dummy_registry = type("DummyRegistry", (), {"get_tool": lambda self, name: None})()
    manager = AgentManager(api_client=dummy_api, tool_registry=dummy_registry, max_iterations=5)

    manager.pause("test pause")
    assert manager.state == AgentState.PAUSED
    assert manager._paused_reason == "test pause"
