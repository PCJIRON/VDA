"""Agent manager subsystem — state machine, doom loop detection, and permission system.

The agent_manager package implements the Antigravity-style agent loop:
spec → plan → execute → verify → iterate, with doom loop detection
and per-tool permission control.
"""

from qwen_desktop.core.agent_manager.agent_manager import AgentManager, AgentState
from qwen_desktop.core.agent_manager.doom_detector import DoomLoopDetector, ToolCallRecord
from qwen_desktop.core.agent_manager.permission_system import PermissionSystem, PermissionDecision

__all__ = [
    "AgentManager",
    "AgentState",
    "DoomLoopDetector",
    "ToolCallRecord",
    "PermissionSystem",
    "PermissionDecision",
]
