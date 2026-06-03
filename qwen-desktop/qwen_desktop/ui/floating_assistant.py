from PyQt6.QtWidgets import (
    QWidget, QLineEdit, QHBoxLayout, QPushButton, QLabel, QVBoxLayout, QScrollArea,
    QApplication, QGraphicsDropShadowEffect, QFrame, QMenu, QFileDialog, QSizePolicy,
    QTextEdit
)
from PyQt6.QtCore import (
    Qt, QPropertyAnimation, QRect, QPoint, QEasingCurve, pyqtSignal,
    QTimer, QEvent, QThread, QVariantAnimation
)
from PyQt6.QtGui import (
    QColor, QPainter, QLinearGradient, QBrush, QCursor, QAction, QFont, QPalette, QPixmap
)
from typing import List, Tuple, Optional
import datetime
import asyncio
import logging
import re
import cv2
import numpy as np
from qwen_desktop.core.session_service import SessionService
from qwen_desktop.core.vision_capture import VisionCaptureService
from qwen_desktop.core.pyautogui_executor import PyAutoGUIExecutor
from qwen_desktop.auth.provider_config import ProviderConfig
from qwen_desktop.core.api_client import APIClient
from qwen_desktop.core.zen_client import ZenClient
import uuid

try:
    import uiautomation as auto
    UI_AUTOMATION_AVAILABLE = True
    logging.info("[UIA] UI Automation loaded successfully")
except ImportError:
    UI_AUTOMATION_AVAILABLE = False
    logging.warning("[UIA] UI Automation not available (Windows only)")

from qwen_desktop.ui.components.vision_button import VisionButton
from qwen_desktop.ui.components.attach_button import AttachButton
from qwen_desktop.ui.components.send_button import SendButton
from qwen_desktop.ui.components.settings_button import SettingsButton
from qwen_desktop.ui.components.uied_button import UIEDButton, UIEDResultsPanel
from qwen_desktop.ui.uied_overlay import UIEDOverlayWidget
from qwen_desktop.ui.settings_dialog import SettingsDialog

logger = logging.getLogger(__name__)


class APIServerWorker(QThread):
    chunk_received = pyqtSignal(str)
    finished_response = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, api_client, message, history, vision_mode=False):
        super().__init__()
        self.api_client = api_client
        self.message = message
        self.history = list(history)
        self.vision_mode = vision_mode
        self._full_response = ""

    def run(self):
        try:
            asyncio.run(self._stream())
        except Exception as e:
            self.error_occurred.emit(str(e))

    async def _stream(self):
        try:
            async for chunk in self.api_client.send_message(
                self.message, self.history, vision_mode=self.vision_mode
            ):
                self._full_response += chunk
                self.chunk_received.emit(self._full_response)
            self.finished_response.emit(self._full_response)
        except Exception as e:
            self.error_occurred.emit(str(e))


class MessageBubble(QWidget):
    def __init__(self, text: str, sender: str, is_vision: bool = False, attachments: list = None, parent=None):
        super().__init__(parent)
        self.sender = sender
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 12, 16, 12)

        self.frame = QFrame()
        self.frame.setMaximumWidth(280)
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
                    background-color: white;
                    color: #1f2937;
                    border: 1px solid #e5e7eb;
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
        self.frame_layout.addWidget(time_lbl)

        outer_layout = QHBoxLayout()
        outer_layout.setContentsMargins(0, 0, 0, 0)
        if sender == "user":
            outer_layout.addStretch()
            outer_layout.addWidget(self.frame)
        else:
            outer_layout.addWidget(self.frame)
            outer_layout.addStretch()

        self.layout.addLayout(outer_layout)

    def update_text(self, new_text: str):
        self.msg_lbl.setText(new_text)


