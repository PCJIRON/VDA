"""Floating assistant controller — main application window with chat, vision, and UIED functionality."""

import base64
import io
import logging
import os
import uuid
from typing import Optional, Tuple

from PyQt6.QtCore import (
    QEasingCurve,
    QEvent,
    QPoint,
    QPropertyAnimation,
    QRect,
    QRectF,
    Qt,
    QThread,
    QTimer,
    QVariantAnimation,
    pyqtSignal,
)
from PyQt6.QtGui import QAction, QBrush, QColor, QCursor, QPainter, QPen, QPixmap
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from vda.auth.provider_config import ProviderConfig
from vda.core.agent_manager.agent_manager import AgentManager
from vda.core.agent_manager.agent_worker import AgentWorker
from vda.core.api_client import APIClient
from vda.core.auto_template_extractor import AutoTemplateExtractor
from vda.core.behavior_tracker import BehaviorTracker
from vda.core.default_prompt import build_system_prompt
from vda.core.enhanced_executor import EnhancedExecutor
from vda.core.memory_manager import DailyTaskCache, LongTermMemory, ShortTermMemory
from vda.core.pyautogui_executor import PyAutoGUIExecutor
from vda.core.session_service import SessionService
from vda.core.tool_registry import get_registry
from vda.core.zen_client import ZenClient
from vda.ui.assistant.chat_popup import ChatHistoryPopup
from vda.ui.assistant.thinking_panel import ThinkingPanel
from vda.ui.assistant.uied_handler import UIEDHandlerMixin
from vda.ui.assistant.vision_handler import VisionHandlerMixin
from vda.ui.assistant.worker import APIServerWorker
from vda.ui.components.chat_panel import ChatPanel
from vda.ui.components.floating_widget import FloatingWidget
from vda.ui.components.settings_modal import SettingsModal
from vda.ui.components.stop_button import StopButton

UI_AUTOMATION_SUPPORTED = os.name == "nt"
auto = None

logger = logging.getLogger(__name__)


class AgentDWorker(QThread):
    """Minimal QThread that runs the opencode Go agent and emits streaming events.

    Used for non-vision (text-only) agent tasks. Signals replace the
    full AgentWorker signal set with a simpler one since agentd handles
    tool execution internally.

    Signals:
        text_delta: Streaming text content from the agent.
        tool_call: (tool_name, tool_input)
        tool_result: (tool_name, content, is_error)
        finished: (final content string)
        error_occurred: (error message)
    """

    text_delta = pyqtSignal(str)
    tool_call = pyqtSignal(str, str)
    tool_result = pyqtSignal(str, str, bool)
    finished = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(
        self,
        task: str,
        provider: str,
        model: str,
        api_key: str,
        base_url: str,
        working_dir: str = "",
        system_prompt: str = "",
    ) -> None:
        super().__init__()
        self._task = task
        self._provider = provider
        self._model = model
        self._api_key = api_key
        self._base_url = base_url
        self._working_dir = working_dir or os.path.expanduser("~")
        self._system_prompt = system_prompt

    def run(self) -> None:
        from vda.opencode_bridge import run_agentd

        full_content = ""
        try:
            for event in run_agentd(
                task=self._task,
                provider=self._provider,
                model=self._model,
                api_key=self._api_key,
                base_url=self._base_url,
                working_dir=self._working_dir,
                system_prompt=self._system_prompt,
            ):
                etype = event.get("type", "")
                if etype == "text":
                    delta = event.get("content", "")
                    if delta:
                        self.text_delta.emit(delta)
                        full_content += delta
                elif etype == "tool_call":
                    self.tool_call.emit(
                        event.get("tool_name", ""),
                        event.get("tool_input", ""),
                    )
                elif etype == "tool_result":
                    self.tool_result.emit(
                        event.get("tool_name", ""),
                        event.get("tool_result", ""),
                        event.get("is_error", False),
                    )
                elif etype == "error":
                    self.error_occurred.emit(event.get("content", "Unknown error"))
                elif etype == "done":
                    content = event.get("content", "")
                    if content and content != full_content:
                        delta = content[len(full_content):] if content.startswith(full_content) else content
                        self.text_delta.emit(delta)
                        full_content = content
                    self.finished.emit(full_content)
                    return

            # If we exited without a done event, emit finished with whatever we have
            if not self.isInterruptionRequested():
                self.finished.emit(full_content)
        except Exception as e:
            logger.error("[AgentDWorker] Error: %s", e, exc_info=True)
            self.error_occurred.emit(str(e))


