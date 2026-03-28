"""
Conversation sidebar for quick access to recent conversations.

Provides a collapsible sidebar with conversation list.
Styled with qwen-dark theme.
"""

from PyQt6.QtWidgets import (
    QDockWidget,
    QListWidget,
    QListWidgetItem,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QMenu,
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QAction, QFont
from typing import Optional

from qwen_desktop.core.conversation_manager import ConversationManager
from qwen_desktop.ui.theme_manager import ThemeManager


class ConversationLoader(QThread):
    """Background thread for loading conversations."""

    loaded = pyqtSignal(list)

    def __init__(self, conversation_manager: ConversationManager, limit: int = 20) -> None:
        super().__init__()
        self.conversation_manager = conversation_manager
        self.limit = limit

    def run(self) -> None:
        """Load conversations in background."""
        convs = self.conversation_manager.get_recent_conversations(self.limit)
        self.loaded.emit(convs)


class ConversationSidebar(QDockWidget):
    """Sidebar widget showing recent conversations."""

    conversation_selected = pyqtSignal(str)  # filepath
    new_conversation = pyqtSignal()
    delete_conversation = pyqtSignal(str)  # filepath

    def __init__(self, parent=None) -> None:
        """Initialize conversation sidebar.

        Args:
            parent: Parent widget.
        """
        super().__init__("Conversations", parent)

        self.conversation_manager = ConversationManager()
        self.current_filepath: Optional[str] = None

        # Allow docking on left and right sides
        self.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea
            | Qt.DockWidgetArea.RightDockWidgetArea
        )

        # Create main widget
        main_widget = QWidget()
        self.setWidget(main_widget)

        # Setup UI
        self._setup_ui()
        self._apply_styles()
        self._connect_signals()

        # Load conversations
        self.load_conversations()

    def _setup_ui(self) -> None:
        """Set up the UI components."""
        tm = ThemeManager.instance()
        c = tm.colors
        s = tm.semantic

        layout = QVBoxLayout(self.widget())
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Header with new button
        header_layout = QHBoxLayout()

        header_label = QLabel("Recent")
        header_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        header_label.setStyleSheet(f"color: {s.text.primary};")
        header_layout.addWidget(header_label)

        header_layout.addStretch()

        # New conversation button
        self.new_btn = QPushButton("+")
        self.new_btn.setFixedSize(28, 28)
        self.new_btn.setToolTip("New Conversation")
        self.new_btn.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.new_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c.AccentBlue};
                color: white;
                border: none;
                border-radius: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {c.LightBlue};
            }}
        """)
        header_layout.addWidget(self.new_btn)

        layout.addLayout(header_layout)

        # Conversation list
        self.list_widget = QListWidget()
        self.list_widget.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        layout.addWidget(self.list_widget)

        # Info label
        self.info_label = QLabel("Click to load conversation")
        self.info_label.setFont(QFont("Segoe UI", 9))
        self.info_label.setStyleSheet(f"color: {c.Comment};")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

    def _apply_styles(self) -> None:
        """Apply styles to the sidebar."""
        tm = ThemeManager.instance()
        c = tm.colors
        s = tm.semantic

        self.setStyleSheet(f"""
            QDockWidget {{
                background-color: {s.background.secondary};
                color: {s.text.primary};
            }}
            QDockWidget::title {{
                background-color: {s.background.secondary};
                padding: 8px;
                border-bottom: 1px solid {s.border.default};
                color: {s.text.primary};
            }}
            QListWidget {{
                background-color: {s.background.secondary};
                color: {s.text.primary};
                border: none;
                font-size: 12px;
            }}
            QListWidget::item {{
                padding: 10px 8px;
                border-radius: 6px;
                margin-bottom: 2px;
            }}
            QListWidget::item:selected {{
                background-color: {c.AccentBlue}33;
                color: {s.text.primary};
            }}
            QListWidget::item:hover {{
                background-color: {s.background.hover};
            }}
        """)

    def _connect_signals(self) -> None:
        """Connect signal handlers."""
        self.new_btn.clicked.connect(self.new_conversation.emit)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.list_widget.customContextMenuRequested.connect(
            self._show_context_menu
        )

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """Handle item click."""
        filepath = item.data(Qt.ItemDataRole.UserRole)
        if filepath:
            self.current_filepath = filepath
            self.conversation_selected.emit(filepath)

    def _show_context_menu(self, position) -> None:
        """Show context menu for item."""
        item = self.list_widget.itemAt(position)
        if not item:
            return

        filepath = item.data(Qt.ItemDataRole.UserRole)
        if not filepath:
            return

        tm = ThemeManager.instance()
        c = tm.colors
        s = tm.semantic

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {s.background.elevated};
                color: {s.text.primary};
                border: 1px solid {s.border.default};
                border-radius: 6px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 16px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {s.background.selected};
            }}
        """)

        delete_action = QAction("🗑️ Delete", self)
        delete_action.triggered.connect(
            lambda: self.delete_conversation.emit(filepath)
        )
        menu.addAction(delete_action)

        menu.exec(self.list_widget.viewport().mapToGlobal(position))

    def load_conversations(self, limit: int = 20) -> None:
        """Load recent conversations into list asynchronously."""
        self.list_widget.clear()
        self.info_label.setText("Loading...")

        # Load in background thread
        self.loader = ConversationLoader(self.conversation_manager, limit)
        self.loader.loaded.connect(self._on_conversations_loaded)
        self.loader.start()

    def _on_conversations_loaded(self, convs: list) -> None:
        """Handle conversations loaded from background thread."""
        self.list_widget.clear()

        tm = ThemeManager.instance()
        c = tm.colors

        for conv in convs:
            # Format title
            title = conv.get("title", "Untitled")
            if len(title) > 35:
                title = title[:32] + "..."

            item = QListWidgetItem(f"💬 {title}")
            item.setData(Qt.ItemDataRole.UserRole, conv["filepath"])
            item.setFont(QFont("Segoe UI", 10))

            # Tooltip with details
            from datetime import datetime

            try:
                updated = datetime.fromisoformat(
                    conv["updated_at"].replace("Z", "+00:00")
                )
                date_str = updated.strftime("%b %d, %Y %H:%M")
            except (ValueError, KeyError):
                date_str = ""

            msg_count = conv.get("message_count", 0)
            item.setToolTip(f"{conv['title']}\n{date_str}\n{msg_count} messages")

            self.list_widget.addItem(item)

        # Update info label
        if convs:
            self.info_label.setText(f"{len(convs)} conversations")
        else:
            self.info_label.setText("No conversations yet")

    def refresh(self) -> None:
        """Refresh conversation list."""
        current = self.current_filepath
        self.load_conversations()

        # Re-select current item if still exists
        if current:
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                if item and item.data(Qt.ItemDataRole.UserRole) == current:
                    self.list_widget.setCurrentItem(item)
                    break

    def highlight_current(self, filepath: str) -> None:
        """Highlight current conversation."""
        self.current_filepath = filepath

        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item and item.data(Qt.ItemDataRole.UserRole) == filepath:
                self.list_widget.setCurrentItem(item)
                break
