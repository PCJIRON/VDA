"""Shell execution for the ToolExecutor.

Extracted from the original monolithic ``tool_executor.py``.
"""

import subprocess
import logging

logger = logging.getLogger(__name__)


def execute_shell(command: str, workspace_dir: str) -> str:
    """Execute a shell command.

    Args:
        command: Command to execute.
        workspace_dir: Working directory for the command.

    Returns:
        Command output or error message.
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=workspace_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += f"\nSTDERR:\n{result.stderr}"
        if not output:
            output = f"Command executed successfully (exit code {result.returncode}), no output."
        return output
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds."
    except Exception as exc:
        return f"Error executing command: {str(exc)}"