VDA_SYSTEM_PROMPT = """You are VDA (Voice-Driven Desktop Agent), a desktop AI assistant powered by the OpenCode engine. You control the computer to accomplish tasks — you can search files, edit files, run commands, browse the web, and more.

Your goal is to understand what the user wants and use your tools to make it happen. Be thorough and precise. When you're not sure about something, use your tools to investigate rather than guessing.

You operate anywhere on the user's system, not just inside a specific project folder."""


class _ChatPopupAdapter:
    """Adapter: wraps ChatPanel + ThinkingPanel with the old ChatHistoryPopup API.
    Allows vision_handler.py and uied_handler.py to work unchanged.
    """
    def __init__(self, chat_panel: ChatPanel, thinking_panel: ThinkingPanel):
        self._chat = chat_panel
        self._thinking = thinking_panel
        self._visible = False
        self._geometry_rect = None

        # Staging (file attachments) — kept as no-op for backward compat
        class _StagingScroll:
            def show(self): pass
            def hide(self): pass
        class _StagingLayout:
            def count(self): return 0
            def takeAt(self, i): return None
            def addWidget(self, w): pass
            def addStretch(self): pass
        self.staging_scroll = _StagingScroll()
        self.staging_layout = _StagingLayout()
        self.close_btn = type("_Btn", (), {"clicked": type("_Sig", (), {"connect": lambda s, fn: None})()})()
        self.new_chat_clicked = None

    def add_message(self, text: str, sender: str, attachments=None):
        self._chat.add_message(text, is_user=(sender == "user"))

    def update_last_message(self, text: str):
        self._chat._update_last_text(text)

    def set_thinking_status(self, text: str):
        self._thinking.set_thinking_status(text) if hasattr(self._thinking, "set_thinking_status") else None

    def set_vision_status(self, status: str):
        self._chat.add_message(status, is_user=False)

    def clear_chat(self):
        self._chat._clear_messages()
        self._chat._show_empty_state()

    def show(self):
        self._visible = True
        self._chat.show()

    def hide(self):
        self._visible = False
        self._chat.hide()

    def isVisible(self):
        return self._visible

    def geometry(self):
        return self._geometry_rect or self._chat.geometry() if hasattr(self._chat, "geometry") else type("_R", (), {"contains": lambda s, p: False})()

    def width(self):
        return 460

    def height(self):
        return 500

    def move(self, x, y):
        pass

    def populate_sessions(self, sessions, click_callback):
        self._chat.set_history_items([s.title if hasattr(s, "title") else str(s) for s in sessions])


