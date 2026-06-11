"""Agent manager subsystem — state machine, sub-agent delegation, session
compaction, doom loop detection, and permission system.

The agent_manager package implements the Antigravity-style agent loop:
spec → plan → execute → verify → iterate, with sub-agent delegation for
specialized workers, session compaction for context management, doom loop
detection, and per-tool permission control.
"""

from vda.core.agent_manager.agent_manager import AgentManager, AgentState
from vda.core.agent_manager.agent_worker import AgentWorker
from vda.core.agent_manager.doom_detector import DoomLoopDetector, ToolCallRecord
from vda.core.agent_manager.permission_system import PermissionSystem, PermissionDecision
from vda.core.agent_manager.session_compactor import SessionCompactor
from vda.core.agent_manager.sub_agent_delegator import (
    SubAgentDelegator,
    SubAgentContext,
    SubAgentResult,
)

__all__ = [
    "AgentManager",
    "AgentState",
    "AgentWorker",
    "DoomLoopDetector",
    "ToolCallRecord",
    "PermissionSystem",
    "PermissionDecision",
    "SessionCompactor",
    "SubAgentDelegator",
    "SubAgentContext",
    "SubAgentResult",
]
