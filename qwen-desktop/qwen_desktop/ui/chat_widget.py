"""
Chat widget for displaying conversation history.

Contains the message list and handles message display.
Styled to match qwen-code's dark theme.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QScrollArea,
    QLabel,
    QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

from qwen_desktop.ui.message_bubble import MessageBubble
from qwen_desktop.ui.components.typing_indicator import TypingIndicator
from qwen_desktop.ui.theme_manager import ThemeManager


class ChatWidget(QWidget):
    """Chat widget for displaying conversation."""

    message_added = pyqtSignal(str, bool)  # message, is_user

    def __init__(self, parent: None = None) -> None:
        """Initialize the chat widget.

        Args:
            parent: Parent widget.
        """
        super().__init__(parent)

        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self) -> None:
        """Set up the UI components."""
        tm = ThemeManager.instance()
        s = tm.semantic
        c = tm.colors

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Scroll area for messages
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        # Container for messages
        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setContentsMargins(16, 16, 16, 16)
        self.messages_layout.setSpacing(12)

        # Welcome message
        self.welcome_widget = self._create_welcome()
        self.messages_layout.addWidget(self.welcome_widget)

        self.messages_layout.addStretch()

        self.scroll_area.setWidget(self.messages_container)
        layout.addWidget(self.scroll_area)

        # Typing indicator at bottom
        self.typing_indicator = TypingIndicator()
        self.typing_indicator.hide()
        layout.addWidget(self.typing_indicator)

    def _create_welcome(self) -> QWidget:
        """Create welcome message widget.

        Returns:
            Welcome widget.
        """
        tm = ThemeManager.instance()
        c = tm.colors
        s = tm.semantic

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)
        layout.setContentsMargins(40, 60, 40, 60)

        # Logo / title
        title = QLabel(">_ Qwen Desktop")
        title.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {c.AccentYellow}; background: transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Your AI coding assistant")
        subtitle.setFont(QFont("Segoe UI", 13))
        subtitle.setStyleSheet(f"color: {s.text.secondary}; background: transparent;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        # Tips
        tips = QLabel(
            "Type a message to start chatting • Use /help for commands\n"
            "Drag & drop files to attach • Shift+Enter for new line"
        )
        tips.setFont(QFont("Segoe UI", 10))
        tips.setStyleSheet(f"color: {c.Comment}; background: transparent;")
        tips.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tips.setWordWrap(True)
        layout.addWidget(tips)

        widget.setStyleSheet("background: transparent;")
        return widget

    def _apply_styles(self) -> None:
        """Apply styles to the widget."""
        tm = ThemeManager.instance()
        s = tm.semantic

        self.setStyleSheet(f"""
            ChatWidget {{
                background-color: {s.background.primary};
            }}
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QWidget {{
                background-color: transparent;
            }}
        """)

    def add_message(
        self,
        text: str,
        is_user: bool = False,
        is_system: bool = False,
    ) -> None:
        """Add a message to the chat.

        Args:
            text: Message text.
            is_user: True if message is from user.
            is_system: True if message is a system message.
        """
        # Hide welcome on first message
        if self.welcome_widget.isVisible():
            self.welcome_widget.hide()

        bubble = MessageBubble(text, is_user=is_user, is_system=is_system)

        # Insert before the stretch
        self.messages_layout.insertWidget(
            self.messages_layout.count() - 1,
            bubble,
        )

        # Scroll to bottom after a brief delay to let layout settle
        QTimer.singleShot(50, self._scroll_to_bottom)

        self.message_added.emit(text, is_user)

    def _scroll_to_bottom(self) -> None:
        """Scroll to the bottom of the chat."""
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear(self) -> None:
        """Clear all messages."""
        # Remove all bubbles (keep the stretch)
        while self.messages_layout.count() > 1:
            item = self.messages_layout.itemAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        # Re-add welcome widget
        self.welcome_widget = self._create_welcome()
        self.messages_layout.insertWidget(0, self.welcome_widget)

    def set_typing_indicator(self, showing: bool) -> None:
        """Show or hide typing indicator.

        Args:
            showing: True to show indicator.
        """
        if showing:
            self.typing_indicator.show_indicator()
            QTimer.singleShot(50, self._scroll_to_bottom)
        else:
            self.typing_indicator.hide_indicator()
