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
    import tempfile
    import os

    stdout_fd, stdout_path = tempfile.mkstemp()
    stderr_fd, stderr_path = tempfile.mkstemp()

    try:
        with open(stdout_fd, "wb") as stdout_file, open(stderr_fd, "wb") as stderr_file:
            result = subprocess.run(
                command,
                shell=True,
                cwd=workspace_dir,
                stdout=stdout_file,
                stderr=stderr_file,
                timeout=30,
            )

        # Read the outputs
        with open(stdout_path, "r", encoding="utf-8", errors="replace") as f:
            stdout_content = f.read()
        with open(stderr_path, "r", encoding="utf-8", errors="replace") as f:
            stderr_content = f.read()

        output = ""
        if stdout_content:
            output += stdout_content
        if stderr_content:
            output += f"\nSTDERR:\n{stderr_content}"
        if not output:
            output = f"Command executed successfully (exit code {result.returncode}), no output."
        return output
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds."
    except Exception as exc:
        return f"Error executing command: {str(exc)}"
    finally:
        # Clean up temporary files
        try:
            if os.path.exists(stdout_path):
                os.remove(stdout_path)
        except Exception:
            pass
        try:
            if os.path.exists(stderr_path):
                os.remove(stderr_path)
        except Exception:
            pass
