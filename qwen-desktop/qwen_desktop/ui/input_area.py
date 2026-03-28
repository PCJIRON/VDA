"""
Input area widget for composing and sending messages.

Port of qwen-code's InputPrompt.tsx / Composer.tsx.
Includes file attachment support, slash commands, and send button.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QToolButton,
    QLabel,
    QScrollArea,
    QFrame,
    QFileDialog,
    QListWidget,
    QListWidgetItem,
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QEvent, QObject
from PyQt6.QtGui import QKeyEvent, QDragEnterEvent, QDragLeaveEvent, QDropEvent, QFont
from pathlib import Path
from typing import Optional

from qwen_desktop.attachments.file_manager import Attachment
from qwen_desktop.config.settings import Settings
from qwen_desktop.ui.theme_manager import ThemeManager


class SlashCommandPopup(QListWidget):
    """Popup for slash command autocompletion."""

    command_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setMaximumHeight(200)
        self.setMinimumWidth(250)
        self.itemClicked.connect(self._on_item_clicked)
        self._apply_styles()

    def _apply_styles(self):
        """Apply theme styling."""
        tm = ThemeManager.instance()
        c = tm.colors
        s = tm.semantic

        self.setStyleSheet(f"""
            QListWidget {{
                background-color: {s.background.elevated};
                border: 1px solid {s.border.default};
                border-radius: 8px;
                color: {s.text.primary};
                font-size: 12px;
                padding: 4px;
            }}
            QListWidget::item {{
                padding: 6px 12px;
                border-radius: 4px;
            }}
            QListWidget::item:selected {{
                background-color: {s.background.selected};
            }}
            QListWidget::item:hover {{
                background-color: {s.background.hover};
            }}
        """)

    def _on_item_clicked(self, item: QListWidgetItem):
        """Handle command selection."""
        cmd = item.data(Qt.ItemDataRole.UserRole)
        if cmd:
            self.command_selected.emit(cmd)
        self.hide()

    def show_commands(self, commands: list, pos):
        """Show command suggestions.

        Args:
            commands: List of (name, description) tuples.
            pos: Position to show at.
        """
        self.clear()
        tm = ThemeManager.instance()
        c = tm.colors

        for name, description in commands:
            item = QListWidgetItem(f"/{name}  —  {description}")
            item.setData(Qt.ItemDataRole.UserRole, f"/{name}")
            self.addItem(item)

        if self.count() > 0:
            self.setFixedHeight(min(self.count() * 32 + 8, 200))
            self.move(pos)
            self.show()
        else:
            self.hide()


class InputArea(QWidget):
    """Input area for composing messages."""

    message_sent = pyqtSignal(str)
    attachments_changed = pyqtSignal(list)

    def __init__(self, settings: Optional[Settings] = None, parent: None = None) -> None:
        """Initialize the input area.

        Args:
            settings: Application settings.
            parent: Parent widget.
        """
        super().__init__(parent)

        self.settings = settings
        self.attachments: list[Attachment] = []

        self._setup_ui()
        self._apply_styles()
        self._connect_signals()

        # Slash command popup
        self.command_popup = SlashCommandPopup(self)
        self.command_popup.command_selected.connect(self._on_command_selected)
        self.command_popup.hide()

        # Install event filter for Enter key handling
        self.text_input.installEventFilter(self)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """Handle Enter key to send messages.

        Args:
            obj: Object receiving event.
            event: The event.

        Returns:
            True if event handled, False otherwise.
        """
        if event.type() == QEvent.Type.KeyPress:
            key_event = event  # type: ignore
            if key_event.key() == Qt.Key.Key_Return:
                # Shift+Enter for new line, Enter alone to send
                if not key_event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    self._on_send()
                    return True
            elif key_event.key() == Qt.Key.Key_Escape:
                if self.command_popup.isVisible():
                    self.command_popup.hide()
                    return True
            elif key_event.key() == Qt.Key.Key_Tab:
                if self.command_popup.isVisible():
                    # Select first command
                    if self.command_popup.count() > 0:
                        item = self.command_popup.item(0)
                        cmd = item.data(Qt.ItemDataRole.UserRole)
                        if cmd:
                            self._on_command_selected(cmd)
                    return True
        return super().eventFilter(obj, event)

    def _setup_ui(self) -> None:
        """Set up the UI components."""
        tm = ThemeManager.instance()
        c = tm.colors
        s = tm.semantic

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 12)
        layout.setSpacing(6)

        # Enable drag and drop
        self.setAcceptDrops(True)

        # Attachments preview area
        self.attachments_area = QScrollArea()
        self.attachments_area.setWidgetResizable(True)
        self.attachments_area.setMaximumHeight(80)
        self.attachments_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.attachments_area.setVisible(False)

        self.attachments_container = QWidget()
        self.attachments_layout = QHBoxLayout(self.attachments_container)
        self.attachments_layout.setContentsMargins(4, 4, 4, 4)
        self.attachments_layout.setSpacing(6)
        self.attachments_layout.addStretch()

        self.attachments_area.setWidget(self.attachments_container)
        layout.addWidget(self.attachments_area)

        # Input row in a styled container
        input_frame = QFrame()
        input_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {s.background.input};
                border: 1px solid {s.border.default};
                border-radius: 12px;
            }}
            QFrame:focus-within {{
                border: 1px solid {s.border.focus};
            }}
        """)

        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(8, 4, 8, 4)
        input_layout.setSpacing(8)

        # Attach button
        self.attach_btn = QToolButton()
        self.attach_btn.setText("📎")
        self.attach_btn.setToolTip("Attach files (or drag & drop)")
        self.attach_btn.setFixedSize(36, 36)
        self.attach_btn.setStyleSheet(f"""
            QToolButton {{
                background-color: transparent;
                border: none;
                border-radius: 6px;
                font-size: 18px;
            }}
            QToolButton:hover {{
                background-color: {s.background.hover};
            }}
        """)
        input_layout.addWidget(self.attach_btn)

        # Text input
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText(
            "  Type your message or @path/to/file"
        )
        self.text_input.setMaximumHeight(120)
        self.text_input.setMinimumHeight(36)
        self.text_input.setFont(QFont("Segoe UI", 12))
        self.text_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: transparent;
                color: {s.text.primary};
                border: none;
                padding: 6px 4px;
                font-size: 13px;
            }}
        """)
        input_layout.addWidget(self.text_input, 1)

        # Send button
        self.send_btn = QPushButton("➤")
        self.send_btn.setToolTip("Send message (Enter)")
        self.send_btn.setFixedSize(36, 36)
        self.send_btn.setFont(QFont("Segoe UI", 14))
        self.send_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c.AccentBlue};
                color: white;
                border: none;
                border-radius: 18px;
                font-size: 16px;
            }}
            QPushButton:hover {{
                background-color: {c.LightBlue};
            }}
            QPushButton:disabled {{
                background-color: {c.Gray};
                color: {c.Comment};
            }}
        """)
        input_layout.addWidget(self.send_btn)

        layout.addWidget(input_frame)

    def _apply_styles(self) -> None:
        """Apply styles to the widget."""
        tm = ThemeManager.instance()
        s = tm.semantic

        self.setStyleSheet(f"""
            InputArea {{
                background-color: {s.background.primary};
                border-top: 1px solid {s.border.subtle};
            }}
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
        """)

    def _connect_signals(self) -> None:
        """Connect signal handlers."""
        self.send_btn.clicked.connect(self._on_send)
        self.attach_btn.clicked.connect(self._on_attach)
        self.text_input.textChanged.connect(self._on_text_changed)

    def _on_send(self) -> None:
        """Handle send button click."""
        text = self.text_input.toPlainText().strip()
        if text:
            self.message_sent.emit(text)
            self.text_input.clear()
            self.command_popup.hide()

    def _on_attach(self) -> None:
        """Handle attach button click."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Files",
            "",
            "All Files (*)",
        )

        if files:
            for file_path in files:
                self.add_attachment(file_path)

    def _on_text_changed(self) -> None:
        """Handle text change - check for slash commands."""
        text = self.text_input.toPlainText().strip()

        # Enable/disable send button
        has_text = bool(text)
        self.send_btn.setEnabled(has_text)

        # Check for slash command input
        if text.startswith("/") and "\n" not in text:
            prefix = text[1:].lower()
            self._show_command_suggestions(prefix)
        else:
            self.command_popup.hide()

    def _show_command_suggestions(self, prefix: str) -> None:
        """Show slash command suggestions.

        Args:
            prefix: Command prefix to filter.
        """
        from qwen_desktop.core.command_registry import CommandRegistry

        registry = CommandRegistry()
        commands = registry.get_all_commands()

        # Filter commands
        filtered = []
        for cmd in commands:
            if cmd.name.startswith(prefix) or any(
                a.startswith(prefix) for a in cmd.aliases
            ):
                filtered.append((cmd.name, cmd.description))

        if filtered and prefix:
            # Position popup above input
            pos = self.text_input.mapToGlobal(self.text_input.rect().topLeft())
            pos.setY(pos.y() - min(len(filtered) * 32 + 8, 200) - 4)
            self.command_popup.show_commands(filtered, pos)
        else:
            self.command_popup.hide()

    def _on_command_selected(self, command: str) -> None:
        """Handle command selection from popup.

        Args:
            command: Selected command text.
        """
        self.text_input.setPlainText(command + " ")

        # Move cursor to end
        cursor = self.text_input.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.text_input.setTextCursor(cursor)

        self.command_popup.hide()

    def add_attachment(self, file_path: str) -> None:
        """Add a file attachment.

        Args:
            file_path: Path to the file.
        """
        attachment = Attachment(file_path)
        self.attachments.append(attachment)
        self._update_attachments_display()
        self.attachments_changed.emit(self.attachments)

    def remove_attachment(self, index: int) -> None:
        """Remove an attachment by index.

        Args:
            index: Index of attachment to remove.
        """
        if 0 <= index < len(self.attachments):
            self.attachments.pop(index)
            self._update_attachments_display()
            self.attachments_changed.emit(self.attachments)

    def clear_attachments(self) -> None:
        """Clear all attachments."""
        self.attachments.clear()
        self._update_attachments_display()
        self.attachments_changed.emit(self.attachments)

    def _update_attachments_display(self) -> None:
        """Update the attachments preview display."""
        tm = ThemeManager.instance()
        c = tm.colors
        s = tm.semantic

        # Clear existing widgets
        while self.attachments_layout.count() > 1:
            item = self.attachments_layout.itemAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        # Show/hide attachments area
        self.attachments_area.setVisible(len(self.attachments) > 0)

        # Add attachment chips
        for i, attachment in enumerate(self.attachments):
            chip = QFrame()
            chip.setFrameShape(QFrame.Shape.StyledPanel)
            chip.setStyleSheet(f"""
                QFrame {{
                    background-color: {c.AccentBlue}33;
                    border: 1px solid {c.AccentBlue}55;
                    border-radius: 6px;
                }}
                QLabel {{
                    color: {c.Foreground};
                    font-size: 11px;
                    background: transparent;
                    border: none;
                }}
            """)

            chip_layout = QHBoxLayout(chip)
            chip_layout.setContentsMargins(8, 4, 8, 4)
            chip_layout.setSpacing(6)

            # File icon
            icon = "📄"
            if attachment.is_code_file:
                icon = "💻"
            elif attachment.is_image:
                icon = "🖼️"
            elif attachment.is_config_file:
                icon = "⚙️"

            icon_label = QLabel(icon)
            chip_layout.addWidget(icon_label)

            # File name
            name_label = QLabel(attachment.name)
            name_label.setFont(QFont("Segoe UI", 10))
            chip_layout.addWidget(name_label)

            # Size
            size_label = QLabel(f"({attachment.size_formatted})")
            size_label.setStyleSheet(f"color: {c.Comment}; border: none;")
            size_label.setFont(QFont("Segoe UI", 9))
            chip_layout.addWidget(size_label)

            # Remove button
            remove_btn = QToolButton()
            remove_btn.setText("✕")
            remove_btn.setFixedSize(18, 18)
            remove_btn.setStyleSheet(f"""
                QToolButton {{
                    background: transparent;
                    border: none;
                    color: {c.Comment};
                    font-size: 12px;
                    border-radius: 9px;
                }}
                QToolButton:hover {{
                    background-color: {c.AccentRed}33;
                    color: {c.AccentRed};
                }}
            """)
            remove_btn.clicked.connect(lambda checked, idx=i: self.remove_attachment(idx))
            chip_layout.addWidget(remove_btn)

            self.attachments_layout.addWidget(chip)

    def get_message(self) -> str:
        """Get the current message text.

        Returns:
            Message text.
        """
        return self.text_input.toPlainText().strip()

    # Drag-and-drop event handlers
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            has_valid_file = False
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path and Path(file_path).is_file():
                    has_valid_file = True
                    break

            if has_valid_file:
                event.acceptProposedAction()
                tm = ThemeManager.instance()
                c = tm.colors
                self.attachments_area.setVisible(True)
                self.attachments_area.setStyleSheet(f"""
                    QScrollArea {{
                        border: 2px dashed {c.AccentBlue};
                        border-radius: 8px;
                        background-color: {c.AccentBlue}11;
                    }}
                """)
        else:
            super().dragEnterEvent(event)

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        """Handle drag leave event."""
        if not self.attachments:
            self.attachments_area.setVisible(False)
        self.attachments_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        """Handle drop event."""
        self.attachments_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path:
                from qwen_desktop.attachments.file_manager import FileManager

                manager = FileManager(
                    max_file_size_mb=self.settings.get("max_file_size_mb", 10)
                    if self.settings
                    else 10,
                    allowed_extensions=set(),
                )
                is_valid, error = manager.validate_file(file_path)
                if is_valid:
                    self.add_attachment(file_path)
