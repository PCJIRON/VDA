"""File operations for the ToolExecutor.

Extracted from the original monolithic ``tool_executor.py``.
"""

import os
import re
import glob
import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


def resolve_path(filepath: str, workspace_dir: str) -> Path:
    """Resolve a file path relative to workspace.

    Args:
        filepath: Path to resolve.
        workspace_dir: Base directory for relative paths.

    Returns:
        Resolved absolute Path.
    """
    path = Path(filepath)
    if not path.is_absolute():
        path = Path(workspace_dir) / path
    return path.resolve()


def read_file(filepath: str, workspace_dir: str) -> str:
    """Read file contents.

    Args:
        filepath: Path to read.
        workspace_dir: Base directory for relative paths.

    Returns:
        File contents or error message.
    """
    path = resolve_path(filepath, workspace_dir)
    if not path.exists():
        return f"Error: File not found: {filepath}"
    if not path.is_file():
        return f"Error: Not a file: {filepath}"
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return f"--- {filepath} ---\n{content}"
    except UnicodeDecodeError:
        return f"Error: File is binary or not utf-8 encoded: {filepath}"


def write_file(filepath: str, content: str, workspace_dir: str) -> str:
    """Write content to file.

    Args:
        filepath: Path to write.
        content: Content to write.
        workspace_dir: Base directory for relative paths.

    Returns:
        Success message.
    """
    path = resolve_path(filepath, workspace_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Successfully wrote to {filepath}"


def search_files(query: str, search_type: str, workspace_dir: str) -> str:
    """Search for files using glob or grep.

    Args:
        query: Search query (glob pattern or regex).
        search_type: 'grep' or 'glob'.
        workspace_dir: Base directory.

    Returns:
        Search results.
    """
    if search_type == "glob":
        pattern = str(resolve_path(query, workspace_dir))
        if not os.path.isabs(query) and not query.startswith("**"):
            pattern = str(resolve_path(f"**/{query}", workspace_dir))
        matches = glob.glob(pattern, recursive=True)
        if not matches:
            return "No files found matching glob pattern."
        rel_matches = [os.path.relpath(m, workspace_dir) for m in matches[:100]]
        result = f"Found {len(matches)} files:\n" + "\n".join(rel_matches)
        if len(matches) > 100:
            result += "\n... (truncated)"
        return result

    if search_type == "grep":
        results_tmp: List[str] = []
        try:
            pattern = re.compile(query)
        except re.error as e:
            return f"Error: Invalid regex pattern: {e}"
        for root, dirs, files in os.walk(workspace_dir):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for file in files:
                if file.endswith((".pyc", ".exe", ".dll", ".so", ".pdf", ".png", ".jpg")):
                    continue
                path = os.path.join(root, file)
                rel_path = os.path.relpath(path, workspace_dir)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        for i, line in enumerate(f, 1):
                            if pattern.search(line):
                                results_tmp.append(f"{rel_path}:{i}:{line.strip()}")
                                if len(results_tmp) >= 50:
                                    results_tmp.append("... (truncated)")
                                    return "\n".join(results_tmp)
                except (UnicodeDecodeError, IOError):
                    pass
        if not results_tmp:
            return "No matches found."
        return "\n".join(results_tmp)

    return f"Error: Unknown search type '{search_type}'"
