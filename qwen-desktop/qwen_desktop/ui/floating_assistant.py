"""
Floating AI Assistant Widget.
Matches the exact expanding, glowing, modern UI from the React design.
"""
from PyQt6.QtWidgets import (
    QWidget, QLineEdit, QHBoxLayout, QPushButton, QLabel, QVBoxLayout, QScrollArea,
    QApplication, QGraphicsDropShadowEffect, QFrame, QMenu
)
from PyQt6.QtCore import (
    Qt, QPropertyAnimation, QRect, QPoint, QEasingCurve, pyqtSignal, 
    QTimer, QEvent, QThread
)
from PyQt6.QtGui import (
    QColor, QPainter, QLinearGradient, QBrush, QCursor, QAction, QFont, QPalette
)
import datetime
import asyncio
from qwen_desktop.core.qwen_session_service import QwenSessionService
import uuid

from qwen_desktop.ui.components.vision_button import VisionButton
from qwen_desktop.ui.components.attach_button import AttachButton
from qwen_desktop.ui.components.send_button import SendButton
from qwen_desktop.ui.components.settings_button import SettingsButton

class APIServerWorker(QThread):
    """QThread worker to run DashScope API calls without blocking the UI."""
    chunk_received = pyqtSignal(str)
    finished_response = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, api_client, message, history):
        super().__init__()
        self.api_client = api_client
        self.message = message
        # Shallow copy of history
        self.history = list(history)
        self._full_response = ""

    def run(self):
        try:
            asyncio.run(self._stream())
        except Exception as e:
            self.error_occurred.emit(str(e))

    async def _stream(self):
        try:
            async for chunk in self.api_client.send_message(self.message, self.history):
                self._full_response += chunk
                self.chunk_received.emit(self._full_response)
            self.finished_response.emit(self._full_response)
        except Exception as e:
            self.error_occurred.emit(str(e))


class MessageBubble(QWidget):
    """A chat message bubble resembling the React design."""
    def __init__(self, text: str, sender: str, is_vision: bool = False, file_name: str = None, parent=None):
        super().__init__(parent)
        self.sender = sender
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 12, 16, 12)
        
        # Bubble Frame
        self.frame = QFrame()
        self.frame.setMaximumWidth(280)
        self.frame_layout = QVBoxLayout(self.frame)
        
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
            
        if file_name:
            attach_lbl = QLabel(f"📎 {file_name}")
            attach_lbl.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {'white' if sender=='user' else '#4b5563'}; border-bottom: 1px solid {'rgba(255,255,255,0.2)' if sender=='user' else '#e5e7eb'}; padding-bottom: 4px;")
            self.frame_layout.addWidget(attach_lbl)

        self.msg_lbl = QLabel(text)
        self.msg_lbl.setWordWrap(True)
        self.msg_lbl.setStyleSheet("background: transparent; border: none;")
        self.frame_layout.addWidget(self.msg_lbl)
        
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
        self.session_scroll.setStyleSheet("QScrollArea { border: none; border-right: 1px solid #e5e7eb; background: transparent; }")
        
        self.session_list_w = QWidget()
        # Explicit explicitly setting background to transparent stops the sharp corners from overlapping radius
        self.session_list_w.setStyleSheet("background: transparent;")
        self.session_layout = QVBoxLayout(self.session_list_w)
        self.session_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.session_layout.setContentsMargins(6, 6, 6, 6)
        self.session_layout.setSpacing(4)
        
        self.session_scroll.setWidget(self.session_list_w)
        c_layout.addWidget(self.session_scroll)
        
        # Right Panel (Chat View)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.messages_w = QWidget()
        self.messages_w.setStyleSheet("background: transparent;")
        self.msg_layout = QVBoxLayout(self.messages_w)
        self.msg_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll.setWidget(self.messages_w)
        c_layout.addWidget(self.scroll)
        
        layout.addWidget(content_w)
        
        outer_layout.addWidget(self.container)

    def populate_sessions(self, sessions, click_callback):
        # Clear old sessions
        while self.session_layout.count():
            item = self.session_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        for s in sessions:
            btn = QPushButton(f"{s['title']}\n{s.get('last_msg', '')}")
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent; color: #4b5563; text-align: left; padding: 10px;
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
        
    def add_message(self, text, sender, is_vision=False, file_name=None):
        bubble = MessageBubble(text, sender, is_vision, file_name)
        if sender == "ai":
            self._last_ai_bubble = bubble
        self.msg_layout.addWidget(bubble)
        # Scroll to bottom
        QTimer.singleShot(50, self.scroll_to_bottom)

    def update_last_message(self, text):
        if self._last_ai_bubble:
            self._last_ai_bubble.update_text(text)
            self.scroll_to_bottom()

    def scroll_to_bottom(self):
        bar = self.scroll.verticalScrollBar()
        bar.setValue(bar.maximum())