class ChatHistoryPopup(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(600, 450)
        self._last_ai_bubble = None

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(10, 10, 10, 10)

        self.container = QFrame()
        self.container.setObjectName("HistoryContainer")

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 70))
        shadow.setOffset(0, 8)
        self.container.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #9333ea, stop:1 #2563eb);
                border-top-left-radius: 16px;
                border-top-right-radius: 16px;
            }
        """)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 12, 16, 12)

        title = QLabel("Conversation")
        title.setStyleSheet("color: white; font-weight: bold; background: transparent;")
        h_layout.addWidget(title)

        self.vision_status_lbl = QLabel("")
        self.vision_status_lbl.setStyleSheet(
            "color: #86efac; font-size: 11px; font-weight: bold; "
            "background: rgba(0,0,0,0.25); border-radius: 6px; padding: 2px 8px;"
        )
        self.vision_status_lbl.hide()
        h_layout.addWidget(self.vision_status_lbl)

        self.close_btn = QPushButton("\u2715")
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: white; border: none; font-weight: bold;
            }
            QPushButton:hover { background: rgba(255,255,255,0.2); border-radius: 4px; }
        """)
        h_layout.addStretch()
        h_layout.addWidget(self.close_btn)

        layout.addWidget(header)

        content_w = QWidget()
        content_w.setStyleSheet("background-color: #ffffff; border-bottom-left-radius: 16px; border-bottom-right-radius: 16px;")
        c_layout = QHBoxLayout(content_w)
        c_layout.setContentsMargins(0, 0, 0, 0)
        c_layout.setSpacing(0)

        self.session_scroll = QScrollArea()
        self.session_scroll.setFixedWidth(200)
        self.session_scroll.setWidgetResizable(True)
        self.session_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scroll_style = """
            QScrollArea { border: none; border-right: 1px solid #e5e7eb; background: transparent; }
            QScrollBar:vertical { border: none; background: transparent; width: 6px; margin: 0px; }
            QScrollBar::handle:vertical { background: #d1d5db; min-height: 30px; border-radius: 3px; }
            QScrollBar::handle:vertical:hover { background: #9ca3af; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
        """
        self.session_scroll.setStyleSheet(scroll_style)

        self.session_list_w = QWidget()
        self.session_list_w.setStyleSheet("background: transparent;")
        self.session_layout = QVBoxLayout(self.session_list_w)
        self.session_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.session_layout.setContentsMargins(6, 6, 6, 6)
        self.session_layout.setSpacing(4)

        self.session_scroll.setWidget(self.session_list_w)
        c_layout.addWidget(self.session_scroll)

        right_panel_w = QWidget()
        right_panel_w.setStyleSheet("background: transparent;")
        rp_layout = QVBoxLayout(right_panel_w)
        rp_layout.setContentsMargins(0, 0, 0, 0)
        rp_layout.setSpacing(0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        msg_scroll_style = """
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { border: none; background: transparent; width: 6px; margin: 0px; }
            QScrollBar::handle:vertical { background: #d1d5db; min-height: 30px; border-radius: 3px; }
            QScrollBar::handle:vertical:hover { background: #9ca3af; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
        """
        self.scroll.setStyleSheet(msg_scroll_style)

        self.messages_w = QWidget()
        self.messages_w.setStyleSheet("background: transparent;")
        self.msg_layout = QVBoxLayout(self.messages_w)
        self.msg_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll.setWidget(self.messages_w)
        rp_layout.addWidget(self.scroll)

        self.staging_scroll = QScrollArea()
        self.staging_scroll.setFixedHeight(95)
        self.staging_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.staging_scroll.setStyleSheet("QScrollArea { border: none; border-top: 1px solid #e5e7eb; background: #f9fafb; border-bottom-right-radius: 16px; } QScrollBar {height:0px;}")

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

        c_layout.addWidget(right_panel_w)

        layout.addWidget(content_w)

        outer_layout.addWidget(self.container)

    def populate_sessions(self, sessions, click_callback):
        while self.session_layout.count():
            item = self.session_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for s in sessions:
            title = s['title']
            preview = s.get('last_msg', '')
            btn = QPushButton(f"{title}\n{preview}")
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent; color: #4b5563; text-align: center; padding: 10px;
                    border-radius: 6px; font-size: 11px; font-weight: 500;
                }
                QPushButton:hover { background-color: #e5e7eb; color: #1f2937; }
            """)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, u=s['id']: click_callback(u))
            self.session_layout.addWidget(btn)

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
            self._last_ai_bubble.update_text(text)
            self.scroll_to_bottom()

    def scroll_to_bottom(self):
        bar = self.scroll.verticalScrollBar()
        bar.setValue(bar.maximum())

    def set_vision_status(self, status: str):
        if status:
            self.vision_status_lbl.setText(status)
            self.vision_status_lbl.show()
        else:
            self.vision_status_lbl.hide()


class FloatingAssistant(QWidget):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self._config = ProviderConfig(settings)

        self.is_hovered = False
        self.is_expanded = False
        self.is_dragging = False
        self.is_vision_enabled = False

        self._pyautogui_mode = PyAutoGUIExecutor.ASK_FIRST
        self._last_vision_w = 1920
        self._last_vision_h = 1080

        self.drag_position = QPoint()
        self._press_position = QPoint()

        self.collapsed_size = 70
        self.expanded_size = 450

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(self.collapsed_size, self.collapsed_size)

        screen = QApplication.primaryScreen().availableGeometry()
        self.move(
            int(screen.width() - self.collapsed_size - 40),
            int(screen.height() - self.collapsed_size - 40),
        )

        self.history_popup = ChatHistoryPopup()
        self.history_popup.close_btn.clicked.connect(self.toggle_expand)

        self._setup_ui()
        self._setup_context_menu()
        self._init_api()

        self.session_service = SessionService(self.settings.get("cwd", ""))
        self.session_id = str(uuid.uuid4())
        self._chat_history = []
        self.last_msg_uuid = None
        self.messages_count = 0
        self.staged_files = []

        self._vision_service = None

        self._pyautogui_executor = PyAutoGUIExecutor(mode=self._pyautogui_mode)

        self._template_cache = {}
        self._template_threshold = 0.8

        self._use_ui_automation = UI_AUTOMATION_AVAILABLE

        self._uied_overlay = None
        self._uied_components = []
        self._is_uied_detecting = False

        self.load_session_clicked = lambda u: self._switch_to_session(u)
        self.history_popup.populate_sessions(
            self.session_service.get_all_sessions(), self.load_session_clicked
        )

        QApplication.instance().installEventFilter(self)

    def _find_with_ui_automation(self, target_name: str) -> Optional[Tuple[int, int, str]]:
        if not self._use_ui_automation:
            return None
        try:
            target = target_name.lower().replace('_', ' ').strip()
            try:
                taskbar = auto.WindowControl(ClassName='Shell_TrayWnd')
                if not taskbar.Exists(maxSearchSeconds=0.1):
                    return None
                for btn in taskbar.GetChildren():
                    try:
                        name = (btn.Name or '').lower()
                        if target in name or name in target:
                            rect = btn.BoundingRectangle
                            cx = (rect.left + rect.right) // 2
                            cy = (rect.top + rect.bottom) // 2
                            logger.info(f"[UIA] Taskbar: '{name}' at ({cx}, {cy})")
                            return (cx, cy, name)
                    except:
                        continue
            except Exception:
                pass
            try:
                active = auto.GetForegroundControl()
                if active:
                    name = (active.Name or '').lower()
                    if target in name or name in target:
                        rect = active.BoundingRectangle
                        cx = (rect.left + rect.right) // 2
                        cy = (rect.top + rect.bottom) // 2
                        logger.info(f"[UIA] Active: '{name}' at ({cx}, {cy})")
                        return (cx, cy, name)
            except:
                pass
            return None
        except Exception:
            return None

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonPress:
            click_pos = event.globalPosition().toPoint()
            if self.is_expanded:
                bar_contains = self.geometry().contains(click_pos)
                popup_contains = self.history_popup.isVisible() and self.history_popup.geometry().contains(click_pos)
                if not bar_contains and not popup_contains:
                    self.toggle_expand()
                    return False
        return super().eventFilter(obj, event)

    def _setup_ui(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.input_wrapper = QWidget()
        self.input_layout = QHBoxLayout(self.input_wrapper)
        self.input_layout.setContentsMargins(15, 0, 10, 0)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask AI...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
            }
        """)
        self.input_field.returnPressed.connect(self.submit_message)

        self.send_btn = SendButton()
        self.send_btn.clicked.connect(self.submit_message)
        self._is_sending = False

        self.vision_btn = VisionButton()
        self.vision_btn.clicked.connect(self.toggle_vision)

        self.attach_btn = AttachButton()
        self.attach_btn.clicked.connect(self.select_files)

        self.settings_btn = SettingsButton()
        self.settings_btn.clicked.connect(self.open_settings)

        self.uied_btn = UIEDButton()
        self.uied_btn.clicked.connect(self.trigger_uied_detection)

        self.input_layout.addWidget(self.settings_btn)
        self.input_layout.addWidget(self.input_field, 1)
        self.input_layout.addWidget(self.send_btn)
        self.input_layout.addWidget(self.vision_btn)
        self.input_layout.addWidget(self.uied_btn)
        self.input_layout.addWidget(self.attach_btn)

        self.input_wrapper.setFixedWidth(self.expanded_size - self.collapsed_size)
        self.input_wrapper.hide()

        self.sparkle_wrapper = QWidget()
        self.sparkle_wrapper.setFixedSize(self.collapsed_size, self.collapsed_size)

        self.main_layout.addWidget(self.input_wrapper)
        self.main_layout.addWidget(self.sparkle_wrapper)

    def _setup_context_menu(self):
        self.context_menu = QMenu(self)
        self.context_menu.setStyleSheet("""
            QMenu { background-color: #1f2937; color: white; border-radius: 8px; padding: 4px; }
            QMenu::item { padding: 8px 20px; border-radius: 4px; }
            QMenu::item:selected { background-color: #6366f1; }
        """)

        settings_act = QAction("Settings", self)
        settings_act.triggered.connect(self.open_settings)

        quit_act = QAction("Quit Assistant", self)
        quit_act.triggered.connect(QApplication.quit)

        self.context_menu.addAction(settings_act)
        self.context_menu.addAction(quit_act)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        radius = height / 2.0

        painter.setOpacity(1.0 if (self.is_hovered or self.is_expanded) else 0.8)

        gradient = QLinearGradient(0, 0, width, height)
        gradient.setColorAt(0, QColor("#9333ea"))
        gradient.setColorAt(1, QColor("#2563eb"))

        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, width, height, radius, radius)

        painter.setOpacity(1.0)
        painter.setPen(QColor("white"))
        font = self.font()
        font.setPointSize(24)
        painter.setFont(font)

        rect = QRect(int(width - self.collapsed_size), 0, int(self.collapsed_size), int(self.collapsed_size))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "\u2728")

    def _on_anim_step(self, val: int):
        self.setFixedSize(val, self.collapsed_size)
        new_x = self._anim_right_edge - val + 1
        self.move(new_x, self.y())

    def update_size(self, expand: bool):
        target_width = self.expanded_size if expand else self.collapsed_size

        if getattr(self, "_current_target_width", -1) == target_width:
            return

        self._current_target_width = target_width

        if hasattr(self, 'anim') and getattr(self.anim, "state", lambda: None)() == QPropertyAnimation.State.Running:
            self.anim.stop()

        self._anim_right_edge = self.geometry().right()

        self.anim = QVariantAnimation(self)
        self.anim.setDuration(250)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.valueChanged.connect(self._on_anim_step)

        self.anim.setStartValue(self.width())
        self.anim.setEndValue(target_width)

        if expand:
            try:
                self.anim.finished.disconnect()
            except:
                pass

            def expand_done():
                self.input_wrapper.show()
                self.position_history_popup()
                self.input_field.setFocus()

            self.anim.finished.connect(expand_done)
        else:
            self.input_wrapper.hide()
            try:
                self.anim.finished.disconnect()
            except:
                pass

        self.anim.start()

    def enterEvent(self, event):
        if not self.is_dragging and not self.is_expanded:
            self.is_hovered = True
            self.update_size(True)
        self.update()

    def check_mouse_leave(self):
        if not self.is_expanded and not self.geometry().contains(QCursor.pos()):
            self.is_hovered = False
            self.update_size(False)
            self.update()

    def leaveEvent(self, event):
        QTimer.singleShot(100, self.check_mouse_leave)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_position = event.globalPosition().toPoint()
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        elif event.button() == Qt.MouseButton.RightButton:
            self.context_menu.exec(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self._press_position
            if delta.manhattanLength() > 5:
                self.is_dragging = True

            if self.is_dragging:
                screen = QApplication.primaryScreen().availableGeometry()
                new_pos = event.globalPosition().toPoint() - self.drag_position

                new_x = max(screen.left(), min(new_pos.x(), screen.right() - self.width()))
                new_y = max(screen.top(), min(new_pos.y(), screen.bottom() - self.height()))

                self.move(new_x, new_y)
                self.position_history_popup()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.is_dragging:
                sparkle_rect = QRect(int(self.width() - self.collapsed_size), 0, int(self.collapsed_size), int(self.collapsed_size))
                if sparkle_rect.contains(event.position().toPoint()):
                    if not self._config.is_configured():
                        self.open_settings()
                    else:
                        self.toggle_expand()
            self.is_dragging = False

    def toggle_expand(self):
        self.is_expanded = not self.is_expanded

        self.is_hovered = self.geometry().contains(QCursor.pos())

        self.update_size(self.is_expanded or self.is_hovered)
        self.update()

        if self.is_expanded:
            self.history_popup.show()
        else:
            self.history_popup.hide()

    def position_history_popup(self):
        screen = QApplication.primaryScreen().availableGeometry()
        x = self.x() + self.width() - self.history_popup.width()

        space_above = self.y() - screen.top()
        space_needed = self.history_popup.height() + 15

        if space_above >= space_needed:
            y = self.y() - space_needed
        else:
            y = self.y() + self.height() + 15

        new_x = max(screen.left(), min(x, screen.right() - self.history_popup.width()))
        new_y = max(screen.top(), min(y, screen.bottom() - self.history_popup.height()))

        self.history_popup.move(new_x, new_y)

    def _switch_to_session(self, session_id):
        sid, hist, last_uuid = self.session_service.load_session(session_id)
        self.session_id = sid
        self._chat_history = hist
        self.last_msg_uuid = last_uuid

        self.history_popup.clear_chat()
        for msg in self._chat_history:
            self.history_popup.add_message(msg["content"], "user" if msg["role"] == "user" else "ai")

    def open_settings(self):
        dialog = SettingsDialog(self._config, self.settings, self)
        dialog.exec()
        if self._config.is_configured():
            self._init_api()
            self.history_popup.add_message("Settings saved. API is configured.", "ai")
        else:
            self.history_popup.add_message("API not configured. Please set up your API key.", "ai")

    def _init_api(self):
        self.api_client = None
        if self._config.is_configured():
            try:
                provider_id = self._config.get_provider_id()
                if provider_id == "opencode":
                    self.api_client = ZenClient(self.settings)
                    logger.info("ZenClient initialized for OpenCode Zen")
                else:
                    self.api_client = APIClient(self.settings)
                    logger.info(f"APIClient initialized for {provider_id}")
            except Exception as e:
                logger.error(f"API init failed: {e}")

    def toggle_vision(self):
        self.is_vision_enabled = not self.is_vision_enabled
        self.vision_btn.is_green = self.is_vision_enabled

        if self.is_vision_enabled:
            self.input_field.setPlaceholderText("Vision ON - Describe what to click...")
            self.history_popup.add_message(
                "Vision mode ON\nDescribe what to interact with on screen.",
                "ai",
            )
            self._update_vision_status_bar()
        else:
            self.input_field.setPlaceholderText("Ask AI...")
            self.history_popup.add_message("Vision mode OFF", "ai")
            self._update_vision_status_bar()

        self.update()

    def _delayed_vision_start(self):
        if not self.is_vision_enabled:
            return
        ok = self._vision_service.start()
        if not ok:
            self.is_vision_enabled = False
            self.vision_btn.is_green = False
            self.history_popup.add_message(
                "Vision requires pyautogui + pynput.\n"
                "Run: pip install pyautogui pynput Pillow",
                "ai",
            )
            self._update_vision_status_bar()
            self.update()

    def _update_vision_status_bar(self):
        try:
            import pyautogui
            sw, sh = pyautogui.size()
            mx, my = pyautogui.position()
            status = f"VISION ON  |  {sw}x{sh}  |  ({mx},{my})" if self.is_vision_enabled else ""
        except Exception:
            status = "VISION ON" if self.is_vision_enabled else ""
        self.history_popup.set_vision_status(status)

    def _on_vision_screenshot(self, b64: str, meta: dict):
        if not self.is_vision_enabled:
            return
        if not getattr(self, 'api_client', None) or not self._config.is_configured():
            return

        if hasattr(self, '_rate_limited') and self._rate_limited:
            logger.debug("Vision: rate-limited, skipping API request")
            self.history_popup.add_message(
                f"Screenshot captured (rate-limited) | ({meta['mouse_x']},{meta['mouse_y']})",
                "ai"
            )
            return

        sw = meta["screen_width"]
        sh = meta["screen_height"]
        mx = meta["mouse_x"]
        my = meta["mouse_y"]
        xp = meta["mouse_x_pct"]
        yp = meta["mouse_y_pct"]

        self._last_screen_resolution = (sw, sh)

        from PIL import Image
        import io
        import base64
        screenshot_img = Image.open(io.BytesIO(base64.b64decode(b64)))
        self._last_screenshot_size = (screenshot_img.width, screenshot_img.height)
        logger.info(f"Screenshot size: {screenshot_img.width}x{screenshot_img.height}, Screen resolution: {sw}x{sh}")

        vision_text = (
            f"[VISION METADATA]\n"
            f"Screen Resolution: {sw}x{sh}\n"
            f"Current Mouse Position: ({mx}, {my})\n"
            f"Relative Position: ({xp:.3f}, {yp:.3f}) of screen\n\n"
            f"[TASK]\n"
            f"Analyze the attached screenshot. The user wants to interact with a UI element.\n"
            f"Use the current mouse position as context for what they're looking at.\n\n"
            f"[OUTPUT FORMAT]\n"
            f"Respond in this EXACT JSON format:\n"
            f"{{\n"
            f'  "action": "click",\n'
            f'  "target": [x, y],  // Pixel-perfect coordinates for {sw}x{sh} screen\n'
            f'  "confidence": 0.95,\n'
            f'  "description": "What element you found and why these coordinates"\n'
            f"}}\n\n"
            f"[IMPORTANT]\n"
            f"- Calculate coordinates for the FULL screen resolution ({sw}x{sh})\n"
            f"- If element is near current mouse, use those coordinates\n"
            f"- Be PRECISE - user will click exactly where you specify\n"
            f"- Center of buttons/icons is the best target\n"
        )

        payload = [
            {"type": "text", "text": vision_text},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
        ]

        self.history_popup.add_message(
            f"Vision: {sw}x{sh} | ({mx},{my})", "user"
        )
        self.history_popup.add_message("Analyzing...", "ai")

        if not self.is_expanded:
            self.toggle_expand()

        self._update_vision_status_bar()

        self.last_msg_uuid = self.session_service.save_message(
            self.session_id, "user", vision_text,
            attachments=[{"type": "image", "base64": b64, "mime": "image/png", "name": "screenshot.png"}],
            parent_uuid=self.last_msg_uuid,
        )

        self.worker = APIServerWorker(
            self.api_client, payload, self._chat_history, vision_mode=True
        )
        self.worker.chunk_received.connect(self._on_api_chunk)
        self.worker.finished_response.connect(self._on_api_finished)
        self.worker.error_occurred.connect(self._on_api_error)
        self.worker.start()

        self._chat_history.append({"role": "user", "content": payload})

    def select_files(self):
        from pathlib import Path
        import base64
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files", "", "All Files (*);;Images (*.png *.jpg *.jpeg *.bmp)")
        if not files:
            return

        for file_path in files:
            path = Path(file_path)
            content_type = "image" if path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp', '.gif'] else "file"

            if content_type == "image":
                try:
                    with open(path, "rb") as f:
                        b64 = base64.b64encode(f.read()).decode('utf-8')
                    self.staged_files.append({"type": "image", "path": str(path), "base64": b64, "name": path.name, "mime": f"image/{path.suffix[1:]}"})
                except Exception:
                    pass
            else:
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        text = f.read()
                    self.staged_files.append({"type": "file", "path": str(path), "content": text, "name": path.name})
                except:
                    pass

        self.update_staging_ui()

        if not self.is_expanded and self.staged_files:
            self.toggle_expand()

    def update_staging_ui(self):
        while self.history_popup.staging_layout.count():
            item = self.history_popup.staging_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.staged_files:
            self.history_popup.staging_scroll.hide()
            return

        self.history_popup.staging_scroll.show()

        for idx, f in enumerate(self.staged_files):
            chip = QWidget()
            chip.setStyleSheet("background: white; border: 1px solid #e5e7eb; border-radius: 6px;")
            chip.setFixedHeight(60)
            chip_layout = QHBoxLayout(chip)
            chip_layout.setContentsMargins(6, 6, 6, 6)

            if f['type'] == 'image':
                img_lbl = QLabel()
                pixmap = QPixmap()
                import base64
                pixmap.loadFromData(base64.b64decode(f['base64']))
                img_lbl.setPixmap(pixmap.scaledToHeight(48, Qt.TransformationMode.SmoothTransformation))
                chip_layout.addWidget(img_lbl)
            else:
                icon_lbl = QLabel("\uE7C3")
                icon_lbl.setStyleSheet("font-family: 'Segoe Fluent Icons', 'Segoe UI'; font-size: 24px; color: #6366f1; border: none;")
                chip_layout.addWidget(icon_lbl)
                name_lbl = QLabel(f['name'])
                name_lbl.setStyleSheet("font-size: 11px; color: #374151; font-weight: bold; border: none;")
                name_lbl.setMaximumWidth(100)
                chip_layout.addWidget(name_lbl)

            close_btn = QPushButton("\uE711")
            close_btn.setStyleSheet("QPushButton { font-family: 'Segoe Fluent Icons'; font-size: 12px; border: none; background: transparent; color: #ef4444; } QPushButton:hover { background: #fee2e2; border-radius: 10px; }")
            close_btn.setFixedSize(20, 20)
            close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            close_btn.clicked.connect(lambda checked, i=idx: self.remove_staged_file(i))

            chip_layout.addWidget(close_btn)
            self.history_popup.staging_layout.addWidget(chip)

        self.history_popup.staging_layout.addStretch()

    def remove_staged_file(self, idx):
        if 0 <= idx < len(self.staged_files):
            self.staged_files.pop(idx)
            self.update_staging_ui()

    def submit_message(self):
        text = self.input_field.text().strip()
        if not text and not self.staged_files:
            return

        if not text and self.staged_files:
            text = "Please refer to the attached files."

        self.messages_count += 1
        self.input_field.clear()

        att_copy = self.staged_files.copy()
        self.staged_files.clear()
        self.update_staging_ui()

        if not self.is_expanded:
            self.toggle_expand()

        self.history_popup.add_message(text, "user", attachments=att_copy)

        if getattr(self, "api_client", None) and self._config.is_configured():
            self.last_msg_uuid = self.session_service.save_message(self.session_id, "user", text, attachments=att_copy, parent_uuid=self.last_msg_uuid)
            self._handle_api(text, att_copy)
        else:
            QTimer.singleShot(400, lambda: self.history_popup.add_message("Please configure API key in Settings first.", "ai"))

    def _handle_api(self, text, attachments):
        self.history_popup.add_message("...", "ai")

        content_payload = []
        if text:
            content_payload.append({"type": "text", "text": text})

        if self.is_vision_enabled:
            try:
                import pyautogui, io, base64
                from PIL import Image

                sw, sh = pyautogui.size()
                mx, my = pyautogui.position()
                img = pyautogui.screenshot()
                img_w, img_h = img.size

                self._last_screen_resolution = (sw, sh)
                self._last_screenshot_size = (img_w, img_h)

                buf = io.BytesIO()
                img.save(buf, format="PNG", optimize=True, compress_level=1)
                b64 = base64.b64encode(buf.getvalue()).decode()

                logger.info(f"Vision screenshot: {img_w}x{img_h} -> Screen: {sw}x{sh}")

                vision_prompt = f"""
[VISION TASK]
Find this element: "{text if text else 'the element near mouse cursor'}"

Current mouse position: ({mx}, {my}) on {sw}x{sh} screen

[OUTPUT FORMAT - CRITICAL]
Respond ONLY in this JSON format:
{{
    "action": "click",
    "target_normalized": [0.0-1.0, 0.0-1.0],
    "confidence": 0.95,
    "description": "What you found"
}}

target_normalized[0] = x / {img_w} (0.0 = left edge, 1.0 = right edge)
target_normalized[1] = y / {img_h} (0.0 = top edge, 1.0 = bottom edge)

Be PRECISE - center of element. Example:
{{"action": "click", "target_normalized": [0.365, 0.898], "confidence": 0.95}}
"""
                content_payload = [
                    {"type": "text", "text": vision_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                ]

                logger.info(f"Vision: attached live screenshot ({len(b64)//1024}KB)")
            except Exception as e:
                logger.warning(f"Vision screenshot attach failed: {e}")

        for att in attachments:
            if att['type'] == 'image':
                content_payload.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{att.get('mime', 'image/png')};base64,{att['base64']}"},
                })
            elif att['type'] == 'file':
                if not content_payload:
                    content_payload.append({"type": "text", "text": ""})
                content_payload[0]['text'] += f"\n\n<document path='{att['name']}'>\n{att['content']}\n</document>"

        self.worker = APIServerWorker(
            self.api_client,
            content_payload if len(content_payload) > 1 else text,
            self._chat_history,
            vision_mode=self.is_vision_enabled,
        )
        self.worker.chunk_received.connect(self._on_api_chunk)
        self.worker.finished_response.connect(self._on_api_finished)
        self.worker.error_occurred.connect(self._on_api_error)
        self.worker.start()

        self._chat_history.append({"role": "user", "content": content_payload if len(content_payload) > 1 else text})

    def _on_api_chunk(self, chunk):
        self.history_popup.update_last_message(chunk)

    def _on_api_finished(self, full_text):
        self._set_send_mode()
        self.history_popup.update_last_message(full_text)
        self.last_msg_uuid = self.session_service.save_message(
            self.session_id, "assistant", full_text, parent_uuid=self.last_msg_uuid
        )
        self._chat_history.append({"role": "assistant", "content": full_text})

        if '"action"' in full_text and ('"target_name"' in full_text or '"description"' in full_text):
            logger.info("LLM returned action with target - triggering UIED execution")
            QTimer.singleShot(500, lambda: self._execute_uied_from_llm(full_text))

    def _execute_uied_from_llm(self, llm_response: str):
        import json
        import re

        json_match = re.search(r'```json\s*({.*?})\s*```', llm_response, re.DOTALL)
        if not json_match:
            json_match = re.search(r'({.*?"action".*?})', llm_response, re.DOTALL)

        if not json_match:
            logger.warning(f"No JSON found in LLM response: {llm_response[:200]}")
            return

        try:
            action_data = json.loads(json_match.group(1))
            action = action_data.get('action', 'click')
            target_name = action_data.get('target_name', '')
            description = action_data.get('description', '')

            logger.info(f"UIED-LLM: Parsed JSON: {action_data}")
            logger.info(f"UIED-LLM: Action={action}, Target={target_name}, Desc={description}")

            if not target_name and description:
                match = re.search(r'Found ([A-Za-z0-9\s\-_]+?)(?:\s+(?:icon|button|logo|text|element|in|at|on|the|a))', description, re.IGNORECASE)
                if match:
                    target_name = match.group(1).strip()
                    logger.info(f"UIED-LLM: Extracted target from description: '{target_name}'")
                else:
                    words = description.split()[:3]
                    target_name = ' '.join(words).replace('"', '').replace("'", '')[:30]
                    logger.info(f"UIED-LLM: Fallback target: '{target_name}'")

            if not target_name:
                logger.warning("UIED-LLM: No target_name in response")
                self.history_popup.add_message(
                    "LLM didn't identify a specific target. Please be more specific.",
                    "ai"
                )
                return

            self.history_popup.add_message(
                f"Finding '{target_name}' on screen...",
                "ai"
            )

            template_path = self._find_uied_template_for_target(target_name)

            if not template_path:
                logger.warning(f"UIED-LLM: No template found for '{target_name}'")
                self.history_popup.add_message(
                    f"'{target_name}' not found in detected components.\n"
                    f"Click UIED button to scan screen first.",
                    "ai"
                )
                return

            logger.info(f"UIED-LLM: Found template: {template_path}")
            coords = self._pyautogui_executor.find_with_template(template_path, threshold=0.7)

            if coords:
                cx, cy = coords
                logger.info(f"UIED-LLM: Match found at ({cx}, {cy})")
                self.history_popup.add_message(
                    f"Found '{target_name}' at ({cx}, {cy})\nExecuting: {action}",
                    "ai"
                )
                self._execute_uied_action(action, cx, cy, {'label': target_name})
            else:
                self.history_popup.add_message(
                    f"Could not locate '{target_name}' on current screen.\n"
                    f"The screen may have changed.",
                    "ai"
                )

        except json.JSONDecodeError as e:
            logger.error(f"UIED-LLM: Failed to parse JSON: {e}")
            logger.error(f"UIED-LLM: Raw response: {llm_response[:500]}")
            self.history_popup.add_message("Failed to parse LLM response", "ai")
        except Exception as e:
            logger.error(f"UIED-LLM: Error: {e}", exc_info=True)
            self.history_popup.add_message(f"Error: {e}", "ai")

    def _find_uied_template_for_target(self, target_name: str) -> Optional[str]:
        import os

        template_dir = os.path.join(
            os.path.expanduser("~"),
            ".qwen_desktop",
            "uied_templates"
        )

        if not os.path.exists(template_dir):
            logger.warning(f"UIED-LLM: Template directory not found: {template_dir}")
            return None

        target_lower = target_name.lower().replace('_', ' ').strip()

        template_files = [f for f in os.listdir(template_dir) if f.endswith('.png')]

        logger.info(f"UIED-LLM: Searching {len(template_files)} templates for '{target_name}'")

        for template_file in template_files:
            label_part = template_file.replace('.png', '')
            label_lower = label_part.lower().replace('_', ' ')

            if target_lower in label_lower or label_lower in target_lower:
                template_path = os.path.join(template_dir, template_file)
                logger.info(f"UIED-LLM: Found match: {template_file}")
                return template_path

        target_words = target_lower.split()
        for template_file in template_files:
            label_part = template_file.replace('.png', '').lower().replace('_', ' ')

            matches = sum(1 for word in target_words if word in label_part and len(word) > 3)
            if matches >= 1:
                template_path = os.path.join(template_dir, template_file)
                logger.info(f"UIED-LLM: Found fuzzy match: {template_file} ({matches} words)")
                return template_path

        logger.warning(f"UIED-LLM: No matching template found for '{target_name}'")
        return None

    def _execute_vision_action(self, action: str, target: List[int], confidence: float, target_name: str = None):
        model_x, model_y = target[0], target[1]

        if target_name and self._use_ui_automation:
            logger.info(f"[UIA] Priority 1: Trying UI Automation for '{target_name}'...")
            ui_result = self._find_with_ui_automation(target_name)
            if ui_result:
                center_x, center_y, element_name = ui_result
                logger.info(f"[UIA] Found via UI Automation: ({center_x}, {center_y})")
                import pyautogui
                pyautogui.moveTo(center_x, center_y, duration=0.2)
                pyautogui.click()
                self.history_popup.add_message(f"Clicked '{element_name}' (UI Automation)", "ai")
                return

        if target_name and target_name in self._template_cache:
            logger.info(f"[OPENCV] Priority 2: Template found for '{target_name}'. Fast matching...")
            try:
                import pyautogui
                screen = np.array(pyautogui.screenshot())
                screen_bgr = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)
                screen_gray = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2GRAY)

                template_gray = self._template_cache[target_name]
                res = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

                if max_val >= self._template_threshold:
                    h, w = template_gray.shape
                    center_x = max_loc[0] + (w // 2)
                    center_y = max_loc[1] + (h // 2)
                    logger.info(f"[OPENCV] Exact match! Confidence: {max_val:.2f} at ({center_x}, {center_y})")
                    pyautogui.moveTo(center_x, center_y, duration=0.2)
                    pyautogui.click()
                    self.history_popup.add_message(f"Clicked '{target_name}' (OpenCV)", "ai")
                    return
                else:
                    logger.info(f"[OPENCV] Match failed ({max_val:.2f} < {self._template_threshold}). Re-learning...")
                    del self._template_cache[target_name]
            except Exception as e:
                logger.debug(f"[OPENCV] Error: {e}. Falling back to VLM...")
                if target_name in self._template_cache:
                    del self._template_cache[target_name]

        logger.info(f"[VLM] Priority 3: No UIA/Template. Using VLM for '{target_name or 'target'}'...")

        is_normalized = (0.0 <= model_x <= 1.0) and (0.0 <= model_y <= 1.0)

        if is_normalized:
            if hasattr(self, '_last_screenshot_size') and hasattr(self, '_last_screen_resolution'):
                screenshot_w, screenshot_h = self._last_screenshot_size
                screen_w, screen_h = self._last_screen_resolution

                ss_x = model_x * screenshot_w
                ss_y = model_y * screenshot_h

                ratio_x = screen_w / screenshot_w
                ratio_y = screen_h / screenshot_h

                real_x = int(ss_x * ratio_x)
                real_y = int(ss_y * ratio_y)

                logger.info(f"Normalized: [{model_x:.4f}, {model_y:.4f}]")
                logger.info(f"Screenshot: {screenshot_w}x{screenshot_h}")
                logger.info(f"Screenshot pixels: ({ss_x:.1f}, {ss_y:.1f})")
                logger.info(f"Ratio: {ratio_x:.6f} x {ratio_y:.6f}")
                logger.info(f"Screen (before refine): [{real_x}, {real_y}] ({screen_w}x{screen_h})")

                try:
                    import pyautogui
                    import os
                    fresh_ss = np.array(pyautogui.screenshot())
                    fresh_bgr = cv2.cvtColor(fresh_ss, cv2.COLOR_RGB2BGR)
                    fresh_gray = cv2.cvtColor(fresh_bgr, cv2.COLOR_BGR2GRAY)

                    crop_size = 80
                    bbox_w = crop_size
                    bbox_h = crop_size

                    x1 = max(0, int(ss_x) - bbox_w // 2)
                    y1 = max(0, int(ss_y) - bbox_h // 2)
                    x2 = min(screenshot_w, int(ss_x) + bbox_w // 2)
                    y2 = min(screenshot_h, int(ss_y) + bbox_h // 2)

                    crop_gray = fresh_gray[y1:y2, x1:x2]
                    crop_bgr = fresh_bgr[y1:y2, x1:x2]

                    if crop_gray.size > 0 and target_name:
                        self._template_cache[target_name] = crop_gray

                        debug_dir = os.path.join(os.path.expanduser("~"), ".qwen-desktop", "templates")
                        os.makedirs(debug_dir, exist_ok=True)
                        template_path = os.path.join(debug_dir, f"{target_name}.png")
                        cv2.imwrite(template_path, crop_bgr)

                        logger.info(f"[LEARNED] Saved template for '{target_name}' (Size: {crop_gray.shape})")
                        logger.info(f"[LEARNED] Template saved to: {template_path}")
                except Exception as e:
                    logger.debug(f"Template extraction failed: {e}")

                target = [real_x, real_y]
            else:
                if hasattr(self, '_last_screen_resolution'):
                    screen_w, screen_h = self._last_screen_resolution
                    real_x = int(model_x * screen_w)
                    real_y = int(model_y * screen_h)
                    logger.warning(f"No screenshot size! Using screen: [{real_x}, {real_y}]")
                    target = [real_x, real_y]
                else:
                    logger.error("No screen resolution stored! Using normalized coords as-is")
        else:
            if hasattr(self, '_last_screenshot_size') and hasattr(self, '_last_screen_resolution'):
                img_w, img_h = self._last_screenshot_size
                screen_w, screen_h = self._last_screen_resolution

                scale_x = screen_w / img_w
                scale_y = screen_h / img_h

                real_x = int(model_x * scale_x)
                real_y = int(model_y * scale_y)

                logger.info(f"Scaling coords: [{model_x}, {model_y}] (image {img_w}x{img_h}) -> [{real_x}, {real_y}] (screen {screen_w}x{screen_h})")
                target = [real_x, real_y]
            else:
                logger.warning("No sizing info, using pixel coords as-is")

        if confidence < 0.7:
            self.history_popup.add_message(
                f"Low confidence ({confidence:.0%}). Should I proceed?",
                "ai",
            )
            return

        success = self._pyautogui_executor.execute(action, target, confidence)

        if success:
            if target_name:
                self.history_popup.add_message(f"Clicked '{target_name}' (VLM)", "ai")
            else:
                self.history_popup.add_message("Action completed!", "ai")
        else:
            self.history_popup.add_message("Action failed!", "ai")

    def _refine_with_template(self, screen_x: int, screen_y: int,
                               ss_x: int, ss_y: int,
                               screenshot_w: int, screenshot_h: int) -> Tuple[Optional[int], Optional[int]]:
        try:
            import pyautogui
            import cv2
            import numpy as np

            fresh_ss = pyautogui.screenshot()
            fresh_np = np.array(fresh_ss)
            fresh_bgr = cv2.cvtColor(fresh_np, cv2.COLOR_RGB2BGR)

            template_size = 40
            search_size = 80

            x1 = max(0, ss_x - template_size // 2)
            y1 = max(0, ss_y - template_size // 2)
            x2 = min(screenshot_w, ss_x + template_size // 2)
            y2 = min(screenshot_h, ss_y + template_size // 2)

            template = fresh_bgr[y1:y2, x1:x2].copy()

            if template.shape[0] < 10 or template.shape[1] < 10:
                return None, None

            sx1 = max(0, screen_x - search_size // 2)
            sy1 = max(0, screen_y - search_size // 2)
            sx2 = min(fresh_bgr.shape[1], screen_x + search_size // 2)
            sy2 = min(fresh_bgr.shape[0], screen_y + search_size // 2)

            search_area = fresh_bgr[sy1:sy2, sx1:sx2]

            if search_area.shape[0] < template.shape[0] or search_area.shape[1] < template.shape[1]:
                return None, None

            result = cv2.matchTemplate(search_area, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)

            if max_val < 0.6:
                logger.debug(f"Template match low: {max_val:.3f}")
                return None, None

            template_h, template_w = template.shape[:2]
            best_x_in_search = max_loc[0] + template_w // 2
            best_y_in_search = max_loc[1] + template_h // 2

            refined_screen_x = sx1 + best_x_in_search
            refined_screen_y = sy1 + best_y_in_search

            logger.debug(f"Template match: {max_val:.3f} at ({refined_screen_x}, {refined_screen_y})")

            return refined_screen_x, refined_screen_y

        except Exception as e:
            logger.debug(f"Template refinement error: {e}")
            return None, None

    def _on_api_error(self, err):
        self._set_send_mode()
        self.history_popup.update_last_message(f"API Error: {err}")

    def _set_stop_mode(self):
        self._is_sending = True
        self.send_btn.setStyleSheet("""
            QPushButton {
                background: #ef4444;
                border: none; border-radius: 8px;
                color: white; font-size: 16px; font-weight: bold;
            }
            QPushButton:hover { background: #dc2626; }
        """)
        try:
            self.send_btn.clicked.disconnect()
        except Exception:
            pass
        self.send_btn.clicked.connect(self._stop_worker)
        self.send_btn.setText("\u25A0")

    def _set_send_mode(self):
        self._is_sending = False
        self.send_btn.setStyleSheet("")
        self.send_btn.setText("")
        try:
            self.send_btn.clicked.disconnect()
        except Exception:
            pass
        self.send_btn.clicked.connect(self.submit_message)
        self.send_btn.update()

    def _stop_worker(self):
        if hasattr(self, 'worker') and self.worker:
            try:
                self.worker.chunk_received.disconnect()
                self.worker.finished_response.disconnect()
                self.worker.error_occurred.disconnect()
            except Exception:
                pass
            self.worker.quit()
            self.worker.wait(300)
            if self.worker.isRunning():
                self.worker.terminate()
        self._set_send_mode()
        self.history_popup.update_last_message("Stopped")

    def trigger_uied_detection(self):
        if self._is_uied_detecting:
            logger.info("Box editor already open")
            return

        logger.info("Opening manual box editor overlay")
        self._is_uied_detecting = True
        self.uied_btn.set_detecting(True)

        self._show_uied_overlay([])

    def _show_uied_overlay(self, components: list):
        if self._uied_overlay is None:
            self._uied_overlay = UIEDOverlayWidget(self)
            self._uied_overlay.component_edited.connect(self._on_uied_component_edited)
            self._uied_overlay.component_added.connect(self._on_uied_component_added)
            self._uied_overlay.component_deleted.connect(self._on_uied_component_deleted)
            self._uied_overlay.close_requested.connect(self._on_uied_overlay_closed)

        self._uied_overlay.set_components(components)
        self._uied_overlay.show()
        self._uied_overlay.activateWindow()

        logger.info("Manual box editor overlay shown")

    def _on_uied_component_edited(self, index: int, new_label: str, new_type: str):
        import os

        if 0 <= index < len(self._uied_components):
            comp = self._uied_components[index]
            comp['label'] = new_label
            comp['component_type'] = new_type

            old_path = comp.get('template_path')
            if old_path and os.path.exists(old_path):
                try:
                    template_dir = os.path.dirname(old_path)
                    safe_label = new_label.replace(' ', '_').replace('/', '_')[:40]
                    new_filename = f"{comp['id']}_{safe_label}_{new_type}.png"
                    new_path = os.path.join(template_dir, new_filename)
                    os.rename(old_path, new_path)
                    comp['template_path'] = new_path
                    logger.info(f"Template renamed: {new_filename}")
                except Exception as e:
                    logger.error(f"Failed to rename template: {e}")

            logger.info(f"Component {index} edited: {new_label} [{new_type}]")
            self._uied_overlay.set_components(self._uied_components)

    def _on_uied_component_added(self, x: int, y: int, w: int, h: int, label: str, comp_type: str):
        import uuid
        import cv2
        import numpy as np
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QBuffer, QIODevice
        from PIL import Image
        import io

        new_component = {
            'id': f"comp_user_{uuid.uuid4().hex[:6]}",
            'label': label,
            'component_type': comp_type,
            'x': x,
            'y': y,
            'width': w,
            'height': h,
            'center_x': x + w // 2,
            'center_y': y + h // 2,
            'confidence': 1.0,
            'template_path': None,
            '_template_gray': None,
            '_template_rgb': None,
        }

        try:
            logger.info(f"Capturing template at widget coordinates: ({x}, {y}) {w}x{h}")

            if self._uied_overlay:
                self._uied_overlay.hide()
                QApplication.processEvents()

            import time
            time.sleep(0.05)

            screen = QApplication.primaryScreen()
            pixmap = screen.grabWindow(0, x, y, w, h)

            if self._uied_overlay:
                self._uied_overlay.show()
                QApplication.processEvents()

            if pixmap.isNull():
                logger.error("grabWindow returned null pixmap")
                return

            logger.info(f"Pixmap size: {pixmap.width()}x{pixmap.height()}")

            buffer = QBuffer()
            buffer.open(QIODevice.OpenModeFlag.ReadWrite)
            pixmap.save(buffer, "PNG")

            img = Image.open(io.BytesIO(bytes(buffer.data())))
            template_rgb = np.array(img)
            template_bgr = cv2.cvtColor(template_rgb, cv2.COLOR_RGB2BGR)

            logger.info(f"Template captured: {template_bgr.shape}")

            new_component['_template_rgb'] = template_bgr
            new_component['_template_gray'] = cv2.cvtColor(template_bgr, cv2.COLOR_BGR2GRAY)

            logger.info(f"Template captured successfully using Qt grabWindow")

        except Exception as e:
            logger.error(f"Failed to capture template: {e}", exc_info=True)

        self._uied_components.append(new_component)
        self._uied_overlay.set_components(self._uied_components)

        logger.info(f"New component added: {label} [{comp_type}] at ({x}, {y}) {w}x{h}")

    def _on_uied_component_deleted(self, index: int):
        import os

        if 0 <= index < len(self._uied_components):
            deleted = self._uied_components.pop(index)

            template_path = deleted.get('template_path')
            if template_path and os.path.exists(template_path):
                try:
                    os.remove(template_path)
                    logger.info(f"Template deleted: {template_path}")
                except Exception as e:
                    logger.error(f"Failed to delete template: {e}")

            self._uied_overlay.set_components(self._uied_components)

            logger.info(f"Component {index} deleted: {deleted.get('label')}")

    def _on_uied_overlay_closed(self):
        logger.info(f"Manual box editor closed. Final component count: {len(self._uied_components)}")

        saved_count = 0

        import numpy as np
        import os
        import cv2

        template_dir = os.path.join(
            os.path.expanduser("~"),
            ".qwen_desktop",
            "uied_templates"
        )
        os.makedirs(template_dir, exist_ok=True)

        for comp_dict in self._uied_components:
            try:
                if '_template_rgb' in comp_dict and comp_dict['_template_rgb'] is not None:
                    template = comp_dict['_template_rgb']
                    safe_label = comp_dict.get('label', 'unknown').replace(' ', '_').replace('/', '_')[:40]
                    comp_type = comp_dict.get('component_type', 'other')
                    template_filename = f"{comp_dict.get('id', 'user')}_{safe_label}_{comp_type}.png"
                    template_path = os.path.join(template_dir, template_filename)
                    cv2.imwrite(template_path, template)
                    saved_count += 1
                    logger.info(f"Saved RGB template: {template_filename} {template.shape}")

                elif '_template_gray' in comp_dict and comp_dict['_template_gray'] is not None:
                    template_gray = comp_dict['_template_gray']
                    template = cv2.cvtColor(template_gray, cv2.COLOR_GRAY2BGR)
                    safe_label = comp_dict.get('label', 'unknown').replace(' ', '_').replace('/', '_')[:40]
                    comp_type = comp_dict.get('component_type', 'other')
                    template_filename = f"{comp_dict.get('id', 'user')}_{safe_label}_{comp_type}.png"
                    template_path = os.path.join(template_dir, template_filename)
                    cv2.imwrite(template_path, template)
                    saved_count += 1
                    logger.info(f"Saved grayscale template (fallback): {template_filename}")

            except Exception as e:
                logger.error(f"Failed to save template: {e}")

        self.history_popup.add_message(
            f"Box editor closed. {len(self._uied_components)} components created.\n"
            f"{saved_count} components labeled and saved to disk (RGB color).",
            "ai"
        )

        if self._uied_overlay:
            self._uied_overlay.hide()
            self._uied_overlay.close()
            self._uied_overlay = None

        self._uied_components = []
        self._is_uied_detecting = False
        self.uied_btn.set_has_results(False, 0)

    def _on_uied_component_selected(self, component: dict):
        logger.info(f"Component selected: {component.get('label')}")

        self.history_popup.add_message(
            f"Selected: **{component.get('label')}** "
            f"({component.get('component_type')}) at ({component.get('x')}, {component.get('y')})",
            "user"
        )

        self._last_uied_component = component

        self._handle_uied_component_action(component)

    def _handle_uied_component_action(self, component: dict):
        component_id = component.get('id')
        label = component.get('label', 'Unknown')
        template_path = component.get('template_path')

        logger.info(f"UIED: Handling action for '{label}' (id={component_id})")
        logger.info(f"UIED: Template path: {template_path}")
        logger.info(f"UIED: Component data: x={component.get('x')}, y={component.get('y')}, w={component.get('width')}, h={component.get('height')}")

        if not template_path:
            logger.warning(f"UIED: No template path for '{label}'")
            self.history_popup.add_message(
                f"No template saved for {label}",
                "ai"
            )
            return

        import os
        if not os.path.exists(template_path):
            logger.error(f"UIED: Template file not found: {template_path}")
            self.history_popup.add_message(
                f"Template file not found for {label}\nThe UI may have changed. Re-run detection.",
                "ai"
            )
            return

        if self._pyautogui_executor:
            logger.info(f"UIED: Attempting template matching with threshold=0.7")
            coords = self._pyautogui_executor.find_with_template(template_path, threshold=0.7)

            if coords:
                cx, cy = coords
                logger.info(f"UIED: Template match found at ({cx}, {cy})")
                self.history_popup.add_message(
                    f"Template match found at ({cx}, {cy}) - 100% accurate!",
                    "ai"
                )
                self._ask_uied_action(label, cx, cy, component)
                return
            else:
                logger.warning(f"UIED: Template match failed for '{label}'")

        cx = component.get('center_x') or (component.get('x', 0) + component.get('width', 0) // 2)
        cy = component.get('center_y') or (component.get('y', 0) + component.get('height', 0) // 2)

        logger.info(f"UIED: Using stored coordinates: ({cx}, {cy})")
        self.history_popup.add_message(
            f"Using stored coordinates: ({cx}, {cy})\nTemplate match failed - UI may have changed",
            "ai"
        )
        self._ask_uied_action(label, cx, cy, component)

    def _ask_uied_action(self, label: str, x: int, y: int, component: dict):
        actions_menu = QMenu(self)
        actions_menu.setStyleSheet("""
            QMenu {
                background-color: #1f2937;
                color: white;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 8px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #6366f1;
            }
        """)

        click_act = QAction(f"Click '{label}'", self)
        click_act.triggered.connect(lambda: self._execute_uied_action('click', x, y, component))

        double_act = QAction(f"Double-click '{label}'", self)
        double_act.triggered.connect(lambda: self._execute_uied_action('double_click', x, y, component))

        type_act = QAction(f"Type into '{label}'", self)
        type_act.triggered.connect(lambda: self._execute_uied_action('type', x, y, component))

        actions_menu.addAction(click_act)
        actions_menu.addAction(double_act)
        actions_menu.addAction(type_act)

        actions_menu.exec(self.mapToGlobal(self.uied_btn.pos()))

    def _execute_uied_action(self, action: str, x: int, y: int, component: dict):
        label = component.get('label', 'Unknown')

        logger.info(f"UIED: Executing '{action}' at ({x}, {y}) for '{label}'")

        try:
            import pyautogui

            screen_w, screen_h = pyautogui.size()

            if x < 0 or x >= screen_w or y < 0 or y >= screen_h:
                error_msg = f"Coordinates ({x}, {y}) out of bounds (screen: {screen_w}x{screen_h})"
                logger.error(f"UIED: {error_msg}")
                self.history_popup.add_message(f"Error: {error_msg}", "ai")
                return

            pyautogui.FAILSAFE = False

            if action == 'click':
                logger.info(f"UIED: Moving to ({x}, {y}) and clicking")
                pyautogui.moveTo(x, y, duration=0.3)
                pyautogui.click()
                self.history_popup.add_message(f"Clicked '{label}' at ({x}, {y})", "ai")

            elif action == 'double_click':
                logger.info(f"UIED: Moving to ({x}, {y}) and double-clicking")
                pyautogui.moveTo(x, y, duration=0.3)
                pyautogui.doubleClick()
                self.history_popup.add_message(f"Double-clicked '{label}' at ({x}, {y})", "ai")

            elif action == 'type':
                logger.info(f"UIED: Moving to ({x}, {y}) and clicking for typing")
                pyautogui.moveTo(x, y, duration=0.3)
                pyautogui.click()
                self.history_popup.add_message(
                    f"Clicked '{label}' - ready for typing.\nType your message in the input field.",
                    "ai"
                )

            pyautogui.FAILSAFE = True

            logger.info(f"UIED: Action '{action}' completed successfully")

        except Exception as e:
            error_msg = f"Action '{action}' failed: {str(e)}"
            logger.error(f"UIED: {error_msg}", exc_info=True)
            self.history_popup.add_message(f"Error: {error_msg}", "ai")
