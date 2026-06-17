from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class _SidebarButton(QPushButton):
    def __init__(self, text, icon="", parent=None):
        super().__init__(text, parent)
        self._icon = icon
        self._hovered = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(36)
        self.setStyleSheet(self._style(False))

    def _style(self, hover):
        bg = "#26262b" if hover else "transparent"
        return f"QPushButton {{ background: {bg}; border: none; border-radius: 12px; padding: 6px 10px; color: #a3a3a3; font-size: 13px; text-align: left; }} QPushButton:hover {{ background: #26262b; color: #e5e5e5; }}"

    def enterEvent(self, e):
        self._hovered = True
        self.setStyleSheet(self._style(True))
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._hovered = False
        self.setStyleSheet(self._style(False))
        super().leaveEvent(e)


class MessageBubbleWidget(QFrame):
    def __init__(self, content: str, is_user: bool, parent=None):
        super().__init__(parent)
        self._content = content
        self._is_user = is_user
        self.setFixedWidth(380)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self._msg_label = QLabel(content)
        self._msg_label.setWordWrap(True)
        self._msg_label.setStyleSheet(
            f"color: {'white' if is_user else '#e5e5e5'}; font-size: 14px; "
            f"background: {'#262626' if is_user else 'transparent'}; "
            f"padding: 10px 16px; border-radius: 16px; "
            f"border: {'none' if is_user else '1px solid rgba(64,64,64,0.6)'}; "
            f"{'border-top-right-radius: 4px' if is_user else 'border-top-left-radius: 4px'};"
        )

        if is_user:
            layout.addStretch()
            layout.addWidget(self._msg_label)
        else:
            layout.addWidget(self._msg_label)
            layout.addStretch()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._is_user:
            color = QColor("#2563eb")
            x = self.width() - 36
        else:
            color = QColor("#262626")
            x = 0

        path = QPainterPath()
        path.addEllipse(x, 4, 28, 28)
        p.fillPath(path, color)
        if not self._is_user:
            pen = p.pen()
            pen.setColor(QColor("#404040"))
            pen.setWidthF(1)
            p.setPen(pen)
            p.drawEllipse(x, 4, 28, 28)

        font = QFont("Segoe Fluent Icons, Segoe MDL2 Assets")
        font.setPixelSize(14)
        p.setFont(font)
        p.setPen(QColor("white"))
        icon = "\uE77B" if self._is_user else "\u2728"
        p.drawText(x, 4, 28, 28, Qt.AlignmentFlag.AlignCenter, icon)

        super().paintEvent(e)