class FloatingAssistant(QWidget):
    """The main expanding button acting as the full interface."""
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        
        self.is_hovered = False
        self.is_expanded = False
        self.is_dragging = False
        self.is_vision_enabled = False
        
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
        self.move(int(screen.width() - self.collapsed_size - 40), int(screen.height() - self.collapsed_size - 40))
        
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
            
        # Hook up sessions logic
        self.load_session_clicked = lambda u: self._switch_to_session(u)
        self.history_popup.populate_sessions(self.session_service.get_all_sessions(), self.load_session_clicked)
        
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
        
        self.vision_btn = VisionButton()
        self.vision_btn.clicked.connect(self.toggle_vision)
        
        self.attach_btn = AttachButton()
        
        self.send_btn = SendButton()
        self.send_btn.clicked.connect(self.submit_message)
        
        self.settings_btn = SettingsButton()
        self.settings_btn.clicked.connect(self.toggle_auth)
        
        self.input_layout.addWidget(self.settings_btn)
        self.input_layout.addWidget(self.input_field, 1)
        self.input_layout.addWidget(self.vision_btn)
        self.input_layout.addWidget(self.attach_btn)
        self.input_layout.addWidget(self.send_btn)
        
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
            self.input_wrapper.show()
            try:
                self.anim.finished.disconnect()
            except:
                pass
            self.anim.finished.connect(self.position_history_popup)
        else:
            try:
                self.anim.finished.disconnect()
            except:
                pass
            self.anim.finished.connect(self.input_wrapper.hide)
            
        self.anim.start()

    def enterEvent(self, event):
        if not self.is_dragging and not self.is_expanded:
            self.is_hovered = True
            self.update_size(True)
        self.update()

    def leaveEvent(self, event):
        if not self.is_expanded:
            self.is_hovered = False
            self.update_size(False)
        self.update()

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
        self.update_size(self.is_expanded or self.is_hovered)
        self.update()
        
        if self.is_expanded:
            self.position_history_popup()
            self.history_popup.show()
            self.input_field.setFocus()
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
        self.is_vision_enabled = not self.is_vision_enabled
        self.vision_btn.is_green = self.is_vision_enabled
        self.input_field.setPlaceholderText("Ask with Vision..." if self.is_vision_enabled else "Ask Qwen AI...")
        self.update()
        
    def submit_message(self):
        text = self.input_field.text().strip()
        if not text: return
        
        self.messages_count += 1
        self.input_field.clear()
        
        if not self.is_expanded:
            self.toggle_expand()
            
        self.history_popup.add_message(text, "user", self.is_vision_enabled)
        
        if self.oauth and self.oauth.is_authenticated() and getattr(self, "api_client", None):
            self.last_msg_uuid = self.session_service.save_message(self.session_id, "user", text, self.last_msg_uuid)
            self._handle_api(text)
        else:
            QTimer.singleShot(400, lambda: self.history_popup.add_message(
                "Please login first.", 
                "ai"
            ))
            
    def _handle_api(self, text):
        self.history_popup.add_message("...", "ai") # Initial empty message bubble
        
        self.worker = APIServerWorker(self.api_client, text, self._chat_history)
        self.worker.chunk_received.connect(self._on_api_chunk)
        self.worker.finished_response.connect(self._on_api_finished)
        self.worker.error_occurred.connect(self._on_api_error)
        self.worker.start()
        
        # update memory
        self._chat_history.append({"role": "user", "content": text})

    def _on_api_chunk(self, chunk):
        self.history_popup.update_last_message(chunk)

    def _on_api_finished(self, full_text):
        self.history_popup.update_last_message(full_text)
        self.last_msg_uuid = self.session_service.save_message(self.session_id, "assistant", full_text, self.last_msg_uuid)
        self._chat_history.append({"role": "assistant", "content": full_text})

    def _on_api_error(self, err):
        self.history_popup.update_last_message(f"API Error: {err}")
