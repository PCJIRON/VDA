"""
Embedded terminal widget for displaying shell commands.

Matches qwen-code's CLI shell execution display.
Provides a read-only terminal-like view for command output.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QLabel,
    QPushButton,
    QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor, QColor

from qwen_desktop.ui.theme_manager import ThemeManager


class ShellWidget(QFrame):
    """Embedded terminal widget for shell commands."""

    aborted = pyqtSignal()
    approved = pyqtSignal()

    def __init__(self, command: str, requires_approval: bool = False, parent=None):
        """Initialize shell widget.

        Args:
            command: Command being executed.
            requires_approval: If true, show approve/reject buttons.
            parent: Parent widget.
        """
        super().__init__(parent)
        self.command = command
        self.requires_approval = requires_approval
        
        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self) -> None:
        """Set up the UI components."""
        tm = ThemeManager.instance()
        c = tm.colors
        s = tm.semantic

        self.setFrameShape(QFrame.Shape.StyledPanel)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header bar
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {s.background.elevated};
                border-bottom: 1px solid {s.border.subtle};
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }}
        """)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 6, 12, 6)
        
        icon = QLabel("⚡")
        header_layout.addWidget(icon)
        
        title = QLabel("Shell execution")
        title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {s.text.primary};")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Command input preview
        cmd_preview = QLabel(self.command)
        cmd_preview.setFont(QFont("Consolas", 9))
        cmd_preview.setStyleSheet(f"color: {c.AccentYellow};")
        header_layout.addWidget(cmd_preview)
        
        layout.addWidget(header)

        # Approval buttons (if needed)
        if self.requires_approval:
            approval_container = QWidget()
            approval_container.setStyleSheet(f"background-color: {s.background.secondary};")
            app_layout = QHBoxLayout(approval_container)
            app_layout.setContentsMargins(12, 8, 12, 8)
            
            warning = QLabel("⚠️ Qwen wants to run this command. Approve?")
            warning.setStyleSheet(f"color: {s.status.warning};")
            app_layout.addWidget(warning)
            
            app_layout.addStretch()
            
            self.approve_btn = QPushButton("✓ Approve")
            self.approve_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {c.AccentGreen};
                    color: black;
                    border: none;
                    border-radius: 4px;
                    padding: 4px 12px;
                    font-weight: bold;
                }}
                QPushButton:hover {{ background-color: #BDFF5C; }}
            """)
            self.approve_btn.clicked.connect(self._on_approve)
            app_layout.addWidget(self.approve_btn)
            
            self.reject_btn = QPushButton("✕ Reject")
            self.reject_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {s.background.hover};
                    color: {s.text.primary};
                    border: 1px solid {s.border.default};
                    border-radius: 4px;
                    padding: 4px 12px;
                }}
            """)
            self.reject_btn.clicked.connect(self._on_reject)
            app_layout.addWidget(self.reject_btn)
            
            layout.addWidget(approval_container)
            self.approval_container = approval_container

        # Terminal output area
        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setFont(QFont("Consolas", 10))
        self.terminal.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.terminal.setMinimumHeight(120)
        self.terminal.setMaximumHeight(300)
        
        # Initial prompt
        self.terminal.append(f"<span style='color: {c.AccentGreen}'>$</span> {self.command}")
        
        layout.addWidget(self.terminal)

    def _apply_styles(self) -> None:
        """Apply theme styling."""
        tm = ThemeManager.instance()
        c = tm.colors
        s = tm.semantic

        self.setStyleSheet(f"""
            ShellWidget {{
                background-color: {c.Background};
                border: 1px solid {s.border.default};
                border-radius: 6px;
            }}
            QTextEdit {{
                background-color: {c.Background};
                color: {c.Foreground};
                border: none;
                padding: 8px;
            }}
        """)

    def _on_approve(self) -> None:
        """Handle approve click."""
        self.approval_container.hide()
        self.approved.emit()

    def _on_reject(self) -> None:
        """Handle reject click."""
        self.approval_container.hide()
        self.append_output("\n[Command rejected by user]", error=True)
        self.aborted.emit()

    def append_output(self, text: str, error: bool = False) -> None:
        """Append text to the terminal output.

        Args:
            text: Text to append.
            error: True if stderr output.
        """
        tm = ThemeManager.instance()
        c = tm.colors
        
        color = c.AccentRed if error else c.Foreground
        
        # Replace newlines with HTML breaks
        formatted_text = text.replace('\n', '<br>')
        
        # Move cursor to end
        cursor = self.terminal.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.terminal.setTextCursor(cursor)
        
        # Insert HTML
        self.terminal.insertHtml(f"<span style='color: {color}'>{formatted_text}</span>")
        
        # Scroll to bottom
        scrollbar = self.terminal.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def set_finished(self, exit_code: int) -> None:
        """Mark execution as finished.

        Args:
            exit_code: Process exit code.
        """
        tm = ThemeManager.instance()
        c = tm.colors
        
        color = c.AccentGreen if exit_code == 0 else c.AccentRed
        self.append_output(f"\n[Process exited with code {exit_code}]", error=exit_code != 0)
