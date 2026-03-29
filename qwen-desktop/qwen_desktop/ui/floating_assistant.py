"""
Floating AI Assistant Widget.
Matches the exact expanding, glowing, modern UI from the React design.
Includes Vision Capture (auto-screenshot on interaction) and
PyAutoGUI desktop automation via [PYAUTOGUI]...[/PYAUTOGUI] blocks.
"""
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
from typing import List
import datetime
import asyncio
import logging
from qwen_desktop.core.qwen_session_service import QwenSessionService
from qwen_desktop.core.vision_capture import VisionCaptureService
from qwen_desktop.core.pyautogui_executor import PyAutoGUIExecutor
import uuid

from qwen_desktop.ui.components.vision_button import VisionButton
from qwen_desktop.ui.components.attach_button import AttachButton
from qwen_desktop.ui.components.send_button import SendButton
from qwen_desktop.ui.components.settings_button import SettingsButton

logger = logging.getLogger(__name__)

class APIServerWorker(QThread):
    """QThread worker to run DashScope API calls without blocking the UI."""
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
    """A chat message bubble resembling the React design."""
    def __init__(self, text: str, sender: str, is_vision: bool = False, attachments: list = None, parent=None):
        super().__init__(parent)
        self.sender = sender
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 12, 16, 12)
        
        # Bubble Frame
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
            
        # Render File Chips Above Text
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
        
        # Render Image Previews Below Text
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
                        except Exception as e:
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
    """The Chat History Panel that pops up over the button."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(600, 450)
        self._last_ai_bubble = None
        
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(10, 10, 10, 10)
        
        # Main rounded container
        self.container = QFrame()
        self.container.setStyleSheet("""
            QFrame#HistoryContainer {
                background-color: transparent;
            }
        """)
        self.container.setObjectName("HistoryContainer")
        
        # Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 70))
        shadow.setOffset(0, 8)
        self.container.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
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
        
        title = QLabel("✨ Chat History")
        title.setStyleSheet("color: white; font-weight: bold; background: transparent;")
        h_layout.addWidget(title)

        # Vision status label (hidden by default)
        self.vision_status_lbl = QLabel("")
        self.vision_status_lbl.setStyleSheet(
            "color: #86efac; font-size: 11px; font-weight: bold; "
            "background: rgba(0,0,0,0.25); border-radius: 6px; padding: 2px 8px;"
        )
        self.vision_status_lbl.hide()
        h_layout.addWidget(self.vision_status_lbl)

        self.close_btn = QPushButton("✕")
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
        
        # Content Split
        content_w = QWidget()
        # White background handles the rounded corners cleanly
        content_w.setStyleSheet("background-color: #ffffff; border-bottom-left-radius: 16px; border-bottom-right-radius: 16px;")
        c_layout = QHBoxLayout(content_w)
        c_layout.setContentsMargins(0, 0, 0, 0)
        c_layout.setSpacing(0)
        
        # Left Panel (Sessions List)
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
        # Explicit explicitly setting background to transparent stops the sharp corners from overlapping radius
        self.session_list_w.setStyleSheet("background: transparent;")
        self.session_layout = QVBoxLayout(self.session_list_w)
        self.session_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.session_layout.setContentsMargins(6, 6, 6, 6)
        self.session_layout.setSpacing(4)
        
        self.session_scroll.setWidget(self.session_list_w)
        c_layout.addWidget(self.session_scroll)
        
        # Right Panel Wrapper
        right_panel_w = QWidget()
        right_panel_w.setStyleSheet("background: transparent;")
        rp_layout = QVBoxLayout(right_panel_w)
        rp_layout.setContentsMargins(0, 0, 0, 0)
        rp_layout.setSpacing(0)
        
        # Right Panel (Chat View)
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
        
        # Attachment Staging Area
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
        # Clear old sessions
        while self.session_layout.count():
            item = self.session_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
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
            
            # Using default arg value u=s['id'] creates closure binding
            btn.clicked.connect(lambda checked, u=s['id']: click_callback(u)) 
            self.session_layout.addWidget(btn)
            
    def clear_chat(self):
        while self.msg_layout.count():
            item = self.msg_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self._last_ai_bubble = None
        
    def add_message(self, text, sender, attachments=None):
        bubble = MessageBubble(text, sender, attachments=attachments)
        if sender == "ai":
            self._last_ai_bubble = bubble
        self.msg_layout.addWidget(bubble)
        self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum())
        # Scroll to bottom
        QTimer.singleShot(50, self.scroll_to_bottom)

    def update_last_message(self, text):
        if self._last_ai_bubble:
            self._last_ai_bubble.update_text(text)
            self.scroll_to_bottom()

    def scroll_to_bottom(self):
        bar = self.scroll.verticalScrollBar()
        bar.setValue(bar.maximum())

    def set_vision_status(self, status: str):
        """Update the vision status label in the popup header."""
        if status:
            self.vision_status_lbl.setText(status)
            self.vision_status_lbl.show()
        else:
            self.vision_status_lbl.hide()


class FloatingAssistant(QWidget):
    """The main expanding button acting as the full interface."""
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings

        self.is_hovered = False
        self.is_expanded = False
        self.is_dragging = False
        self.is_vision_enabled = False

        # PyAutoGUI execution mode: 'ask_first' or 'auto'
        self._pyautogui_mode = PyAutoGUIExecutor.ASK_FIRST
        # Last screenshot resolution (for coordinate scaling)
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
        self._check_auth()

        # Load QwenSessionService
        self.session_service = QwenSessionService(self.settings.get("cwd", ""))

        # Force a NEW session explicitly on each boot
        self.session_id = str(uuid.uuid4())
        self._chat_history = []
        self.last_msg_uuid = None
        self.messages_count = 0
        self.staged_files = []

        # Vision capture service
        self._vision_service = VisionCaptureService(self)
        self._vision_service.screenshot_ready.connect(self._on_vision_screenshot)

        # PyAutoGUI executor
        self._pyautogui_executor = PyAutoGUIExecutor(mode=self._pyautogui_mode)

        # Hook up sessions logic
        self.load_session_clicked = lambda u: self._switch_to_session(u)
        self.history_popup.populate_sessions(
            self.session_service.get_all_sessions(), self.load_session_clicked
        )

        # Global click tracker
        QApplication.instance().installEventFilter(self)

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
        
        # Transparent Input Area wrapper
        self.input_wrapper = QWidget()
        self.input_layout = QHBoxLayout(self.input_wrapper)
        self.input_layout.setContentsMargins(15, 0, 10, 0)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask Qwen AI...")
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
        # _is_sending tracks whether we're mid-API call (send → stop mode)
        self._is_sending = False

        self.vision_btn = VisionButton()
        self.vision_btn.clicked.connect(self.toggle_vision)

        self.attach_btn = AttachButton()
        self.attach_btn.clicked.connect(self.select_files)

        self.settings_btn = SettingsButton()
        self.settings_btn.clicked.connect(self.toggle_auth)

        # Layout: [settings] [input] [send/stop] [vision] [attach]
        self.input_layout.addWidget(self.settings_btn)
        self.input_layout.addWidget(self.input_field, 1)
        self.input_layout.addWidget(self.send_btn)   # right next to input
        self.input_layout.addWidget(self.vision_btn)
        self.input_layout.addWidget(self.attach_btn)
        
        self.input_wrapper.setFixedWidth(self.expanded_size - self.collapsed_size)
        self.input_wrapper.hide()
        
        # Sparkle Button wrapper
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
        
        login_act = QAction("Login/Auth", self)
        login_act.triggered.connect(self.trigger_login)
        
        quit_act = QAction("Quit Assistant", self)
        quit_act.triggered.connect(QApplication.quit)
        
        self.context_menu.addAction(login_act)
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
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "✨")
            
    def _on_anim_step(self, val: int):
        self.setFixedSize(val, self.collapsed_size)
        new_x = self._anim_right_edge - val + 1
        self.move(new_x, self.y())

    def update_size(self, expand: bool):
        target_width = self.expanded_size if expand else self.collapsed_size
        
        if getattr(self, "_current_target_width", -1) == target_width: 
            return
            
        self._current_target_width = target_width

        # Stop any running animation
        if hasattr(self, 'anim') and getattr(self.anim, "state", lambda: None)() == QPropertyAnimation.State.Running:
            self.anim.stop()
            
        from PyQt6.QtCore import QVariantAnimation, QEasingCurve
        
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
                # Focus the line edit after fully appearing
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
        from PyQt6.QtGui import QCursor
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
                    if not getattr(self, "oauth", None) or not self.oauth.is_authenticated():
                        self.trigger_login()
                    else:
                        self.toggle_expand()
            self.is_dragging = False

    def toggle_expand(self):
        self.is_expanded = not self.is_expanded
        
        from PyQt6.QtGui import QCursor
        self.is_hovered = self.geometry().contains(QCursor.pos())
        
        self.update_size(self.is_expanded or self.is_hovered)
        self.update()
        
        if self.is_expanded:
            self.history_popup.show()
            # self.input_field.setFocus()  # Moved to expand_done in update_size
        else:
            self.history_popup.hide()

    def position_history_popup(self):
        screen = QApplication.primaryScreen().availableGeometry()
        x = self.x() + self.width() - self.history_popup.width()
        
        # Determine if there is enough space ABOVE the regular bar to fit the UI. 
        # If there isn't, draw it strictly BELOW the bar to prevent screen clamping overlaps.
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

    def toggle_auth(self):
        if not self.oauth: 
            self.trigger_login()
            return
            
        if self.oauth.is_authenticated():
            self.oauth.logout()
            self._check_auth() # Reset
            self.history_popup.add_message("Logged out successfully.", "ai")
        else:
            self.trigger_login()

    def _check_auth(self):
        self.oauth = None
        self.api_client = None
        try:
            from qwen_desktop.auth.oauth_handler import OAuthHandler
            from qwen_desktop.core.api_client import APIClient
            self.oauth = OAuthHandler()
            if self.oauth.is_authenticated():
                self.api_client = APIClient(self.settings, self.oauth)
        except Exception as e:
            print(f"API Setup Failed: {e}")

    def trigger_login(self):
        try:
            from qwen_desktop.auth.qwen_auth_gui import QwenAuthDialog
            self.auth_dialog = QwenAuthDialog(self)
            self.auth_dialog.auth_success.connect(self._on_login_success)
            self.auth_dialog.show()
        except Exception as e:
            print(f"Login trigger failed: {e}")
            
    def _on_login_success(self, credentials):
        self._check_auth()
        if self.api_client:
            self.history_popup.add_message("Login successful! ✨", "ai")
            
    def toggle_vision(self):
        """Start/stop the vision capture service and update UI indicators."""
        self.is_vision_enabled = not self.is_vision_enabled
        self.vision_btn.is_green = self.is_vision_enabled

        if self.is_vision_enabled:
            # Delay listener start by 1.0s so the click that toggled vision
            # doesn't immediately trigger a screenshot capture.
            self._vision_start_ignore_until = __import__('time').time() + 1.0
            QTimer.singleShot(1000, self._delayed_vision_start)
            self.input_field.setPlaceholderText("👁 Vision active — interact to capture...")
            self.history_popup.add_message(
                "👁 Vision mode ON\nAny mouse click or key press will send a screenshot to Qwen.",
                "ai",
            )
            self._update_vision_status_bar()
        else:
            self._vision_service.stop()
            self.input_field.setPlaceholderText("Ask Qwen AI...")
            self.history_popup.add_message("👁 Vision mode OFF", "ai")
            self._update_vision_status_bar()

        self.update()

    def _delayed_vision_start(self):
        """Start the pynput listeners after the toggle-click delay has passed."""
        if not self.is_vision_enabled:
            return  # User disabled vision in the meantime
        ok = self._vision_service.start()
        if not ok:
            self.is_vision_enabled = False
            self.vision_btn.is_green = False
            self.history_popup.add_message(
                "⚠ Vision requires pyautogui + pynput.\n"
                "Run: pip install pyautogui pynput Pillow",
                "ai",
            )
            self._update_vision_status_bar()
            self.update()

    def _update_vision_status_bar(self):
        """Show/hide the vision status label in the popup header."""
        try:
            import pyautogui
            sw, sh = pyautogui.size()
            mx, my = pyautogui.position()
            status = f"👁 VISION ON  |  {sw}×{sh}  |  🖱 ({mx},{my})" if self.is_vision_enabled else ""
        except Exception:
            status = "👁 VISION ON" if self.is_vision_enabled else ""
        self.history_popup.set_vision_status(status)

    # ── Vision screenshot handler ────────────────────────────────────────────

    def _on_vision_screenshot(self, b64: str, meta: dict):
        """
        Called by VisionCaptureService when user sends input with vision enabled.
        Sends screenshot + screen resolution + mouse coordinates to Qwen for analysis.
        Qwen calculates pixel-perfect coordinates using bounding box + metadata.
        """
        if not self.is_vision_enabled:
            return
        if not self.oauth or not self.oauth.is_authenticated() or not self.api_client:
            return

        # Skip if rate-limited (quota exceeded)
        if hasattr(self, '_rate_limited') and self._rate_limited:
            logger.debug("Vision: rate-limited, skipping API request")
            self.history_popup.add_message(
                f"📸 Screenshot captured (rate-limited) | 🖱 ({meta['mouse_x']},{meta['mouse_y']})",
                "ai"
            )
            return

        sw = meta["screen_width"]
        sh = meta["screen_height"]
        mx = meta["mouse_x"]
        my = meta["mouse_y"]
        xp = meta["mouse_x_pct"]
        yp = meta["mouse_y_pct"]

        # Store last resolution for coordinate scaling
        self._last_vision_w = sw
        self._last_vision_h = sh

        # ── ENHANCED PROMPT: Qwen calculates pixel-perfect coordinates ──
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
        # ────────────────────────────────────────────────────────────────

        payload = [
            {"type": "text", "text": vision_text},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
        ]

        # Show in chat
        self.history_popup.add_message(
            f"📸 Vision: {sw}×{sh} | 🖱 ({mx},{my})", "user"
        )
        self.history_popup.add_message("🤔 Analyzing...", "ai")

        # Expand popup if collapsed
        if not self.is_expanded:
            self.toggle_expand()

        # Update status bar with live coords
        self._update_vision_status_bar()

        # Save to session
        self.last_msg_uuid = self.session_service.save_message(
            self.session_id, "user", vision_text,
            attachments=[{"type": "image", "base64": b64, "mime": "image/png", "name": "screenshot.png"}],
            parent_uuid=self.last_msg_uuid,
        )

        # Fire API (vision_mode=True injects expert system prompt)
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
        if not files: return
        
        for file_path in files:
            path = Path(file_path)
            content_type = "image" if path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp', '.gif'] else "file"
            
            if content_type == "image":
                try:
                    with open(path, "rb") as f:
                        b64 = base64.b64encode(f.read()).decode('utf-8')
                    self.staged_files.append({"type": "image", "path": str(path), "base64": b64, "name": path.name, "mime": f"image/{path.suffix[1:]}"})
                except Exception as e:
                    pass
            else:
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        text = f.read()
                    self.staged_files.append({"type": "file", "path": str(path), "content": text, "name": path.name})
                except:
                    pass
                    
        self.update_staging_ui()
        
        # Prevent floating button from staying closed if user clicked outside during FileDialog
        if not self.is_expanded and self.staged_files:
            self.toggle_expand()

    def update_staging_ui(self):
        while self.history_popup.staging_layout.count():
            item = self.history_popup.staging_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
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
        
        if self.oauth and self.oauth.is_authenticated() and getattr(self, "api_client", None):
            self.last_msg_uuid = self.session_service.save_message(self.session_id, "user", text, attachments=att_copy, parent_uuid=self.last_msg_uuid)
            self._handle_api(text, att_copy)
        else:
            QTimer.singleShot(400, lambda: self.history_popup.add_message("Please login first.", "ai"))
            
    def _handle_api(self, text, attachments):
        self.history_popup.add_message("...", "ai")

        content_payload = []
        if text:
            content_payload.append({"type": "text", "text": text})

        # ── Feature 1: Vision ON → auto-attach live screenshot to user message ──
        if self.is_vision_enabled:
            try:
                import pyautogui, io, base64
                sw, sh = pyautogui.size()
                mx, my = pyautogui.position()
                img = pyautogui.screenshot()
                buf = io.BytesIO()
                img.save(buf, format="PNG", optimize=True)
                b64 = base64.b64encode(buf.getvalue()).decode()
                vision_meta = (
                    f"[VISION] Screen: {sw}x{sh} | Mouse: ({mx},{my}) | "
                    f"Rel: ({mx/sw:.3f},{my/sh:.3f})"
                )
                # Prepend metadata to first text part
                if content_payload and content_payload[0]["type"] == "text":
                    content_payload[0]["text"] = vision_meta + "\n" + content_payload[0]["text"]
                else:
                    content_payload.insert(0, {"type": "text", "text": vision_meta})
                # Append screenshot image
                content_payload.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64}"},
                })
                self._last_vision_w = sw
                self._last_vision_h = sh
                logger.info(f"Vision: attached live screenshot to user message ({len(b64)//1024}KB)")
            except Exception as e:
                logger.warning(f"Vision screenshot attach failed: {e}")

        for att in attachments:
            if att['type'] == 'image':
                content_payload.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{att.get('mime', 'image/png')};base64,{att['base64']}"}
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
        self._set_send_mode()   # restore send button
        self.history_popup.update_last_message(full_text)
        self.last_msg_uuid = self.session_service.save_message(
            self.session_id, "assistant", full_text, parent_uuid=self.last_msg_uuid
        )
        self._chat_history.append({"role": "assistant", "content": full_text})

        # ── NEW: Parse and execute vision actions (JSON format) ──────────────
        parsed = self._pyautogui_executor.parse_response(full_text)
        
        if parsed and "target" in parsed:
            # Extract action details from JSON
            action = parsed.get("action", "click")
            target = parsed["target"]
            confidence = parsed.get("confidence", 1.0)
            description = parsed.get("description", "")
            
            # Show what we're doing
            self.history_popup.add_message(
                f"🎯 {description}\nExecuting: {action} at {target}",
                "ai",
            )
            
            # Execute after short delay (user can see what's happening)
            QTimer.singleShot(
                500,
                lambda: self._execute_vision_action(action, target, confidence),
            )
        
        # ── PyAutoGUI command detection (existing fallback) ─────────────────
        if self._pyautogui_executor.has_commands(full_text):
            commands = self._pyautogui_executor.extract_commands(full_text)
            if commands:
                self._handle_pyautogui_commands(commands)
    
    def _execute_vision_action(
        self,
        action: str,
        target: List[int],
        confidence: float,
    ):
        """Execute vision-based action."""
        # Low confidence - ask for confirmation
        if confidence < 0.7:
            self.history_popup.add_message(
                f"⚠️ Low confidence ({confidence:.0%}). Should I proceed?",
                "ai",
            )
            # Add confirm/skip buttons (implement later)
            return
        
        # Execute directly
        success = self._pyautogui_executor.execute(action, target, confidence)
        
        if success:
            self.history_popup.add_message("✅ Action completed!", "ai")
        else:
            self.history_popup.add_message("❌ Action failed!", "ai")

    def _on_api_error(self, err):
        self._set_send_mode()   # restore send button on error too
        self.history_popup.update_last_message(f"API Error: {err}")
        
        # Handle rate limit errors gracefully
        if "429" in str(err) or "insufficient_quota" in str(err):
            self.history_popup.add_message(
                "⚠️ **Rate Limit Reached**\n\n"
                "Your OAuth free tier quota (1000 requests/day) has been exceeded.\n\n"
                "**Options:**\n"
                "1. Wait until midnight UTC for quota reset\n"
                "2. Add an API key in settings for unlimited access\n"
                "3. Continue using without vision mode\n\n"
                "Vision mode will continue capturing screenshots, but won't send API requests.",
                "ai"
            )
            # Mark rate-limited state
            self._rate_limited = True

    # ── Send ↔ Stop button toggle ───────────────────────────────────────────────────────

    def _set_stop_mode(self):
        """Convert send button to red stop button during API call."""
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
        self.send_btn.setText("■")

    def _set_send_mode(self):
        """Restore send button to normal state."""
        self._is_sending = False
        self.send_btn.setStyleSheet("")   # BaseButton paints itself
        self.send_btn.setText("")         # BaseButton draws the icon
        try:
            self.send_btn.clicked.disconnect()
        except Exception:
            pass
        self.send_btn.clicked.connect(self.submit_message)
        self.send_btn.update()

    def _stop_worker(self):
        """Abort the running API worker and restore UI."""
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
        self.history_popup.update_last_message("⏹ Stopped")

    def _handle_pyautogui_commands(self, commands: list):
        """Always auto-execute pyautogui commands, then send feedback screenshot."""
        ok, result = self._pyautogui_executor.execute(
            commands, self._last_vision_w, self._last_vision_h
        )
        self.history_popup.add_message(f"🤖 Executed:\n{result}", "ai")
        # Send feedback screenshot after screen settles
        QTimer.singleShot(600, lambda: self._send_pyautogui_feedback(result))

    # ── Ask-first preview card removed ── always auto now ────────────────────

    def _show_pyautogui_preview_card(self, commands: list, preview: str):
        """Insert a confirm card in the chat popup for pyautogui commands."""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: #1e1e2e;
                border: 1px solid #6366f1;
                border-radius: 10px;
                margin: 4px 16px;
            }
        """)
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(12, 10, 12, 10)
        c_layout.setSpacing(6)

        title = QLabel("🤖 PyAutoGUI Commands Detected")
        title.setStyleSheet("color: #a5b4fc; font-weight: bold; font-size: 12px; background: transparent;")
        c_layout.addWidget(title)

        code_lbl = QTextEdit()
        code_lbl.setReadOnly(True)
        code_lbl.setPlainText(preview)
        code_lbl.setStyleSheet(
            "background: #12121f; color: #e2e8f0; font-family: 'Consolas', monospace; "
            "font-size: 11px; border: none; border-radius: 6px;"
        )
        code_lbl.setFixedHeight(min(120, 24 * len(commands) + 30))
        c_layout.addWidget(code_lbl)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        run_btn = QPushButton("▶  Run")
        run_btn.setStyleSheet("""
            QPushButton {
                background: #6366f1; color: white; border: none;
                border-radius: 6px; padding: 6px 18px; font-weight: bold;
            }
            QPushButton:hover { background: #4f46e5; }
        """)
        run_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        skip_btn = QPushButton("✕  Skip")
        skip_btn.setStyleSheet("""
            QPushButton {
                background: #374151; color: #9ca3af; border: none;
                border-radius: 6px; padding: 6px 14px;
            }
            QPushButton:hover { background: #4b5563; color: white; }
        """)
        skip_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        auto_btn = QPushButton("⚡ Set Auto")
        auto_btn.setStyleSheet("""
            QPushButton {
                background: #065f46; color: #6ee7b7; border: none;
                border-radius: 6px; padding: 6px 12px; font-size: 11px;
            }
            QPushButton:hover { background: #047857; }
        """)
        auto_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        btn_row.addWidget(run_btn)
        btn_row.addWidget(skip_btn)
        btn_row.addStretch()
        btn_row.addWidget(auto_btn)
        c_layout.addLayout(btn_row)

        def _run():
            ok, result = self._pyautogui_executor.execute(
                commands, self._last_vision_w, self._last_vision_h
            )
            code_lbl.setPlainText(result)
            run_btn.setEnabled(False)
            run_btn.setText("✅ Done")
            skip_btn.setEnabled(False)
            # ── Feature 2: send feedback screenshot after execution ──────────────
            QTimer.singleShot(600, lambda: self._send_pyautogui_feedback(result))

        def _skip():
            card.hide()

        def _set_auto():
            self._pyautogui_mode = PyAutoGUIExecutor.AUTO
            self._pyautogui_executor.mode = PyAutoGUIExecutor.AUTO
            auto_btn.setText("✅ Auto ON")
            auto_btn.setStyleSheet(
                "QPushButton { background: #047857; color: #6ee7b7; border: none; "
                "border-radius: 6px; padding: 6px 12px; font-size: 11px; }"
            )
            _run()

        run_btn.clicked.connect(_run)
        skip_btn.clicked.connect(_skip)
        auto_btn.clicked.connect(_set_auto)

        self.history_popup.msg_layout.addWidget(card)
        QTimer.singleShot(50, self.history_popup.scroll_to_bottom)

    def _on_api_error(self, err):
        self.history_popup.update_last_message(f"API Error: {err}")

    # ── PyAutoGUI feedback screenshot ──────────────────────────────────────────

    def _send_pyautogui_feedback(self, exec_result: str):
        """
        After pyautogui executes, take a screenshot of the current screen
        and send it to Qwen as feedback so it can see the result and
        decide on next steps automatically.
        Called 600ms after execution so the screen has time to settle.
        """
        if not self.oauth or not self.oauth.is_authenticated() or not self.api_client:
            return
        # Don't stack if a worker is already running
        if hasattr(self, 'worker') and self.worker and self.worker.isRunning():
            return
        try:
            import pyautogui, io, base64
            sw, sh = pyautogui.size()
            mx, my = pyautogui.position()
            img = pyautogui.screenshot()
            buf = io.BytesIO()
            img.save(buf, format="PNG", optimize=True)
            b64 = base64.b64encode(buf.getvalue()).decode()
        except Exception as e:
            logger.warning(f"PyAutoGUI feedback screenshot failed: {e}")
            return

        feedback_text = (
            f"[PYAUTOGUI-FEEDBACK] Execution complete.\n"
            f"Result: {exec_result}\n"
            f"Current screen: {sw}x{sh} | Mouse now at: ({mx},{my})\n"
            "Analyze the screenshot to see the result. "
            "If the task is complete, say so. If more actions are needed, provide them."
        )

        payload = [
            {"type": "text", "text": feedback_text},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
        ]

        # Show compact feedback marker in chat
        self.history_popup.add_message(
            f"📸 Feedback: {sw}×{sh} | 🖱 ({mx},{my})", "user"
        )
        self.history_popup.add_message("...", "ai")

        # Save to session
        self.last_msg_uuid = self.session_service.save_message(
            self.session_id, "user", feedback_text,
            attachments=[{"type": "image", "base64": b64, "mime": "image/png", "name": "feedback.png"}],
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
        logger.info(f"PyAutoGUI feedback sent: {sw}x{sh} @ ({mx},{my})")
