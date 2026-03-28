"""
Tool execution framework for Qwen Desktop.

Provides local execution of file operations and shell commands,
matching qwen-code's CLI capabilities.
"""

import os
import subprocess
import glob
import re
from typing import Dict, Any, List, Optional
from pathlib import Path


class ToolExecutor:
    """Executes local tools (fileops, shell) for the AI assistant."""

    def __init__(self, workspace_dir: str = None) -> None:
        """Initialize the tool executor.

        Args:
            workspace_dir: Default working directory for tools.
        """
        self.workspace_dir = workspace_dir or os.getcwd()

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get OpenAI-compatible tool definitions.

        Returns:
            List of tool schemas.
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read the contents of a file.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filepath": {
                                "type": "string",
                                "description": "Path to the file to read"
                            }
                        },
                        "required": ["filepath"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Write content to a file. Overwrites if exists.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filepath": {
                                "type": "string",
                                "description": "Path to the file to write"
                            },
                            "content": {
                                "type": "string",
                                "description": "Content to write to the file"
                            }
                        },
                        "required": ["filepath", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "execute_shell",
                    "description": "Execute a shell command. Requires user approval for destructive commands.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "The shell command to execute"
                            }
                        },
                        "required": ["command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_files",
                    "description": "Search for files using glob pattern or grep regex.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Regex pattern to search for (grep) or glob pattern"
                            },
                            "type": {
                                "type": "string",
                                "enum": ["grep", "glob"],
                                "description": "Type of search"
                            }
                        },
                        "required": ["query", "type"]
                    }
                }
            }
        ]

    def _resolve_path(self, filepath: str) -> Path:
        """Resolve a file path relative to workspace.

        Args:
            filepath: Path to resolve.

        Returns:
            Resolved absolute Path.
        """
        path = Path(filepath)
        if not path.is_absolute():
            path = Path(self.workspace_dir) / path
        return path.resolve()

    def execute_tool(self, name: str, kwargs: Dict[str, Any]) -> str:
        """Execute a tool by name.

        Args:
            name: Tool name.
            kwargs: Tool arguments.

        Returns:
            Tool result as string.
        """
        try:
            if name == "read_file":
                return self.read_file(**kwargs)
            elif name == "write_file":
                return self.write_file(**kwargs)
            elif name == "execute_shell":
                return self.execute_shell(**kwargs)
            elif name == "search_files":
                return self.search_files(**kwargs)
            else:
                return f"Error: Unknown tool '{name}'"
        except Exception as e:
            return f"Error executing {name}: {str(e)}"

    def read_file(self, filepath: str) -> str:
        """Read file contents.

        Args:
            filepath: Path to read.

        Returns:
            File contents.
        """
        path = self._resolve_path(filepath)
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

    def write_file(self, filepath: str, content: str) -> str:
        """Write content to file.

        Args:
            filepath: Path to write.
            content: Content to write.

        Returns:
            Success message.
        """
        path = self._resolve_path(filepath)
        
        # Create parent directories if they don't exist
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        return f"Successfully wrote to {filepath}"

    def execute_shell(self, command: str) -> str:
        """Execute a shell command.

        Args:
            command: Command to execute.

        Returns:
            Command output.
        """
        # In a real implementation, this would connect to the ShellWidget
        # for user approval and streaming output.
        # For this basic implementation, we just use subprocess.
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.workspace_dir,
                capture_output=True,
                text=True,
                timeout=30
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
        except Exception as e:
            return f"Error executing command: {str(e)}"

    def search_files(self, query: str, type: str) -> str:
        """Search for files.

        Args:
            query: Search query.
            type: 'grep' or 'glob'.

        Returns:
            Search results.
        """
        if type == "glob":
            pattern = str(self._resolve_path(query))
            if not os.path.isabs(query) and not query.startswith("**"):
                 pattern = str(self._resolve_path(f"**/{query}"))
            
            matches = glob.glob(pattern, recursive=True)
            if not matches:
                return "No files found matching glob pattern."
            
            # Make paths relative to workspace
            rel_matches = [os.path.relpath(m, self.workspace_dir) for m in matches[:100]]
            
            result = f"Found {len(matches)} files:\n" + "\n".join(rel_matches)
            if len(matches) > 100:
                result += "\n... (truncated)"
            return result
            
        elif type == "grep":
            # Very basic grep implementation in Python
            # Look through text files in workspace
            results = []
            try:
                pattern = re.compile(query)
            except re.error as e:
                return f"Error: Invalid regex pattern: {e}"

            for root, _, files in os.walk(self.workspace_dir):
                # Skip hidden dirs like .git
                if any(part.startswith('.') for part in Path(root).parts):
                    continue
                    
                for file in files:
                    # Skip common binaries
                    if file.endswith(('.pyc', '.exe', '.dll', '.so', '.pdf', '.png', '.jpg')):
                        continue
                        
                    path = os.path.join(root, file)
                    rel_path = os.path.relpath(path, self.workspace_dir)
                    
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            for i, line in enumerate(f, 1):
                                if pattern.search(line):
                                    results.append(f"{rel_path}:{i}:{line.strip()}")
                                    if len(results) >= 50:
                                        results.append("... (truncated)")
                                        return "\n".join(results)
                    except (UnicodeDecodeError, IOError):
                        pass

            if not results:
                return "No matches found."
            return "\n".join(results)
            
        return f"Error: Unknown search type '{type}'"