class ChatPanel(QFrame):
    close_requested = pyqtSignal()
    new_chat_requested = pyqtSignal()

    WIDTH = 460
    WIDTH_WITH_SIDEBAR = 680
    HEIGHT = 500

    def __init__(self, parent=None):
        super().__init__(parent)
        self._sidebar_open = False
        self._messages: list[dict] = []

        self.setFixedSize(self.WIDTH, self.HEIGHT)
        self.setStyleSheet("""
            ChatPanel { background: #0f0f11; border: 1px solid rgba(64,64,64,0.5);
                         border-radius: 16px; }
        """)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self._sidebar = QFrame(self)
        self._sidebar.setFixedWidth(0)
        self._sidebar.setStyleSheet("background: #151518; border-right: 1px solid rgba(38,38,38,0.5);")
        sidebar_layout = QVBoxLayout(self._sidebar)
        sidebar_layout.setContentsMargins(8, 12, 8, 12)
        sidebar_layout.setSpacing(4)

        self._new_chat_btn = QPushButton("  +  New chat")
        self._new_chat_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._new_chat_btn.setFixedHeight(38)
        self._new_chat_btn.setStyleSheet(
            "QPushButton { background: transparent; border: 1px solid #404040; border-radius: 12px; "
            "color: #e5e5e5; font-size: 13px; padding: 6px; text-align: left; } "
            "QPushButton:hover { background: #26262b; }"
        )
        self._new_chat_btn.clicked.connect(self.new_chat_requested.emit)
        sidebar_layout.addWidget(self._new_chat_btn)

        self._history_label = QLabel("  History")
        self._history_label.setStyleSheet("color: #737373; font-size: 11px; font-weight: 600; padding: 8px 2px 4px;")
        sidebar_layout.addWidget(self._history_label)

        self._history_list = QVBoxLayout()
        sidebar_layout.addLayout(self._history_list)
        sidebar_layout.addStretch()

        main_layout.addWidget(self._sidebar)

        # Right: main chat area
        self._chat_area = QVBoxLayout()
        self._chat_area.setContentsMargins(0, 0, 0, 0)
        self._chat_area.setSpacing(0)

        # Header
        self._header = QFrame()
        self._header.setFixedHeight(48)
        self._header.setStyleSheet("background: rgba(15,15,17,0.8); border-bottom: 1px solid rgba(38,38,38,0.5);")
        header_layout = QHBoxLayout(self._header)
        header_layout.setContentsMargins(8, 0, 8, 0)

        self._toggle_sidebar_btn = QPushButton("\uE76C")
        self._toggle_sidebar_btn.setFixedSize(32, 32)
        self._toggle_sidebar_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_sidebar_btn.setStyleSheet(
            "QPushButton { background: transparent; border: none; border-radius: 8px; color: #a3a3a3; font-size: 18px; } "
            "QPushButton:hover { background: #26262b; color: white; }"
        )
        self._toggle_sidebar_btn.clicked.connect(self._toggle_sidebar)
        header_layout.addWidget(self._toggle_sidebar_btn)

        header_layout.addStretch()

        badge = QLabel("  VDA v3  ")
        badge.setStyleSheet("background: #26262b; border-radius: 6px; color: #a3a3a3; font-size: 10px; font-weight: 700; padding: 2px 4px;")
        header_layout.addWidget(badge)

        self._close_btn = QPushButton("\u2715")
        self._close_btn.setFixedSize(32, 32)
        self._close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._close_btn.setStyleSheet(
            "QPushButton { background: transparent; border: none; border-radius: 8px; color: #a3a3a3; font-size: 16px; } "
            "QPushButton:hover { background: #26262b; color: white; }"
        )
        self._close_btn.clicked.connect(self.close_requested.emit)
        header_layout.addWidget(self._close_btn)

        self._chat_area.addWidget(self._header)

        # Messages area
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet("QScrollArea { border: none; background: #0f0f11; } QScrollBar:vertical { width: 6px; } QScrollBar::handle:vertical { background: #404040; border-radius: 3px; }")
        self._scroll_content = QWidget()
        self._scroll_content.setStyleSheet("background: #0f0f11;")
        self._messages_layout = QVBoxLayout(self._scroll_content)
        self._messages_layout.setContentsMargins(16, 16, 16, 16)
        self._messages_layout.setSpacing(16)
        self._messages_layout.addStretch()
        self._scroll.setWidget(self._scroll_content)
        self._chat_area.addWidget(self._scroll)

        main_layout.addLayout(self._chat_area)

        self._show_empty_state()

    def _show_empty_state(self):
        self._clear_messages()
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        l = QVBoxLayout(w)
        l.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_lbl = QLabel("\u2728")
        icon_lbl.setStyleSheet("font-size: 28px; color: white;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(icon_lbl)

        t1 = QLabel("New Chat Session")
        t1.setStyleSheet("color: #d4d4d4; font-size: 16px; font-weight: 500;")
        t1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(t1)

        t2 = QLabel("Type in the floating bar to begin.")
        t2.setStyleSheet("color: #737373; font-size: 13px;")
        t2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(t2)

        self._messages_layout.insertWidget(0, w)

    def _clear_messages(self):
        while self._messages_layout.count() > 1:
            item = self._messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _toggle_sidebar(self):
        self._sidebar_open = not self._sidebar_open
        w = self.WIDTH_WITH_SIDEBAR if self._sidebar_open else self.WIDTH
        self._sidebar.setFixedWidth(220 if self._sidebar_open else 0)
        self.setFixedWidth(w)
        self._sidebar.setVisible(self._sidebar_open)
        self._toggle_sidebar_btn.setText("\uE76B" if self._sidebar_open else "\uE76C")

    def add_message(self, content: str, is_user: bool):
        self._clear_messages()
        bubble = MessageBubbleWidget(content, is_user)
        self._messages_layout.insertWidget(self._messages_layout.count() - 1, bubble)

    def _update_last_text(self, text: str):
        """Replace the last message bubble content (for streaming updates)."""
        last_idx = self._messages_layout.count() - 2
        if last_idx >= 0:
            item = self._messages_layout.itemAt(last_idx)
            if item and item.widget():
                existing = item.widget()._msg_label
                existing.setText(text)

    def set_history_items(self, items: list[str]):
        for item in self._history_list:
            w = self._history_list.takeAt(self._history_list.indexOf(item))
            if w and w.widget():
                w.widget().deleteLater()
        for title in items:
            btn = _SidebarButton(f"  \uE70B  {title}")
            self._history_list.addWidget(btn)
        self._history_list.addStretch()
