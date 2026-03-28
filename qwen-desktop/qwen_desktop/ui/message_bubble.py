"""
Message bubble widget for displaying individual messages.

Handles rendering of user and AI messages with markdown support.
Uses qwen-code theme colors and code syntax highlighting.
"""

import markdown

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QTextEdit,
    QToolButton,
    QApplication,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QTextDocument

from qwen_desktop.ui.theme_manager import ThemeManager


class MessageBubble(QFrame):
    """Message bubble widget."""

    def __init__(
        self,
        text: str,
        is_user: bool = False,
        is_system: bool = False,
        parent: None = None,
    ) -> None:
        """Initialize the message bubble.

        Args:
            text: Message text.
            is_user: True if message is from user.
            is_system: True if message is a system message.
            parent: Parent widget.
        """
        super().__init__(parent)

        self.text = text
        self.is_user = is_user
        self.is_system = is_system

        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self) -> None:
        """Set up the UI components."""
        tm = ThemeManager.instance()
        c = tm.colors
        s = tm.semantic

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        # Header row with role label and copy button
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        # Role label
        if self.is_user:
            role_label = QLabel("You")
            role_label.setStyleSheet(
                f"color: {c.AccentBlue}; font-weight: bold; font-size: 12px; background: transparent;"
            )
        elif self.is_system:
            role_label = QLabel("System")
            role_label.setStyleSheet(
                f"color: {c.Comment}; font-weight: bold; font-size: 11px; background: transparent;"
            )
        else:
            role_label = QLabel(">_ Qwen")
            role_label.setStyleSheet(
                f"color: {c.AccentYellow}; font-weight: bold; font-size: 12px; background: transparent;"
            )

        header_layout.addWidget(role_label)
        header_layout.addStretch()

        # Copy button (for all messages)
        if not self.is_system:
            self.copy_btn = QToolButton()
            self.copy_btn.setText("📋")
            self.copy_btn.setToolTip("Copy message")
            self.copy_btn.setFixedSize(24, 24)
            self.copy_btn.setStyleSheet(
                f"""
                QToolButton {{
                    background: transparent;
                    border: none;
                    border-radius: 4px;
                    font-size: 14px;
                }}
                QToolButton:hover {{
                    background-color: {s.background.hover};
                }}
                """
            )
            self.copy_btn.clicked.connect(self._copy_to_clipboard)
            header_layout.addWidget(self.copy_btn)

        layout.addLayout(header_layout)

        # Message content
        self.message_label = QTextEdit()
        self.message_label.setReadOnly(True)
        self.message_label.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.message_label.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.message_label.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        # Render content based on type
        if self.is_system:
            self.message_label.setPlainText(self.text)
            self.message_label.setFont(QFont("Consolas", 10))
        elif self.is_user:
            self.message_label.setPlainText(self.text)
            self.message_label.setFont(QFont("Segoe UI", 12))
        else:
            # AI message: render markdown with code highlighting
            html = self._render_markdown(self.text)
            self.message_label.setHtml(html)
            self.message_label.setFont(QFont("Segoe UI", 12))

        # Auto-resize height
        self.message_label.document().contentsChanged.connect(self._adjust_height)
        self._adjust_height()

        layout.addWidget(self.message_label)

        # Set frame shape
        self.setFrameShape(QFrame.Shape.NoFrame)

    def _render_markdown(self, text: str) -> str:
        """Render markdown to styled HTML.

        Args:
            text: Markdown text.

        Returns:
            Styled HTML string.
        """
        tm = ThemeManager.instance()
        c = tm.colors

        # Convert markdown to HTML
        html = markdown.markdown(
            text,
            extensions=["fenced_code", "codehilite", "tables", "nl2br"],
            extension_configs={
                "codehilite": {
                    "css_class": "code",
                    "noclasses": True,
                    "pygments_style": "monokai",
                }
            },
        )

        # Wrap in styled container with qwen-dark code colors
        styled_html = f"""
        <style>
            body {{
                color: {c.Foreground};
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
                line-height: 1.6;
            }}
            code {{
                background-color: {c.Gray};
                color: {c.AccentCyan};
                padding: 2px 6px;
                border-radius: 4px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
            }}
            pre {{
                background-color: #111419;
                border: 1px solid {c.Gray};
                border-radius: 8px;
                padding: 12px;
                overflow-x: auto;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                line-height: 1.5;
            }}
            pre code {{
                background-color: transparent;
                padding: 0;
                color: {c.Foreground};
            }}
            a {{
                color: {c.AccentBlue};
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
            }}
            strong {{
                color: {c.AccentYellow};
            }}
            em {{
                color: {c.AccentPurple};
                font-style: italic;
            }}
            h1, h2, h3, h4 {{
                color: {c.AccentYellow};
                margin-top: 16px;
                margin-bottom: 8px;
            }}
            ul, ol {{
                margin-left: 16px;
            }}
            li {{
                margin-bottom: 4px;
            }}
            blockquote {{
                border-left: 3px solid {c.AccentBlue};
                padding-left: 12px;
                margin: 8px 0;
                color: {c.Comment};
            }}
            table {{
                border-collapse: collapse;
                margin: 8px 0;
            }}
            th, td {{
                border: 1px solid {c.Gray};
                padding: 6px 12px;
            }}
            th {{
                background-color: #111419;
                color: {c.AccentYellow};
            }}
            hr {{
                border: none;
                border-top: 1px solid {c.Gray};
                margin: 16px 0;
            }}
        </style>
        {html}
        """

        return styled_html

    def _adjust_height(self) -> None:
        """Adjust the text edit height to fit content."""
        doc = self.message_label.document()
        doc.setTextWidth(self.message_label.viewport().width() or 600)
        height = int(doc.size().height()) + 10
        # Clamp height
        min_h = 30
        max_h = 800
        self.message_label.setFixedHeight(max(min_h, min(height, max_h)))

    def _copy_to_clipboard(self) -> None:
        """Copy message text to clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text)

        # Show feedback
        self.copy_btn.setText("✅")
        QTimer.singleShot(1500, lambda: self.copy_btn.setText("📋"))

    def _apply_styles(self) -> None:
        """Apply styles based on message type."""
        tm = ThemeManager.instance()
        c = tm.colors
        s = tm.semantic

        if self.is_user:
            # User message - right aligned with accent
            self.setStyleSheet(f"""
                MessageBubble {{
                    background-color: {c.AccentBlue}22;
                    border: 1px solid {c.AccentBlue}44;
                    border-radius: 12px;
                    margin-left: 60px;
                }}
                QTextEdit {{
                    background-color: transparent;
                    color: {c.Foreground};
                    border: none;
                }}
            """)
        elif self.is_system:
            # System message - centered, subtle
            self.setStyleSheet(f"""
                MessageBubble {{
                    background-color: {s.background.elevated};
                    border: 1px solid {s.border.subtle};
                    border-radius: 8px;
                    margin-left: 40px;
                    margin-right: 40px;
                }}
                QTextEdit {{
                    background-color: transparent;
                    color: {c.Comment};
                    border: none;
                }}
            """)
        else:
            # AI message - left aligned
            self.setStyleSheet(f"""
                MessageBubble {{
                    background-color: {s.background.secondary};
                    border: 1px solid {s.border.subtle};
                    border-radius: 12px;
                    margin-right: 60px;
                }}
                QTextEdit {{
                    background-color: transparent;
                    color: {c.Foreground};
                    border: none;
                }}
            """)
