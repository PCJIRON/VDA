"""Chat message bubble widget — user and AI message rendering with thinking toggle."""

import datetime
import logging

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class MessageBubble(QWidget):
    def __init__(self, text: str, sender: str, is_vision: bool = False, attachments: list = None, parent=None):
        super().__init__(parent)
        self.sender = sender
        self._thinking_visible = False
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(14, 6, 14, 6)
        self.layout.setSpacing(0)

        # Row: avatar + bubble
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

        # Avatar circle
        avatar = QLabel("\U0001F464" if sender == "user" else "")
        avatar.setFixedSize(28, 28)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if sender == "user":
            avatar.setStyleSheet(
                "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #9333ea, stop:1 #2563eb); "
                "color: white; border-radius: 14px; font-size: 14px; font-weight: bold;"
            )
        else:
            import os
            from PyQt6.QtGui import QPainter
            from PyQt6.QtSvg import QSvgRenderer
            svg_path = os.path.join(os.path.dirname(__file__), "..", "assets", "star.svg")
            renderer = QSvgRenderer(svg_path)
            pixmap = QPixmap(18, 18)
            pixmap.fill(Qt.GlobalColor.transparent)
            if renderer.isValid():
                painter = QPainter(pixmap)
                renderer.render(painter)
                painter.end()
                avatar.setPixmap(pixmap)
            else:
                avatar.setText("★")
                avatar.setStyleSheet("color: white; font-size: 14px;")
            
            avatar.setStyleSheet(
                "background: #0B0F19; border: 1px solid rgba(147, 51, 234, 0.4); border-radius: 14px;"
            )
        avatar.setMaximumSize(28, 28)

        self.frame = QFrame()
        self.frame.setMaximumWidth(340)
        self.frame_layout = QVBoxLayout(self.frame)
        self.frame_layout.setContentsMargins(12, 10, 12, 10)
        self.frame_layout.setSpacing(6)

        if sender == "user":
            self.frame.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #9333ea, stop:1 #2563eb);
                    color: white;
                    border-radius: 16px;
                }
            """)
        else:
            self.frame.setStyleSheet("""
                QFrame {
                    background-color: #151924;
                    color: #F8FAFC;
                    border: 1px solid #2A2F42;
                    border-radius: 16px;
                }
            """)

        if attachments:
            for att in attachments:
                if att.get('type') == 'file':
                    name = att.get('name', 'File')
                    chip = QLabel(f"\uE7C3 {name}")
                    chip.setStyleSheet(f"background: {'rgba(255,255,255,0.2)' if sender == 'user' else 'rgba(0,0,0,0.05)'}; color: {'white' if sender == 'user' else '#374151'}; padding: 6px; border-radius: 4px; font-family: 'Segoe Fluent Icons', 'Segoe UI'; font-size: 11px;")
                    self.frame_layout.addWidget(chip)

        self.msg_lbl = QLabel(text)
        self.msg_lbl.setWordWrap(True)
        self.msg_lbl.setStyleSheet("background: transparent; border: none;")
        self.frame_layout.addWidget(self.msg_lbl)

        if sender == "ai":
            self._thinking_toggle = QPushButton("\u2699 Thinking...")
            self._thinking_toggle.setStyleSheet("""
                QPushButton {
                    background: transparent; color: #94A3B8; border: 1px solid #2A2F42;
                    border-radius: 4px; padding: 2px 6px; font-size: 10px;
                    text-align: left;
                }
                QPushButton:hover { background: #1E293B; }
            """)
            self._thinking_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
            self._thinking_toggle.hide()
            self._thinking_toggle.clicked.connect(self._toggle_thinking)
            self.frame_layout.addWidget(self._thinking_toggle)

            self._thinking_content = QLabel("")
            self._thinking_content.setWordWrap(True)
            self._thinking_content.setStyleSheet("""
                background: #0B0F19; color: #94A3B8; border: none;
                border-left: 2px solid #2A2F42; padding: 4px 8px;
                font-size: 10px; font-family: monospace;
            """)
            self._thinking_content.setMaximumHeight(0)
            self.frame_layout.addWidget(self._thinking_content)

        if attachments:
            for att in attachments:
                img_url = att.get('image_url') or att.get('base64')
                if img_url or att.get('type') == 'image':
                    img_data = att.get('base64')
                    if img_url and type(img_url) == dict:
                        img_data = img_url.get('url', '').split('base64,')[-1]
                    if img_data:
                        try:
                            import base64
                            img_lbl = QLabel()
                            pixmap = QPixmap()
                            pixmap.loadFromData(base64.b64decode(img_data))
                            scaled = pixmap.scaledToWidth(240, Qt.TransformationMode.SmoothTransformation)
                            img_lbl.setPixmap(scaled)
                            img_lbl.setStyleSheet("border-radius: 6px; background: transparent;")
                            self.frame_layout.addWidget(img_lbl)
                        except Exception:
                            pass

        time_str = datetime.datetime.now().strftime("%I:%M %p")
        time_lbl = QLabel(time_str)
        time_lbl.setStyleSheet(f"font-size: 10px; background: transparent; border: none; color: {'rgba(255,255,255,0.7)' if sender=='user' else '#6b7280'};")

        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 0, 0, 0)
        footer_layout.addWidget(time_lbl)
        footer_layout.addStretch()

        self.copy_btn = QPushButton("Copy")
        self.copy_btn.setFixedSize(50, 18)
        self.copy_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {'rgba(255,255,255,0.8)' if sender == 'user' else '#2563eb'};
                border: none;
                font-size: 10px;
                font-weight: bold;
                text-align: right;
            }}
            QPushButton:hover {{ text-decoration: underline; }}
        """)
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.clicked.connect(self._copy_text)
        footer_layout.addWidget(self.copy_btn)

        self.frame_layout.addLayout(footer_layout)

        # Assemble: avatar + bubble (+ stretch) depending on sender
        if sender == "user":
            row.addStretch()
            row.addWidget(self.frame)
            row.addWidget(avatar)
        else:
            row.addWidget(avatar)
            row.addWidget(self.frame)
            row.addStretch()

        self.layout.addLayout(row)

    def _copy_text(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.msg_lbl.text())
        self.copy_btn.setText("Copied!")
        QTimer.singleShot(1500, lambda: self.copy_btn.setText("Copy"))

    def update_text(self, new_text: str):
        self.msg_lbl.setText(new_text)

    def set_thinking(self, text: str):
        try:
            if not text:
                self._thinking_toggle.hide()
                self._thinking_content.setText("")
                return
            self._thinking_content.setText(text)
            self._thinking_toggle.show()
            if self._thinking_visible:
                height = min(200, self._thinking_content.sizeHint().height())
                self._thinking_content.setMaximumHeight(height)
        except Exception as e:
            logger.error(f"[UI] set_thinking error: {e}", exc_info=True)

    def _toggle_thinking(self):
        try:
            self._thinking_visible = not self._thinking_visible
            if self._thinking_visible:
                height = min(200, self._thinking_content.sizeHint().height())
                self._thinking_content.setMaximumHeight(height)
                self._thinking_toggle.setText("\u25BC Thinking")
            else:
                self._thinking_content.setMaximumHeight(0)
                self._thinking_toggle.setText("\u2699 Thinking...")
        except Exception as e:
            logger.error(f"[UI] _toggle_thinking error: {e}", exc_info=True)
