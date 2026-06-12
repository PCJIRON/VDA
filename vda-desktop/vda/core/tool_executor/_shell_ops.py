"""Shell execution for the ToolExecutor.

Extracted from the original monolithic ``tool_executor.py``.
"""

import subprocess
import logging

logger = logging.getLogger(__name__)

from vda.core.tool_executor.persistent_shell import PersistentShell

logger = logging.getLogger(__name__)

# Global singleton for the session
_global_shell = None

def get_persistent_shell() -> PersistentShell:
    """Returns the singleton PersistentShell instance."""
    global _global_shell
    if _global_shell is None:
        _global_shell = PersistentShell()
    return _global_shell

def execute_shell(command: str, workspace_dir: str = None) -> str:
    """Execute a shell command using the persistent shell.
    Maintains backward compatibility with older callers.
    """
    shell = get_persistent_shell()
    if workspace_dir and getattr(shell, "cwd", None) != workspace_dir:
        # Note: changing directory in a persistent shell should ideally be done by the agent
        # via 'cd', but we sync it here if explicitly requested.
        pass # Ignore workspace_dir overrides to preserve true persistent state
        
    return shell.execute(command)