class FloatingAssistant(VisionHandlerMixin, UIEDHandlerMixin, QWidget):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self._config = ProviderConfig(settings)

        self.is_vision_enabled = False

        self._pyautogui_mode = PyAutoGUIExecutor.ASK_FIRST
        self._last_vision_w = 1920
        self._last_vision_h = 1080

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.resize(64, 64)

        # Position at bottom-right of primary screen
        screen = QApplication.primaryScreen().availableGeometry()
        target_x = screen.x() + screen.width() - 80
        target_y = screen.y() + screen.height() - 80
        self.move(target_x, target_y)
        # Make sure it's above all other windows
        self.raise_()
        self.activateWindow()

        self.thinking_panel = ThinkingPanel()

        self._setup_ui()

        # Adapter: maintain backward-compatible API for vision/uied handlers
        self._chat_visible = False
        self._is_sending = False
        self._staging_files_visible = False
        self.history_popup = _ChatPopupAdapter(self.chat_panel, self.thinking_panel)
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
        self._enhanced_executor = EnhancedExecutor(mode=self._pyautogui_mode)

        self._template_cache = {}
        self._template_threshold = 0.8

        self._use_ui_automation = UI_AUTOMATION_SUPPORTED

        self._uied_overlay = None
        self._uied_components = []
        self._is_uied_detecting = False

        self._thinking_text = ""
        self._stm = ShortTermMemory()
        self._ltm = LongTermMemory()
        self._daily_cache = DailyTaskCache()
        self._behavior = BehaviorTracker()
        self._auto_template = AutoTemplateExtractor()
        self._task_decomposer = None

        self.load_session_clicked = lambda u: self._switch_to_session(u)

        QApplication.instance().installEventFilter(self)

    def showEvent(self, event):
        super().showEvent(event)
        self.raise_()
        screen_geom = QApplication.primaryScreen().availableGeometry()
        new_x = max(screen_geom.x(), min(self.x(), screen_geom.x() + screen_geom.width() - self.width()))
        new_y = max(screen_geom.y(), min(self.y(), screen_geom.y() + screen_geom.height() - self.height()))
        if new_x != self.x() or new_y != self.y():
            self.move(new_x, new_y)

    def _find_with_ui_automation(self, target_name: str) -> Optional[Tuple[int, int, str]]:
        if not self._use_ui_automation:
            return None
        global auto
        if auto is None:
            try:
                import uiautomation as _auto
                auto = _auto
                logger.info("[UIA] UI Automation loaded successfully (lazy)")
            except Exception as e:
                logger.warning(f"[UIA] UI Automation load failed: {e}")
                self._use_ui_automation = False
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
                logger.exception("Error while scanning taskbar UI elements")
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
            if self._chat_visible:
                bar_contains = self.geometry().contains(click_pos)
                popup_contains = self.history_popup.isVisible() and self.history_popup.geometry().contains(click_pos)
                if not bar_contains and not popup_contains:
                    self.toggle_chat()
                    return False
        return super().eventFilter(obj, event)

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # FloatingWidget (pill-shaped input bar)
        self.floating_widget = FloatingWidget()
        self.floating_widget.send_requested.connect(self._on_new_widget_send)
        self.floating_widget.settings_requested.connect(self.open_settings)
        self.floating_widget.voice_requested.connect(self.toggle_voice)
        self.floating_widget.vision_requested.connect(self.toggle_vision)
        self.floating_widget.crop_requested.connect(self.trigger_uied_detection)
        self.main_layout.addWidget(self.floating_widget)

        # ChatPanel - NOT in layout, positioned as popup above the widget
        self.chat_panel = ChatPanel(self)
        self.chat_panel.setVisible(False)
        self.chat_panel.close_requested.connect(self.toggle_chat)
        self.chat_panel.new_chat_requested.connect(self.start_new_session)

        self._chat_visible = False

    def _on_new_widget_send(self, text: str):
        self.submit_message(text)

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

    def toggle_chat(self):
        """Show/hide the chat panel above the floating widget."""
        self._chat_visible = not self._chat_visible
        self.chat_panel.setVisible(self._chat_visible)
        if self._chat_visible:
            self._position_chat_panel()
        self.raise_()

    def _position_chat_panel(self):
        """Position the ChatPanel as a popup above the floating widget."""
        screen = QApplication.primaryScreen().availableGeometry()
        panel_w = self.chat_panel.WIDTH
        panel_h = self.chat_panel.HEIGHT

        # Center above the widget
        cx = self.x() + self.floating_widget.width() // 2
        px = cx - panel_w // 2
        # Show above the window
        py = self.y() - panel_h - 12

        # Clamp to screen
        px = max(screen.left() + 4, min(px, screen.right() - panel_w - 4))
        py = max(screen.top() + 4, py)

        self.chat_panel.move(px, py)

    def toggle_voice(self):
        self.history_popup.add_message("Voice Input is currently simulated.", "ai")

    def _switch_to_session(self, session_id):
        sid, hist, last_uuid = self.session_service.load_session(session_id)
        self.session_id = sid
        self._chat_history = hist
        self.last_msg_uuid = last_uuid

        self.history_popup.clear_chat()
        for msg in self._chat_history:
            self.history_popup.add_message(msg["content"], "user" if msg["role"] == "user" else "ai")

    def start_new_session(self):
        """Reset the conversation context for a new session."""
        self.session_id = str(uuid.uuid4())
        self._chat_history = []
        self.last_msg_uuid = None
        self.history_popup.clear_chat()
        self.staged_files = []
        if hasattr(self, 'staged_widgets'):
            for w in self.staged_widgets:
                w.deleteLater()
            self.staged_widgets = []
        self.history_popup.staging_scroll.hide()

    def open_settings(self):
        dialog = SettingsModal(self)
        if dialog.exec():
            data = dialog.get_data()
            self.settings["provider"] = data.get("provider", "OpenAI")
            self.settings["api_model"] = data.get("model", "gpt-4o")
            if data.get("custom_model"):
                self.settings["api_model"] = data["custom_model"]
            self.settings["api_key"] = data.get("api_key", "")
            self._config = ProviderConfig(self.settings)
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



    def select_files(self):
        import base64
        from pathlib import Path

        from vda.utils.file_encoder import MAX_FILE_SIZE

        files, _ = QFileDialog.getOpenFileNames(self, "Select Files", "", "All Files (*);;Images (*.png *.jpg *.jpeg *.bmp)")
        if not files:
            return

        for file_path in files:
            path = Path(file_path)
            content_type = "image" if path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp', '.gif'] else "file"

            if path.stat().st_size > MAX_FILE_SIZE:
                logger.warning(f"File {path} exceeds size limit and will be skipped.")
                continue

            if content_type == "image":
                try:
                    with open(path, "rb") as f:
                        b64 = base64.b64encode(f.read()).decode('utf-8')
                    self.staged_files.append({"type": "image", "path": str(path), "base64": b64, "name": path.name, "mime": f"image/{path.suffix[1:]}"})
                except Exception as e:
                    logger.error(f"Failed to read image file {path}: {e}")
            else:
                try:
                    with open(path, encoding="utf-8", errors="ignore") as f:
                        text = f.read()
                    self.staged_files.append({"type": "file", "path": str(path), "content": text, "name": path.name})
                except Exception as e:
                    logger.error(f"Failed to read text file {path}: {e}")

        self.update_staging_ui()

        if self.staged_files and not self._chat_visible:
            self.toggle_chat()

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

    def submit_message(self, text=None):
        if text is None:
            return
        text = text.strip()
        if not text and not self.staged_files:
            return

        if not text and self.staged_files:
            text = "Please refer to the attached files."

        self.messages_count += 1

        att_copy = self.staged_files.copy()
        self.staged_files.clear()
        self.update_staging_ui()

        self.history_popup.add_message(text, "user", attachments=att_copy)

        if getattr(self, "api_client", None) and self._config.is_configured():
            self.last_msg_uuid = self.session_service.save_message(self.session_id, "user", text, attachments=att_copy, parent_uuid=self.last_msg_uuid)
            self._handle_api(text, att_copy)
        else:
            QTimer.singleShot(400, lambda: self.history_popup.add_message("Please configure API key in Settings first.", "ai"))

    def _load_saved_templates_as_components(self) -> list:
        import os
        template_dir = os.path.join(
            os.path.expanduser("~"),
            ".vda",
            "uied_templates"
        )
        if not os.path.exists(template_dir):
            return []

        components = []
        try:
            template_files = [f for f in os.listdir(template_dir) if f.endswith('.png')]
            for f in template_files:
                name_without_ext = f.replace('.png', '')
                parts = name_without_ext.split('_')

                comp_type = "other"
                if len(parts) > 1:
                    possible_type = parts[-1].lower()
                    if possible_type in ['icon', 'button', 'text', 'input', 'checkbox', 'logo', 'other']:
                        comp_type = possible_type
                        parts = parts[:-1]

                start_idx = 0
                while start_idx < len(parts):
                    p = parts[start_idx].lower()
                    if p in ['comp', 'user'] or (p.isalnum() and any(c.isdigit() for c in p)):
                        start_idx += 1
                    else:
                        break

                label_parts = parts[start_idx:]
                if not label_parts:
                    label = " ".join(parts)
                else:
                    label = " ".join(label_parts)

                label = label.replace('_', ' ').replace('-', ' ').strip()

                components.append({
                    "label": label,
                    "component_type": comp_type,
                    "x": "unknown",
                    "y": "unknown"
                })
        except Exception as e:
            logger.error(f"Error loading saved templates: {e}", exc_info=True)

        return components

    def _take_screenshot_b64(self) -> str:
        """Capture the desktop and return a base64 JPEG string (no data: prefix).

        Used by AgentManager as the screenshot_fn injection. The image is
        resized to 1280x720 and saved as JPEG quality 80 to keep the
        per-step LLM call fast (smaller image = fewer tokens + faster
        upload than full-screen PNG).

        Returns:
            Base64-encoded image string. Empty string on failure.
        """
        try:
            import pyautogui
            from PIL import Image

            img = pyautogui.screenshot()
            # Resize to a vision-friendly resolution
            try:
                img = img.resize((1280, 720), Image.Resampling.LANCZOS)
            except AttributeError:
                img = img.resize((1280, 720), Image.LANCZOS)

            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=80, optimize=True)
            return base64.b64encode(buf.getvalue()).decode()
        except Exception as e:
            logger.warning(f"Screenshot capture failed: {e}")
            return ""

    def _build_history_with_prompt(self, history: list) -> list:
        try:
            import pyautogui
            sw, sh = pyautogui.size()
        except Exception:
            sw, sh = 1920, 1080

        saved_components = self._load_saved_templates_as_components()
        components = saved_components + self._uied_components if self._uied_components else saved_components

        skills_content = ""
        skills_path = self.settings.get("skills_md_path")
        if skills_path and os.path.exists(skills_path):
            try:
                with open(skills_path, encoding="utf-8") as f:
                    skills_content = f.read()
            except Exception as e:
                logger.warning(f"Failed to read skills file: {e}")

        prompt = build_system_prompt(
            screen_width=sw, screen_height=sh,
            components=components,
            vision_mode=self.is_vision_enabled,
            skills_content=skills_content,
        )
        has_system = any(m.get("role") == "system" for m in history)
        if not has_system:
            return [{"role": "system", "content": prompt}] + list(history)
        return list(history)

    def _format_results(self, results):
        """Combine tool execution results into a readable AI response.

        Args:
            results: List of step result dictionaries from AgentWorker.

        Returns:
            A string summarizing the outcome, or None if no usable text was produced.
        """
        if not results:
            return None

        # Extract the actual result text from each step (skip empty/None)
        texts = []
        for r in results:
            if not isinstance(r, dict):
                continue
            outcome = r.get("result", "")
            if outcome and isinstance(outcome, str) and outcome.strip():
                texts.append(outcome.strip())

        if not texts:
            return None

        return "\n\n".join(texts)

    def _handle_api(self, text, attachments):
        self._set_stop_mode()
        self.history_popup.add_message("Thinking\u2026", "ai")
        self.history_popup.set_thinking_status("Thinking\u2026")
        # Remember the original user text for fallback (vision may rewrite it)
        self._last_user_text = text or ""

        content_payload = []
        if text:
            content_payload.append({"type": "text", "text": text})

        if self.is_vision_enabled:
            try:
                import base64
                import io

                import pyautogui
                from PIL import Image

                sw, sh = pyautogui.size()
                mx, my = pyautogui.position()
                img = pyautogui.screenshot()
                img_w, img_h = img.size

                self._last_screen_resolution = (sw, sh)
                self._last_screenshot_size = (img_w, img_h)

                if sw > 800:
                    try:
                        img = img.resize((800, int(sh * 800 / sw)), Image.Resampling.LANCZOS)
                    except AttributeError:
                        img = img.resize((800, int(sh * 800 / sw)), Image.LANCZOS)

                img = img.convert("RGB")
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=65, optimize=True)
                b64 = base64.b64encode(buf.getvalue()).decode()

                logger.info(f"Vision screenshot: {img.width}x{img.height} -> Screen: {sw}x{sh}")

                vision_prompt = f"""
[USER REQUEST]
"{text if text else 'Interact with the element near the mouse cursor'}"

Current mouse position: ({mx}, {my}) on {sw}x{sh} screen

[OUTPUT FORMAT - CRITICAL]
Respond ONLY in this JSON format:
{{
  "action": "click",
  "target_name": "target name from the Component Collection, or 'No template found'",
  "target": [x, y],
  "confidence": 0.95,
  "description": "Brief description of what you found"
}}

The coordinates in `target` must be absolute pixel coordinates [x, y] on {sw}x{sh} screen.
"""
                content_payload = [
                    {"type": "text", "text": vision_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
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

        prompted_history = self._build_history_with_prompt(self._chat_history)
        self.worker = self._create_worker(
            self.api_client,
            content_payload if len(content_payload) > 1 else text,
            prompted_history,
            vision_mode=self.is_vision_enabled,
        )

        self._chat_history.append({"role": "user", "content": content_payload if len(content_payload) > 1 else text})

    def _on_api_chunk(self, chunk):
        try:
            self.history_popup.update_last_message(chunk)
        except Exception as e:
            logger.error(f"[UI] _on_api_chunk error: {e}", exc_info=True)

    def _on_api_finished(self, full_text):
        try:
            self._set_send_mode()
            self.history_popup.set_thinking_status("")
            self.history_popup.update_last_message(full_text)
            self.last_msg_uuid = self.session_service.save_message(
                self.session_id, "assistant", full_text, parent_uuid=self.last_msg_uuid
            )
            self._chat_history.append({"role": "assistant", "content": full_text})
        except Exception as e:
            logger.error(f"[UI] _on_api_finished error: {e}", exc_info=True)

        if '\"action\"' in full_text and ('\"target_name\"' in full_text or '\"description\"' in full_text or '\"target\"' in full_text):
            logger.info("LLM returned action with target - triggering UIED execution")
            QTimer.singleShot(500, lambda: self._execute_uied_from_llm(full_text))

    def _on_api_error(self, err):
        # If the agent loop failed (max iterations, doom loop, safety limit, etc.),
        # the user is likely just chatting — fall back to a direct LLM call so they
        # get a real response instead of an error string.
        agent_failure_markers = (
            "max iterations",
            "safety limit",
            "agent loop",
            "unknown error",
        )
        is_agent_failure = any(m in (err or "").lower() for m in agent_failure_markers)

        if is_agent_failure and getattr(self, "_last_user_text", ""):
            logger.info(
                "[UI] Agent loop failed (%s) — falling back to direct LLM call for: %s",
                err, self._last_user_text[:60],
            )
            try:
                # Remove the "API Error: ..." text we are about to overwrite
                self.history_popup.update_last_message("")
            except Exception:
                pass
            self._launch_direct_llm(
                self.api_client,
                self._last_user_text,
                list(self._chat_history),
                vision_mode=self.is_vision_enabled,
            )
            return

        try:
            self._set_send_mode()
            self.history_popup.set_thinking_status("")
            self.history_popup.update_last_message(f"API Error: {err}")
        except Exception as e:
            logger.error(f"[UI] _on_api_error error: {e}", exc_info=True)

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

    @staticmethod
    def _looks_like_chat(user_text: str) -> bool:
        """Heuristic: is this message pure chat (no desktop action needed)?

        Used to short-circuit the agent loop and answer in a single LLM call.
        We are deliberately conservative — if there's any chance the user wants
        a desktop action, return False and let the agent loop handle it.
        """
        text = (user_text or "").strip().lower()
        if not text:
            return True

        # Action-ish signals → not pure chat, let the agent plan
        action_signals = (
            "click", "open", "close", "launch", "start ", "stop ",
            "type ", "search for", "search", "find", "research", "lookup", "look up",
            "play ", "download", "install",
            "navigate to", "go to", "visit", "scroll", "drag",
            "select", "press", "save ", "delete ", "rename",
            "maximize", "minimize", "switch to", "run ", "execute",
            "browser", "tab", "window", "file", "folder",
            "youtube", "google", "gmail", "notepad", "vscode",
            "code ", "script", "command",
            # Hindi/Hinglish keywords
            "karo", "kholo", "chalao", "dhundo", "search karo", "open karo", "run karo",
        )
        if any(sig in text for sig in action_signals):
            return False

        chat_only_signals = (
            "hello", "hi ", "hi,", "hey", "namaste", "namaskar",
            "thanks", "thank you", "bye", "goodbye",
            "how are you", "what's up", "kaise ho", "kya haal",
            "who are you", "what can you do", "tell me about",
            "explain", "what is", "what are", "why", "how does",
            "summarize", "translate", "meaning of",
        )
        if any(sig in text for sig in chat_only_signals):
            return True

        # Short messages without action verbs are usually chat
        if len(text.split()) <= 8:
            return True

        # Long messages without action signals: treat as chat (questions etc.)
        return True

    def _create_worker(self, api_client, message, history, vision_mode=False):
        # Extract the user text from whatever the caller passed in.
        #
        # When the user types in chat (vision ON or OFF), message is a
        # plain string → use it directly.
        #
        # When vision mode is ON, `message` is a list of content blocks:
        #   [{"type": "text", "text": vision_prompt}, {"type": "image_url"}]
        # The vision_prompt contains output format instructions that should
        # NOT be passed as the agent's user_input — that would create a
        # double-layered prompt when the agent wraps it in 'USER TASK:'.
        #
        # Instead, use the ORIGINAL clean user text from _last_user_text.
        # If that's not set (e.g. vision hotkey trigger, not user typing),
        # fall back to extracting from the content payload.
        if isinstance(message, str):
            user_input = message
        elif isinstance(message, list):
            original = getattr(self, "_last_user_text", "")
            if original:
                user_input = original
            else:
                # Fallback: vision hotkey trigger — extract text from payload
                user_input = "".join(
                    block.get("text", "")
                    for block in message
                    if isinstance(block, dict) and block.get("type") == "text"
                )
        else:
            user_input = ""
        logger.info(
            "[WORKER-INIT] message type=%s vision=%s user_input=%r",
            type(message).__name__,
            vision_mode,
            user_input[:120],
        )

        # Short-circuit: when vision is OFF and the message looks like pure chat,
        # skip the entire agent loop and call the LLM directly.
        if not vision_mode and self._looks_like_chat(user_input):
            logger.info("[Worker] Chat-mode short-circuit (no agent loop) for: %s", user_input[:60])
            prompted_history = self._build_history_with_prompt(list(history))
            self._chat_history.append(
                {"role": "user", "content": user_input}
            )
            self._launch_direct_llm(api_client, user_input, prompted_history, vision_mode=False)
            return self.worker

        # Non-vision text tasks → use opencode Go agent directly
        if not vision_mode:
            logger.info("[Worker] Non-vision task -> routing to opencode agentd: %s", user_input[:60])
            return self._launch_agentd_worker(user_input)

        # Build AgentManager and wrap it in AgentWorker for step‑by‑step UI updates
        # Inject a screenshot callable so the agent can grab a fresh
        # screenshot on every PLAN iteration (re-plan-per-step design).
        # Also pass the EnhancedExecutor so vision actions (click/type/
        # scroll) can be executed directly without going through the
        # generic tool registry (which only knows tool names like 'uied').
        saved_components = self._load_saved_templates_as_components()
        all_components = saved_components + self._uied_components if self._uied_components else saved_components

        agent_manager = AgentManager(
            api_client,
            get_registry(),
            self.settings,
            screenshot_fn=self._take_screenshot_b64,
            vision_executor=self._enhanced_executor,
            components=all_components,
            vision_mode=vision_mode,
        )
        # Attach session info for optional compaction signals
        agent_manager.session_service = self.session_service
        agent_manager._session_id = self.session_id
        worker = AgentWorker(agent_manager, user_input)
        # Connect AgentWorker signals to ThinkingPanel UI
        worker.plan_created.connect(self.thinking_panel.set_plan)
        worker.step_started.connect(lambda label, desc: self.thinking_panel.add_step(label, desc))
        worker.step_completed.connect(lambda label, status, result: self.thinking_panel.update_step(label, "success", result))
        worker.step_failed.connect(lambda label, err: self.thinking_panel.update_step(label, "failed", err))
        worker.doom_loop_detected.connect(self.thinking_panel.show_doom_loop)
        worker.permission_required.connect(self.thinking_panel.show_permission_request)
        worker.tool_executed.connect(self._on_tool_executed)
        worker.subagent_activity.connect(self._on_subagent_step)
        worker.error_occurred.connect(self._on_api_error)
        # When agent finishes, format results. If results are empty, fall back to direct LLM call.
        # Build a clean history for the fallback that contains the user's original text (not the vision payload)
        fallback_history = [m for m in list(history) if m.get("role") != "user"]
        fallback_history.append({"role": "user", "content": user_input})
        worker.finished.connect(
            lambda results: self._on_agent_finished(results, api_client, user_input, fallback_history, vision_mode)
        )
        # Connect resume/abort from panel to worker actions
        self.thinking_panel.resume_requested.connect(worker.resume_from_doom_loop)
        self.thinking_panel.abort_requested.connect(worker.abort_agent)
        self.thinking_panel.permission_response.connect(lambda tool, allowed: worker.handle_permission_response(tool, allowed))
        worker.start()
        return worker

    def _on_agent_finished(self, final_output, api_client, user_text, history, vision_mode):
        """Handle agent completion — fall back to direct LLM call if no usable text."""
        self.history_popup.set_thinking_status("")
        if isinstance(final_output, dict) and final_output.get("summary"):
            summary = final_output.get("summary")
            self._on_api_finished(summary)
            return

        # Legacy fallback if it's a list or dict with just raw results
        if isinstance(final_output, dict):
            results = final_output.get("results")
        else:
            results = final_output
        formatted = self._format_results(results)
        if formatted:
            self._on_api_finished(formatted)
            return

        # Agent produced no usable text — fall back to direct LLM call for simple text responses
        logger.info("[Agent] No usable results from agent loop — falling back to direct LLM call")
        self._launch_direct_llm(api_client, user_text, history, vision_mode)

    def _on_tool_executed(self, tool_name, args, result, success):
        """Handle tool execution signal by updating the thinking status (OpenCode style)."""
        status_icon = "✅" if success else "❌"

        if tool_name == "terminal":
            cmd = args.get("command", "")
            if len(cmd) > 30: cmd = cmd[:27] + "..."
            status = f"Running shell: {cmd} {status_icon}"
        elif tool_name == "web_search":
            query = args.get("query", "")
            status = f"Searching web: {query} {status_icon}"
        elif tool_name == "web_fetch":
            url = args.get("url", "")
            status = f"Fetching page: {url} {status_icon}"
        elif tool_name in ("file_read", "file_write", "file_glob", "file_grep"):
            path = args.get("filepath", args.get("pattern", args.get("query", "")))
            status = f"File op ({tool_name}): {path} {status_icon}"
        elif tool_name == "voice":
            status = f"Speaking... {status_icon}"
        elif tool_name == "agent":
            prompt = args.get("prompt", "")
            if len(prompt) > 30: prompt = prompt[:27] + "..."
            status = f"Sub-agent: {prompt} {status_icon}"
        else:
            status = f"Using {tool_name}... {status_icon}"

        self.history_popup.set_thinking_status(status)

    def _on_subagent_step(self, tool_name: str, args: dict, status: str, detail: str):
        """Show sub-agent activity in the ThinkingPanel and header status."""
        if status == "started":
            if tool_name == "web_search":
                query = args.get("query", "")
                label = f"🔍 Sub: {query[:40]}"
            elif tool_name == "web_fetch":
                url = args.get("url", "")
                label = f"📄 Sub: {url[:40]}"
            else:
                label = f"⚙ Sub: {tool_name}"
            self.thinking_panel.add_step(label, f"Sub-agent using {tool_name}")
            self.history_popup.set_thinking_status(label)
        elif status == "completed":
            self.history_popup.set_thinking_status(f"✅ Sub-agent step done")
        elif status == "failed":
            self.history_popup.set_thinking_status(f"❌ Sub-agent step failed")

    def _launch_agentd_worker(self, user_input: str):
        """Launch opencode Go agent for non-vision text tasks.

        Creates AgentDWorker, connects signals to UI, and starts it.
        Uses home directory as global scope so tools can access
        the entire desktop, not just the VDA project folder.
        """
        provider_cfg = ProviderConfig(self.settings)
        worker = AgentDWorker(
            task=user_input,
            provider=provider_cfg.get_provider_id(),
            model=self.settings.get("api_model", ""),
            api_key=provider_cfg.get_api_key(),
            base_url=provider_cfg.get_base_url(),
            working_dir=os.path.expanduser("~"),
            system_prompt=VDA_SYSTEM_PROMPT,
        )
        self._set_stop_mode()
        self.history_popup.add_message("", "ai")
        self.history_popup.set_thinking_status("Thinking...")
        worker.text_delta.connect(self._on_api_chunk)
        worker.tool_call.connect(lambda name, inp: self.thinking_panel.add_step(name, inp[:100]))
        worker.tool_result.connect(lambda name, content, err: self.thinking_panel.update_step(
            name, "error" if err else "success", content[:200],
        ))
        worker.error_occurred.connect(self._on_api_error)
        worker.finished.connect(self._on_api_finished)
        worker.start()
        self.worker = worker
        return worker

    def _launch_direct_llm(self, api_client, user_text, history, vision_mode):
        """Start a direct APIServerWorker as a fallback (no agent loop).

        The "✨ Thinking…" placeholder was already added by _handle_api (or by
        the agent worker's start), so we deliberately do NOT add a second one.
        Streamed chunks will update the existing bubble via _on_api_chunk.
        """
        self._set_stop_mode()
        direct_worker = APIServerWorker(api_client, user_text, list(history), vision_mode=vision_mode)
        direct_worker.chunk_received.connect(self._on_api_chunk)
        direct_worker.finished_response.connect(self._on_api_finished)
        direct_worker.error_occurred.connect(self._on_api_error)
        direct_worker.start()
        self.worker = direct_worker
