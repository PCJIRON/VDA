"""Chat history popup — clean conversation view (ChatGPT/Claude style).

- Session list hidden by default — accessed via ☰ toggle
- Chat bubbles use sender colors and avatars
- No thinking panel — clean chat-only view
- Friendly empty-state copy
"""

import logging

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from qwen_desktop.ui.assistant.message_bubble import MessageBubble

logger = logging.getLogger(__name__)


class ChatHistoryPopup(QWidget):
    def __init__(self, thinking_panel=None, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.SubWindow | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(600, 500)
        self._last_ai_bubble = None
        # thinking_panel parameter kept for backward compat but no longer embedded
        self._sessions_visible = False

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(10, 10, 10, 10)

        self.container = QFrame()
        self.container.setObjectName("HistoryContainer")
        self.container.setStyleSheet("""
            #HistoryContainer {
                background-color: #0B0F19;
                border-radius: 16px;
                border: 1px solid #2A2F42;
            }
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 70))
        shadow.setOffset(0, 8)
        self.container.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # === HEADER ===
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: #151924;
                border-bottom: 1px solid #2A2F42;
                border-top-left-radius: 16px;
                border-top-right-radius: 16px;
            }
        """)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(14, 10, 14, 10)
        h_layout.setSpacing(8)

        # Sessions toggle button (☰) — hidden by default, opens sidebar
        self.sessions_btn = QPushButton("\u2630")
        self.sessions_btn.setFixedSize(28, 28)
        self.sessions_btn.setToolTip("Show chat history")
        self.sessions_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: white; border: none;
                font-size: 18px; font-weight: bold;
            }
            QPushButton:hover { background: rgba(255,255,255,0.2); border-radius: 6px; }
        """)
        self.sessions_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.sessions_btn.clicked.connect(self._toggle_sessions)
        h_layout.addWidget(self.sessions_btn)

        title = QLabel("VDA")
        title.setStyleSheet("color: white; font-weight: bold; font-size: 15px; background: transparent;")
        h_layout.addWidget(title)

        self.vision_status_lbl = QLabel("")
        self.vision_status_lbl.setStyleSheet(
            "color: #86efac; font-size: 11px; font-weight: bold; "
            "background: rgba(0,0,0,0.25); border-radius: 6px; padding: 2px 8px;"
        )
        self.vision_status_lbl.hide()
        h_layout.addWidget(self.vision_status_lbl)

        self.thinking_status_lbl = QLabel("")
        self.thinking_status_lbl.setStyleSheet(
            "color: #fde68a; font-size: 11px; font-weight: bold; "
            "background: rgba(0,0,0,0.25); border-radius: 6px; padding: 2px 8px;"
        )
        self.thinking_status_lbl.hide()
        h_layout.addWidget(self.thinking_status_lbl)

        h_layout.addStretch()

        self.close_btn = QPushButton("\u2715")
        self.close_btn.setFixedSize(28, 28)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: white; border: none; font-size: 16px; font-weight: bold;
            }
            QPushButton:hover { background: rgba(255,255,255,0.25); border-radius: 6px; }
        """)
        h_layout.addWidget(self.close_btn)

        layout.addWidget(header)

        # === CONTENT ===
        content_w = QWidget()
        content_w.setStyleSheet("background: transparent;")
        
        # Sidebar for sessions
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(220)
        self.sidebar.setStyleSheet("""
            QFrame {
                background-color: #151924;
                border-right: 1px solid #2A2F42;
                border-bottom-left-radius: 16px;
            }
        """)
        c_layout = QHBoxLayout(content_w)
        c_layout.setContentsMargins(0, 0, 0, 0)
        c_layout.setSpacing(0)

        # --- Session list (HIDDEN by default) ---
        self.session_scroll = QScrollArea()
        self.session_scroll.setFixedWidth(220)
        self.session_scroll.setWidgetResizable(True)
        self.session_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scroll_style = """
            QScrollArea {
                border: none;
                background: #151924;
            }
            QScrollBar:vertical { border: none; background: transparent; width: 6px; margin: 0px; }
            QScrollBar::handle:vertical { background: #334155; min-height: 30px; border-radius: 3px; }
            QScrollBar::handle:vertical:hover { background: #475569; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
        """
        self.session_scroll.setStyleSheet(scroll_style)

        self.session_list_w = QWidget()
        self.session_list_w.setStyleSheet("background: transparent;")
        self.session_layout = QVBoxLayout(self.session_list_w)
        self.session_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.session_layout.setContentsMargins(8, 10, 8, 10)
        self.session_layout.setSpacing(4)

        # Session list header
        session_header = QLabel("Recent chats")
        session_header.setStyleSheet(
            "color: #64748B; font-size: 11px; font-weight: bold; "
            "padding: 4px 8px 8px 8px; background: transparent;"
        )
        self.session_layout.addWidget(session_header)

        self.session_scroll.setWidget(self.session_list_w)
        self.session_scroll.hide()  # HIDDEN BY DEFAULT
        c_layout.addWidget(self.session_scroll)

        # --- Right panel: chat messages + thinking + staging ---
        right_panel_w = QWidget()
        right_panel_w.setStyleSheet("background: transparent;")
        rp_layout = QVBoxLayout(right_panel_w)
        rp_layout.setContentsMargins(0, 0, 0, 0)
        rp_layout.setSpacing(0)

        # Chat messages scroll area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        msg_scroll_style = """
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { border: none; background: transparent; width: 6px; margin: 0px; }
            QScrollBar::handle:vertical { background: #334155; min-height: 30px; border-radius: 3px; }
            QScrollBar::handle:vertical:hover { background: #475569; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
        """
        self.scroll.setStyleSheet(msg_scroll_style)

        self.messages_w = QWidget()
        self.messages_w.setStyleSheet("background: transparent;")
        self.msg_layout = QVBoxLayout(self.messages_w)
        self.msg_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.msg_layout.setContentsMargins(0, 8, 0, 8)
        self.msg_layout.setSpacing(8)

        self.scroll.setWidget(self.messages_w)
        rp_layout.addWidget(self.scroll, 1)

        # Staging area for attachments
        self.staging_scroll = QScrollArea()
        self.staging_scroll.setFixedHeight(95)
        self.staging_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.staging_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                border-top: 1px solid #2A2F42;
                background: #0B0F19;
            }
            QScrollBar {height:0px;}
        """)

        self.staging_w = QWidget()
        self.staging_w.setStyleSheet("background: transparent;")
        self.staging_layout = QHBoxLayout(self.staging_w)
        self.staging_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.staging_layout.setContentsMargins(10, 10, 10, 10)
        self.staging_layout.setSpacing(10)

        self.staging_scroll.setWidgetResizable(True)
        self.staging_scroll.setWidget(self.staging_w)
        self.staging_scroll.hide()

        rp_layout.addWidget(self.staging_scroll)

        c_layout.addWidget(right_panel_w, 1)

        layout.addWidget(content_w)

        outer_layout.addWidget(self.container)

    def _toggle_sessions(self):
        """Show/hide the session list sidebar."""
        self._sessions_visible = not self._sessions_visible
        if self._sessions_visible:
            self.session_scroll.show()
            self.sessions_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(255,255,255,0.1); color: white; border: none;
                    font-size: 18px; font-weight: bold; border-radius: 6px;
                }
                QPushButton:hover { background: rgba(255,255,255,0.2); }
            """)
        else:
            self.session_scroll.hide()
            self.sessions_btn.setStyleSheet("""
                QPushButton {
                    background: transparent; color: white; border: none;
                    font-size: 18px; font-weight: bold;
                }
                QPushButton:hover { background: rgba(255,255,255,0.1); border-radius: 6px; }
            """)

    def populate_sessions(self, sessions, click_callback):
        """Replace the session list with the given sessions."""
        # Clear existing items except the header
        while self.session_layout.count() > 1:
            item = self.session_layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()

        if not sessions:
            empty = QLabel("No previous chats")
            empty.setStyleSheet(
                "color: #475569; font-size: 11px; font-style: italic; "
                "padding: 12px 8px; background: transparent;"
            )
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.session_layout.addWidget(empty)
            self.session_layout.addStretch()
            return

        for s in sessions:
            title = s['title']
            preview = s.get('last_msg', '')
            preview = preview[:30] + ('\u2026' if len(preview) > 30 else '')
            btn = QPushButton(f"{title}\n{preview}")
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent; color: #94A3B8; text-align: left; padding: 10px; border-radius: 8px; border: 1px solid transparent;
                }
                QPushButton:hover {
                    background: #1E293B; border: 1px solid #2A2F42; color: #F8FAFC;
                }
            """)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, u=s['id']: click_callback(u))
            self.session_layout.addWidget(btn)
        self.session_layout.addStretch()

    def clear_chat(self):
        while self.msg_layout.count():
            item = self.msg_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._last_ai_bubble = None

    def add_message(self, text, sender, attachments=None):
        bubble = MessageBubble(text, sender, attachments=attachments)
        if sender == "ai":
            self._last_ai_bubble = bubble
        self.msg_layout.addWidget(bubble)
        self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum())
        QTimer.singleShot(50, self.scroll_to_bottom)

    def update_last_message(self, text):
        if self._last_ai_bubble:
            # Hide "(no result)" placeholder — show friendly default
            if text.strip() in ("(no result)", "", "..."):
                text = "I'm working on it\u2026"
            self._last_ai_bubble.update_text(text)
            self.scroll_to_bottom()

    def set_thinking_status(self, text: str):
        """Show a small 'Thinking...' indicator in the header while the agent works."""
        if text:
            self.thinking_status_lbl.setText(f"{text}")
            self.thinking_status_lbl.show()
        else:
            self.thinking_status_lbl.hide()

    def update_thinking(self, thinking_text):
        try:
            if self._last_ai_bubble:
                self._last_ai_bubble.set_thinking(thinking_text)
        except Exception as e:
            logger.error(f"[UI] update_thinking error: {e}", exc_info=True)

    def scroll_to_bottom(self):
        bar = self.scroll.verticalScrollBar()
        bar.setValue(bar.maximum())

    def set_vision_status(self, status: str):
        if status:
            self.vision_status_lbl.setText(status)
            self.vision_status_lbl.show()
        else:
            self.vision_status_lbl.hide()
