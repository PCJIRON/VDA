"""
Slash command registry for Qwen Desktop.

Port of qwen-code's command system (packages/cli/src/commands/).
Provides /help, /clear, /model, /theme, /stats, /quit commands.
"""

from dataclasses import dataclass
from typing import Callable, Optional, List
import logging

logger = logging.getLogger(__name__)


@dataclass
class SlashCommand:
    """Definition of a slash command."""

    name: str
    description: str
    aliases: List[str]
    handler: Optional[Callable] = None
    usage: str = ""

    @property
    def display_name(self) -> str:
        """Get display name with slash."""
        return f"/{self.name}"


class CommandRegistry:
    """Registry for slash commands (matches qwen-code's CommandRegistry)."""

    def __init__(self) -> None:
        """Initialize command registry with default commands."""
        self._commands: dict[str, SlashCommand] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Register default slash commands."""
        defaults = [
            SlashCommand(
                name="help",
                description="Show available commands and keyboard shortcuts",
                aliases=["h", "?"],
                usage="/help [command]",
            ),
            SlashCommand(
                name="clear",
                description="Clear the conversation history",
                aliases=["cls"],
                usage="/clear",
            ),
            SlashCommand(
                name="new",
                description="Start a new conversation",
                aliases=["n"],
                usage="/new",
            ),
            SlashCommand(
                name="model",
                description="Change the AI model",
                aliases=["m"],
                usage="/model [model-name]",
            ),
            SlashCommand(
                name="theme",
                description="Change the color theme",
                aliases=["t"],
                usage="/theme [theme-name]",
            ),
            SlashCommand(
                name="stats",
                description="Show session statistics",
                aliases=["s"],
                usage="/stats",
            ),
            SlashCommand(
                name="settings",
                description="Open settings dialog",
                aliases=["config", "prefs"],
                usage="/settings",
            ),
            SlashCommand(
                name="save",
                description="Save the current conversation",
                aliases=[],
                usage="/save",
            ),
            SlashCommand(
                name="compact",
                description="Compress conversation history to save tokens",
                aliases=["compress"],
                usage="/compact",
            ),
            SlashCommand(
                name="quit",
                description="Exit the application",
                aliases=["q", "exit"],
                usage="/quit",
            ),
        ]

        for cmd in defaults:
            self.register(cmd)

    def register(self, command: SlashCommand) -> None:
        """Register a slash command.

        Args:
            command: Command to register.
        """
        self._commands[command.name] = command
        for alias in command.aliases:
            self._commands[alias] = command

    def get_command(self, name: str) -> Optional[SlashCommand]:
        """Get a command by name or alias.

        Args:
            name: Command name (without slash).

        Returns:
            SlashCommand or None.
        """
        return self._commands.get(name)

    def get_all_commands(self) -> List[SlashCommand]:
        """Get all unique commands (no duplicates from aliases).

        Returns:
            List of unique commands.
        """
        seen = set()
        result = []
        for cmd in self._commands.values():
            if cmd.name not in seen:
                seen.add(cmd.name)
                result.append(cmd)
        return result

    def get_completions(self, prefix: str) -> List[str]:
        """Get command name completions for a prefix.

        Args:
            prefix: Prefix to match (without slash).

        Returns:
            List of matching command names.
        """
        prefix_lower = prefix.lower()
        matches = set()

        for name, cmd in self._commands.items():
            if name.startswith(prefix_lower):
                matches.add(cmd.name)

        return sorted(matches)

    def is_command(self, text: str) -> bool:
        """Check if text starts with a slash command.

        Args:
            text: Input text.

        Returns:
            True if text is a slash command.
        """
        if not text.startswith("/"):
            return False

        parts = text[1:].split(maxsplit=1)
        if parts:
            return parts[0].lower() in self._commands

        return False

    def parse_command(self, text: str) -> tuple[Optional[SlashCommand], str]:
        """Parse a slash command from text.

        Args:
            text: Input text starting with /.

        Returns:
            Tuple of (command, arguments_string).
        """
        if not text.startswith("/"):
            return None, text

        parts = text[1:].split(maxsplit=1)
        if not parts:
            return None, ""

        cmd_name = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        cmd = self.get_command(cmd_name)
        return cmd, args

    def get_help_text(self) -> str:
        """Get formatted help text for all commands.

        Returns:
            Help text string.
        """
        commands = self.get_all_commands()
        lines = ["Available Commands:", ""]

        for cmd in commands:
            aliases = ""
            if cmd.aliases:
                aliases = f" (aliases: {', '.join('/' + a for a in cmd.aliases)})"
            lines.append(f"  /{cmd.name:<12} {cmd.description}{aliases}")

        lines.append("")
        lines.append("Keyboard Shortcuts:")
        lines.append("  Enter          Send message")
        lines.append("  Shift+Enter    New line")
        lines.append("  Ctrl+N         New conversation")
        lines.append("  Ctrl+S         Save conversation")
        lines.append("  Ctrl+,         Open settings")
        lines.append("  Ctrl+Q         Quit")

        return "\n".join(lines)
