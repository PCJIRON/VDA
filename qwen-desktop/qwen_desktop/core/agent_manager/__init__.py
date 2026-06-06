"""Agent manager subsystem — state machine, sub-agent delegation, session
compaction, doom loop detection, and permission system.

The agent_manager package implements the Antigravity-style agent loop:
spec → plan → execute → verify → iterate, with sub-agent delegation for
specialized workers, session compaction for context management, doom loop
detection, and per-tool permission control.
"""

from qwen_desktop.core.agent_manager.agent_manager import AgentManager, AgentState
from qwen_desktop.core.agent_manager.doom_detector import DoomLoopDetector, ToolCallRecord
from qwen_desktop.core.agent_manager.permission_system import PermissionSystem, PermissionDecision
from qwen_desktop.core.agent_manager.session_compactor import SessionCompactor
from qwen_desktop.core.agent_manager.sub_agent_delegator import (
    SubAgentDelegator,
    SubAgentContext,
    SubAgentResult,
)

__all__ = [
    "AgentManager",
    "AgentState",
    "DoomLoopDetector",
    "ToolCallRecord",
    "PermissionSystem",
    "PermissionDecision",
    "SessionCompactor",
    "SubAgentDelegator",
    "SubAgentContext",
    "SubAgentResult",
]
