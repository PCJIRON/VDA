"""Agent module — orchestrates the iterative re-plan loop.

Provides the AgentManager (state machine), AgentWorker (QThread wrapper),
DoomLoopDetector, PermissionSystem, and SubAgentDelegator.
"""

from vda.core.agent_manager.agent_manager import AgentManager, AgentState
from vda.core.agent_manager.agent_worker import AgentWorker
from vda.core.agent_manager.doom_detector import DoomLoopDetector, ToolCallRecord
from vda.core.agent_manager.permission_system import PermissionDecision, PermissionSystem
from vda.core.agent_manager.session_compactor import SessionCompactor

__all__ = [
    "AgentManager",
    "AgentState",
    "AgentWorker",
    "DoomLoopDetector",
    "ToolCallRecord",
    "PermissionSystem",
    "PermissionDecision",
    "SessionCompactor",
]
