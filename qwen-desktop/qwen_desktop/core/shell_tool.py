"""
Shell Tool - Terminal execution for Qwen Desktop.

Implements the same permission model as qwen-code:
- ask_first: Ask user before each command (default)
- auto_edit: Auto-approve read-only and edit commands
- yolo: Auto-approve everything (dangerous)

Read-only command detection based on AST analysis.
"""

import subprocess
import platform
import logging
import os
import re
from enum import Enum
from typing import Optional, Tuple, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class PermissionMode(Enum):
    ASK_FIRST = "ask_first"
    AUTO_EDIT = "auto_edit"
    YOLO = "yolo"


@dataclass
class ShellCommand:
    command: str
    description: str = ""
    directory: str = ""
    timeout: int = 30


@dataclass
class ShellResult:
    output: str
    error: str
    exit_code: int
    command: str
    truncated: bool = False


READ_ONLY_COMMANDS = [
    "ls", "dir", "ls -l", "ls -la", "ls -lh",
    "cat", "type", "more", "less", "head", "tail",
    "echo", "pwd", "cd",
    "find", "grep", "rg",
    "git status", "git log", "git diff", "git branch", "git show",
    "ipconfig", "ifconfig", "ip",
    "ping", "nslookup", "tracert", "traceroute",
    "netstat", "route",
    "systeminfo", "tasklist", "ps", "top", "whoami", "hostname",
    "uname", "df", "du", "free",
    "date", "time",
    "tree",
    "wc", "sort", "uniq",
    "md5sum", "sha256sum", "certutil",
    "where", "which",
    "getmac", "arp",
    "schtasks /query",
    "sc query",
    "reg query",
    "wmic",
    "powershell -Command Get-",
]

DANGEROUS_PATTERNS = [
    "$(", "`", "<(", ">)",
    "rm -rf /", "rm -rf ~", "del /f /s /q",
    "format ", "diskpart",
    ":(){ :|:& };:",
    "> /dev/sda", "> /dev/nvme",
    "chmod 777 /", "chown -R",
    "mkfs", "dd if=",
    "shutdown /r /f", "shutdown -r now",
    "sudo rm", "sudo dd",
    "net user ", "net localgroup",
    "passwd ",
]


class ShellTool:
    """Shell execution tool with permission modes like qwen-code."""

    def __init__(self, mode: PermissionMode = PermissionMode.ASK_FIRST):
        self.mode = mode
        self._pending_commands: List[ShellCommand] = []

    def set_mode(self, mode: PermissionMode):
        self.mode = mode

    def is_read_only(self, command: str) -> bool:
        """Check if command is read-only (safe to auto-execute)."""
        cmd_lower = command.lower().strip()

        for dangerous in DANGEROUS_PATTERNS:
            if dangerous.lower() in cmd_lower:
                return False

        for safe in READ_ONLY_COMMANDS:
            if cmd_lower.startswith(safe.lower()):
                return True

        safe_prefixes = ["cat ", "type ", "echo ", "cd ", "pwd", "ls ", "dir ", "find ", "grep ", "head ", "tail ", "wc ", "sort "]
        for prefix in safe_prefixes:
            if cmd_lower.startswith(prefix):
                return True

        if cmd_lower.startswith("git ") and any(kw in cmd_lower for kw in ["status", "log", "diff", "branch", "show", "tag", "remote"]):
            return True

        if cmd_lower.startswith("ipconfig") or cmd_lower.startswith("ifconfig") or cmd_lower.startswith("ping "):
            return True

        if cmd_lower.startswith("powershell -command get-"):
            return True

        return False

    def is_dangerous(self, command: str) -> bool:
        """Check if command is dangerous."""
        cmd_lower = command.lower().strip()
        for pattern in DANGEROUS_PATTERNS:
            if pattern.lower() in cmd_lower:
                return True
        if any(cmd_lower.startswith(p) for p in ["rm ", "del ", "format ", "shutdown ", "sudo "]):
            return True
        return False

    def needs_permission(self, command: str) -> bool:
        """Check if command needs user permission based on mode."""
        if self.mode == PermissionMode.YOLO:
            return False

        if self.mode == PermissionMode.AUTO_EDIT:
            if self.is_read_only(command):
                return False
            return True

        return True

    def get_permission_reason(self, command: str) -> str:
        """Get reason why permission is needed."""
        if self.mode == PermissionMode.YOLO:
            return "YOLO mode - auto-approve"
        if self.is_read_only(command):
            return "Read-only command (safe)"
        if self.is_dangerous(command):
            return "DANGEROUS command - review carefully!"
        return "Write/system command - requires approval"

    def execute(self, command: str, directory: str = "", timeout: int = 30) -> ShellResult:
        """Execute a shell command and return result."""
        cwd = directory or os.getcwd()

        try:
            if platform.system() == "Windows":
                proc = subprocess.run(
                    ["cmd", "/c", command],
                    capture_output=True, text=True, timeout=timeout,
                    cwd=cwd, encoding="utf-8", errors="replace"
                )
            else:
                proc = subprocess.run(
                    ["bash", "-c", command],
                    capture_output=True, text=True, timeout=timeout,
                    cwd=cwd
                )

            output = proc.stdout or ""
            error = proc.stderr or ""

            truncated = False
            max_output = 50000
            if len(output) > max_output:
                output = output[:max_output] + f"\n\n... [Output truncated, {len(proc.stdout) - max_output} more chars]"
                truncated = True
            if len(error) > max_output:
                error = error[:max_output] + f"\n\n... [Error truncated]"
                truncated = True

            return ShellResult(
                output=output,
                error=error,
                exit_code=proc.returncode,
                command=command,
                truncated=truncated
            )

        except subprocess.TimeoutExpired:
            return ShellResult(
                output="",
                error=f"Command timed out after {timeout}s",
                exit_code=-1,
                command=command
            )
        except FileNotFoundError:
            return ShellResult(
                output="",
                error=f"Command not found: {command}",
                exit_code=-1,
                command=command
            )
        except Exception as e:
            return ShellResult(
                output="",
                error=str(e),
                exit_code=-1,
                command=command
            )

    def format_result_for_llm(self, result: ShellResult) -> str:
        """Format result for LLM context."""
        parts = []
        parts.append(f"Command: {result.command}")
        parts.append(f"Exit Code: {result.exit_code}")
        if result.output.strip():
            parts.append(f"Output:\n{result.output.strip()}")
        if result.error.strip():
            parts.append(f"Error:\n{result.error.strip()}")
        return "\n".join(parts)

    def format_result_for_user(self, result: ShellResult) -> str:
        """Format result for user display."""
        if result.exit_code == 0:
            status = "Success"
        else:
            status = f"Failed (exit code {result.exit_code})"

        parts = [f"**{status}** - `{result.command}`"]
        if result.output.strip():
            parts.append(f"```\n{result.output.strip()[:5000]}\n```")
        if result.error.strip():
            parts.append(f"**Error:**\n```\n{result.error.strip()[:2000]}\n```")
        return "\n".join(parts)
