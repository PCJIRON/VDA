"""
UI component for displaying tool executions.

Matches qwen-code's ToolStatsDisplay.tsx.
Visualizes file reads, writes, and shell commands.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QProgressBar,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from qwen_desktop.ui.theme_manager import ThemeManager


class ToolDisplay(QFrame):
    """Widget for visualizing a tool execution process."""

    def __init__(self, tool_name: str, args: dict, parent=None):
        """Initialize tool display.

        Args:
            tool_name: Name of tool (e.g., read_file).
            args: Arguments passed to tool.
            parent: Parent widget.
        """
        super().__init__(parent)
        self.tool_name = tool_name
        self.args = args
        self._status = "running"
        
        self._setup_ui()
        self._apply_styles()

    def _get_icon_and_desc(self) -> tuple[str, str]:
        """Get icon and description based on tool name."""
        if self.tool_name == "read_file":
            filepath = self.args.get("filepath", "")
            return "📄", f"Reading {filepath}"
        elif self.tool_name == "write_file":
            filepath = self.args.get("filepath", "")
            return "📝", f"Writing {filepath}"
        elif self.tool_name == "execute_shell":
            command = self.args.get("command", "")
            if len(command) > 40:
                command = command[:37] + "..."
            return "⚡", f"Executing: {command}"
        elif self.tool_name == "search_files":
            query = self.args.get("query", "")
            return "🔍", f"Searching for '{query}'"
        else:
            return "🔧", f"Running {self.tool_name}"

    def _setup_ui(self) -> None:
        """Set up the UI components."""
        tm = ThemeManager.instance()
        c = tm.colors
        s = tm.semantic

        self.setFrameShape(QFrame.Shape.StyledPanel)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        # Icon
        icon, desc = self._get_icon_and_desc()
        
        self.icon_label = QLabel(icon)
        self.icon_label.setFont(QFont("Segoe UI Emoji", 12))
        self.icon_label.setStyleSheet("background: transparent;")
        header_layout.addWidget(self.icon_label)

        # Description
        self.desc_label = QLabel(desc)
        self.desc_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.desc_label.setStyleSheet(f"color: {s.text.primary}; background: transparent;")
        header_layout.addWidget(self.desc_label)

        header_layout.addStretch()

        # Status
        self.status_label = QLabel("Running...")
        self.status_label.setFont(QFont("Segoe UI", 10))
        self.status_label.setStyleSheet(f"color: {c.AccentYellow}; background: transparent;")
        header_layout.addWidget(self.status_label)

        layout.addLayout(header_layout)

        # Progress bar (indeterminate)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # indeterminate
        self.progress.setFixedHeight(4)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: {s.background.input};
                border: none;
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background-color: {c.AccentBlue};
                border-radius: 2px;
            }}
        """)
        layout.addWidget(self.progress)

    def _apply_styles(self) -> None:
        """Apply theme styling."""
        tm = ThemeManager.instance()
        s = tm.semantic

        self.setStyleSheet(f"""
            ToolDisplay {{
                background-color: {s.background.elevated};
                border: 1px solid {s.border.subtle};
                border-radius: 8px;
            }}
        """)

    def set_complete(self, success: bool = True, output: str = "") -> None:
        """Mark tool execution as complete.

        Args:
            success: Whether execution was successful.
            output: Optional output string.
        """
        tm = ThemeManager.instance()
        c = tm.colors
        
        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        
        if success:
            self._status = "success"
            self.status_label.setText("Completed")
            self.status_label.setStyleSheet(f"color: {c.AccentGreen}; background: transparent;")
            self.progress.setStyleSheet(f"""
                QProgressBar {{ background-color: {c.Gray}; border: none; border-radius: 2px; }}
                QProgressBar::chunk {{ background-color: {c.AccentGreen}; border-radius: 2px; }}
            """)
        else:
            self._status = "error"
            self.status_label.setText("Failed")
            self.status_label.setStyleSheet(f"color: {c.AccentRed}; background: transparent;")
            self.progress.setStyleSheet(f"""
                QProgressBar {{ background-color: {c.Gray}; border: none; border-radius: 2px; }}
                QProgressBar::chunk {{ background-color: {c.AccentRed}; border-radius: 2px; }}
            """)

        # If there's output, show a snippet
        if output and len(output) > 0:
            snippet = QLabel(output[:100] + ("..." if len(output) > 100 else ""))
            snippet.setFont(QFont("Consolas", 9))
            snippet.setStyleSheet(f"color: {c.Comment}; background: transparent; padding-top: 4px;")
            self.layout().addWidget(snippet)
