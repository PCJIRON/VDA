"""Tests for the AgentManager state machine.

Covers state transitions, pause/resume/abort lifecycle, max iteration
limit, and reset behavior. Uses mocked api_client and tool_registry
since AgentManager is a pure state machine testable without PyQt.
"""

import asyncio
from unittest.mock import MagicMock

import pytest

from qwen_desktop.core.agent_manager import AgentManager, AgentState


@pytest.fixture
def mock_api_client():
    """Create a mock API client for testing."""
    client = MagicMock()
    client.send_message = MagicMock()
    return client


@pytest.fixture
def mock_tool_registry():
    """Create a mock tool registry for testing."""
    return MagicMock()


class TestAgentState:
    """Verify all AgentState enum values exist with correct string values."""

    def test_all_states_present(self):
        """Check all lifecycle states exist in the re-plan-per-step design."""
        states = {s.name: s.value for s in AgentState}
        assert states["IDLE"] == "idle"
        assert states["INIT"] == "init"
        assert states["PLAN"] == "plan"
        assert states["EXECUTE"] == "execute"
        assert states["VERIFY"] == "verify"
        assert states["COMPLETE"] == "complete"
        assert states["ERROR"] == "error"
        assert states["PAUSED"] == "paused"
        # ITERATE was removed in the re-plan design — verification is implicit
        assert "ITERATE" not in states
        assert len(states) == 8

    def test_enum_values_are_unique(self):
        """Verify no duplicate enum values."""
        values = [s.value for s in AgentState]
        assert len(values) == len(set(values))


class TestAgentManager:
    """Test AgentManager state machine behavior."""

    def test_initial_state_idle(self, mock_api_client, mock_tool_registry):
        """A new AgentManager starts in IDLE state."""
        manager = AgentManager(mock_api_client, mock_tool_registry)
        assert manager.state == AgentState.IDLE

    def test_pause_sets_paused(self, mock_api_client, mock_tool_registry):
        """pause() sets the state to PAUSED and stores the reason."""
        manager = AgentManager(mock_api_client, mock_tool_registry)
        manager.state = AgentState.EXECUTE  # Simulate active state

        manager.pause("Test pause reason")
        assert manager.state == AgentState.PAUSED
        assert manager._paused_reason == "Test pause reason"

    def test_resume_returns_to_plan(self, mock_api_client, mock_tool_registry):
        """resume() restores PLAN state after pause (re-plan with new screenshot)."""
        manager = AgentManager(mock_api_client, mock_tool_registry)
        manager.state = AgentState.PAUSED
        manager._paused_reason = "Test"

        manager.resume()
        # In the re-plan design, resume goes back to PLAN so the agent
        # re-evaluates the (now changed) screen state.
        assert manager.state == AgentState.PLAN
        assert manager._paused_reason is None

    def test_abort_sets_complete(self, mock_api_client, mock_tool_registry):
        """abort() sets the state to COMPLETE."""
        manager = AgentManager(mock_api_client, mock_tool_registry)
        manager.state = AgentState.EXECUTE

        manager.abort()
        assert manager.state == AgentState.COMPLETE

    def test_reset_returns_to_idle(self, mock_api_client, mock_tool_registry):
        """reset() returns to IDLE with clean state."""
        manager = AgentManager(mock_api_client, mock_tool_registry)

        # Put manager in a non-trivial state
        manager.state = AgentState.EXECUTE
        manager.plan = [{"step": "test", "tool": "echo"}]
        manager.current_step = 1
        manager.iteration_count = 5
        manager.results = [{"status": "ok"}]
        manager._error = "some error"
        manager.pause("Reason")

        # Reset
        manager.reset()
        assert manager.state == AgentState.IDLE
        assert manager.plan == []
        assert manager.current_step == 0
        assert manager.iteration_count == 0
        assert manager.results == []
        assert manager._error is None
        assert manager._paused_reason is None

    def test_max_iterations_property(self, mock_api_client, mock_tool_registry):
        """Constructor respects max_iterations parameter."""
        manager = AgentManager(mock_api_client, mock_tool_registry, max_iterations=5)
        assert manager.max_iterations == 5

        # Default is 30 in the re-plan design (one PLAN per step, so more
        # headroom is needed vs the old static-plan design).
        default_manager = AgentManager(mock_api_client, mock_tool_registry)
        assert default_manager.max_iterations == 30

    def test_step_returns_paused_state(self, mock_api_client, mock_tool_registry):
        """When paused, step() returns immediately."""
        manager = AgentManager(mock_api_client, mock_tool_registry)
        manager.state = AgentState.PAUSED
        manager._paused_reason = "Doom loop"

        async def run_step():
            return await manager.step()

        next_state, output = asyncio.run(run_step())
        assert next_state == AgentState.PAUSED
        assert output["event"] == "paused"
        assert output["reason"] == "Doom loop"

    def test_step_idle_no_handler(self, mock_api_client, mock_tool_registry):
        """IDLE state has no handler — step() returns immediately."""
        manager = AgentManager(mock_api_client, mock_tool_registry)

        async def run_step():
            return await manager.step()

        next_state, output = asyncio.run(run_step())
        assert next_state == AgentState.IDLE
        assert output is None

    def test_subsystems_created(self, mock_api_client, mock_tool_registry):
        """AgentManager creates doom_detector and permission_system."""
        manager = AgentManager(mock_api_client, mock_tool_registry)
        assert manager.doom_detector is not None
        assert manager.permission_system is not None

    def test_handle_init_transition(self, mock_api_client, mock_tool_registry):
        """INIT handler transitions to PLAN."""
        from qwen_desktop.core.agent_manager.agent_manager import AgentManager as AM

        manager = AM(mock_api_client, mock_tool_registry)
        manager.state = AgentState.INIT

        async def run_step():
            return await manager.step()

        next_state, output = asyncio.run(run_step())
        assert next_state == AgentState.PLAN
        assert output["event"] == "init_complete"

    def test_handle_complete_returns_results(self, mock_api_client, mock_tool_registry):
        """COMPLETE handler returns results."""
        manager = AgentManager(mock_api_client, mock_tool_registry)
        manager.state = AgentState.COMPLETE
        manager.results = [{"status": "done"}]

        async def run_step():
            return await manager.step()

        next_state, output = asyncio.run(run_step())
        assert next_state == AgentState.COMPLETE
        assert output["event"] == "completed"
        assert output["results"] == [{"status": "done"}]

    def test_handle_error_returns_message(self, mock_api_client, mock_tool_registry):
        """ERROR handler returns error message."""
        manager = AgentManager(mock_api_client, mock_tool_registry)
        manager.state = AgentState.ERROR
        manager._error = "Something went wrong"

        async def run_step():
            return await manager.step()

        next_state, output = asyncio.run(run_step())
        assert next_state == AgentState.ERROR
        assert output["event"] == "error"
        assert output["message"] == "Something went wrong"
