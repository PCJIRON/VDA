"""Floating assistant controller — main application window with chat, vision, and UIED functionality."""

import base64
import datetime
import io
import logging
import re
import uuid

from PyQt6.QtCore import Qt, QPoint, QEasingCurve, QTimer, QEvent, QVariantAnimation, QPropertyAnimation, QRect, QRectF
from PyQt6.QtGui import QColor, QPainter, QLinearGradient, QBrush, QCursor, QPixmap, QAction, QPen
from PyQt6.QtWidgets import (
    QWidget, QLineEdit, QHBoxLayout, QPushButton, QLabel, QVBoxLayout,
    QApplication, QMenu, QFileDialog,
)
from PyQt6.QtSvg import QSvgRenderer
from typing import List, Optional, Tuple

from qwen_desktop.core.session_service import SessionService
from qwen_desktop.core.vision_capture import VisionCaptureService
from qwen_desktop.core.pyautogui_executor import PyAutoGUIExecutor
from qwen_desktop.core.enhanced_executor import EnhancedExecutor
from qwen_desktop.core.auto_template_extractor import AutoTemplateExtractor
from qwen_desktop.core.default_prompt import build_system_prompt
from qwen_desktop.auth.provider_config import ProviderConfig
from qwen_desktop.core.api_client import APIClient
from qwen_desktop.core.zen_client import ZenClient
from qwen_desktop.core.memory_manager import ShortTermMemory, LongTermMemory, DailyTaskCache
from qwen_desktop.core.task_decomposer import TaskDecomposer
from qwen_desktop.core.behavior_tracker import BehaviorTracker
from qwen_desktop.core.clickers import ClickerEngine
from qwen_desktop.ui.components.vision_button import VisionButton
from qwen_desktop.ui.components.attach_button import AttachButton
from qwen_desktop.ui.components.send_button import SendButton
from qwen_desktop.ui.components.settings_button import SettingsButton
from qwen_desktop.ui.components.uied_button import UIEDButton
from qwen_desktop.ui.settings_dialog import SettingsDialog
from qwen_desktop.ui.assistant.chat_popup import ChatHistoryPopup
from qwen_desktop.ui.assistant.worker import APIServerWorker
from qwen_desktop.core.agent_manager.agent_worker import AgentWorker
from qwen_desktop.core.agent_manager.agent_manager import AgentManager
from qwen_desktop.core.tool_registry import get_registry
from qwen_desktop.ui.assistant.thinking_panel import ThinkingPanel
from qwen_desktop.ui.assistant.vision_handler import VisionHandlerMixin
from qwen_desktop.ui.assistant.uied_handler import UIEDHandlerMixin

try:
    import uiautomation as auto
    UI_AUTOMATION_AVAILABLE = True
    logging.info("[UIA] UI Automation loaded successfully")
except ImportError:
    UI_AUTOMATION_AVAILABLE = False
    logging.warning("[UIA] UI Automation not available (Windows only)")

logger = logging.getLogger(__name__)


class FloatingAssistant(VisionHandlerMixin, UIEDHandlerMixin, QWidget):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self._config = ProviderConfig(settings)

        self.is_hovered = False
        self.is_expanded = False
        self.is_dragging = False

        import os
        svg_path = os.path.join(os.path.dirname(__file__), "..", "assets", "star.svg")
        self.star_renderer = QSvgRenderer(svg_path)

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
            Qt.WindowType.SubWindow
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.resize(self.collapsed_size, self.collapsed_size)

        screen = QApplication.primaryScreen().availableGeometry()
        target_x = screen.x() + screen.width() - self.collapsed_size - 40
        target_y = screen.y() + screen.height() - self.collapsed_size - 40
        target_x = max(screen.x(), min(target_x, screen.x() + screen.width() - self.collapsed_size))
        target_y = max(screen.y(), min(target_y, screen.y() + screen.height() - self.collapsed_size))
        self.move(target_x, target_y)

        self.thinking_panel = ThinkingPanel()
        self.history_popup = ChatHistoryPopup(thinking_panel=self.thinking_panel)
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
        self._enhanced_executor = EnhancedExecutor(mode=self._pyautogui_mode)

        self._template_cache = {}
        self._template_threshold = 0.8

        self._use_ui_automation = UI_AUTOMATION_AVAILABLE

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
        self.history_popup.populate_sessions(
            self.session_service.get_all_sessions(), self.load_session_clicked
        )

        QApplication.instance().installEventFilter(self)

    def showEvent(self, event):
        super().showEvent(event)
        screen_geom = QApplication.primaryScreen().availableGeometry()
        new_x = max(screen_geom.x(), min(self.x(), screen_geom.x() + screen_geom.width() - self.width()))
        new_y = max(screen_geom.y(), min(self.y(), screen_geom.y() + screen_geom.height() - self.height()))
        if new_x != self.x() or new_y != self.y():
            self.move(new_x, new_y)

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
            except Exception as e:
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
                background-color: #151924;
                color: white;
                border: 1px solid #2A2F42;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #9333ea;
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

        self.input_wrapper.setMinimumWidth(0)
        self.input_wrapper.setMaximumWidth(self.expanded_size - self.collapsed_size)
        self.input_wrapper.hide()

        self.sparkle_wrapper = QWidget()
        self.sparkle_wrapper.setFixedSize(self.collapsed_size, self.collapsed_size)

        # Layout: input wrapper (hidden when collapsed), sparkle on right
        self.panel_container = QWidget()
        self.panel_container.setFixedWidth(0)
        self.panel_layout = QVBoxLayout(self.panel_container)
        self.panel_layout.setContentsMargins(0, 0, 0, 0)
        self.panel_layout.setSpacing(0)
        self.panel_layout.addWidget(self.input_wrapper)
        # Add container and sparkle to main layout
        self.main_layout.addWidget(self.panel_container)
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

        painter.setBrush(QBrush(QColor("#0B0F19"))) # Deep Navy background
        
        pen = QPen(QColor("#9333ea")) # Subtle purple border
        pen.setWidth(1)
        painter.setPen(pen)
        
        # Adjust rect to account for pen width
        painter.drawRoundedRect(0, 0, width - 1, height - 1, radius, radius)

        painter.setOpacity(1.0)
        
        # Calculate rect for the SVG icon
        icon_size = 32
        x_pos = float(width - self.collapsed_size / 2 - icon_size / 2)
        y_pos = float(height / 2 - icon_size / 2)
        rect = QRectF(x_pos, y_pos, float(icon_size), float(icon_size))
        
        if self.star_renderer.isValid():
            self.star_renderer.render(painter, rect)
        else:
            # Fallback
            painter.setPen(QColor("white"))
            font = self.font()
            font.setPointSize(20)
            painter.setFont(font)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "★")

    def _on_anim_step(self, val: int):
        self.setFixedSize(val, self.collapsed_size)
        new_x = self._anim_right_edge - val + 1
        self.move(new_x, self.y())
        panel_w = max(0, val - self.collapsed_size)
        self.panel_container.setFixedWidth(panel_w)

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
            self.panel_container.setFixedWidth(0)
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



    def select_files(self):
        from pathlib import Path
        import base64
        from qwen_desktop.utils.file_encoder import MAX_FILE_SIZE
        
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
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        text = f.read()
                    self.staged_files.append({"type": "file", "path": str(path), "content": text, "name": path.name})
                except Exception as e:
                    logger.error(f"Failed to read text file {path}: {e}")

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

    def _load_saved_templates_as_components(self) -> list:
        import os
        template_dir = os.path.join(
            os.path.expanduser("~"),
            ".qwen_desktop",
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

        prompt = build_system_prompt(
            screen_width=sw, screen_height=sh,
            components=components,
            vision_mode=self.is_vision_enabled,
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
        self.history_popup.add_message("Thinking\u2026", "ai")
        self.history_popup.set_thinking_status("Thinking\u2026")
        # Remember the original user text for fallback (vision may rewrite it)
        self._last_user_text = text or ""

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

        # Action-ish signals → not pure chat, let the agent plan
        action_signals = (
            "click", "open", "close", "launch", "start ", "stop ",
            "type ", "search for", "play ", "download", "install",
            "navigate to", "go to", "visit", "scroll", "drag",
            "select", "press", "save ", "delete ", "rename",
            "maximize", "minimize", "switch to", "run ", "execute",
            "browser", "tab", "window", "file", "folder",
            "youtube", "google", "gmail", "notepad", "vscode",
            "code ", "script", "command",
        )
        if any(sig in text for sig in action_signals):
            return False

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
        # skip the entire agent loop and call the LLM directly. The agent loop is
        # designed for multi-step desktop automation — running it on "hello" causes
        # a 10-iteration doom loop and a 30-second wait for no reason.
        if not vision_mode:
            if self._looks_like_chat(user_input):
                logger.info("[Worker] Chat-mode short-circuit (no agent loop) for: %s", user_input[:60])
                prompted_history = self._build_history_with_prompt(list(history))
                self._chat_history.append(
                    {"role": "user", "content": user_input}
                )
                self._launch_direct_llm(api_client, user_input, prompted_history, vision_mode=False)
                return self.worker
            else:
                logger.warning("[Worker] Desktop action blocked because Vision Mode is OFF.")
                try:
                    self.history_popup.update_last_message("❌ Error: Desktop control requires Vision Mode to be ON. Please enable Vision Mode.")
                    self.history_popup.set_thinking_status("")
                    self._set_send_mode()
                except Exception as e:
                    logger.error(f"Error updating UI for blocked vision action: {e}")
                return None

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

    def _on_agent_finished(self, results, api_client, user_text, history, vision_mode):
        """Handle agent completion — fall back to direct LLM call if no usable text."""
        formatted = self._format_results(results)
        if formatted:
            self._on_api_finished(formatted)
            return

        # Agent produced no usable text — fall back to direct LLM call for simple text responses
        logger.info("[Agent] No usable results from agent loop — falling back to direct LLM call")
        self._launch_direct_llm(api_client, user_text, history, vision_mode)

    def _launch_direct_llm(self, api_client, user_text, history, vision_mode):
        """Start a direct APIServerWorker as a fallback (no agent loop).

        The "✨ Thinking…" placeholder was already added by _handle_api (or by
        the agent worker's start), so we deliberately do NOT add a second one.
        Streamed chunks will update the existing bubble via _on_api_chunk.
        """
        direct_worker = APIServerWorker(api_client, user_text, list(history), vision_mode=vision_mode)
        direct_worker.chunk_received.connect(self._on_api_chunk)
        direct_worker.finished_response.connect(self._on_api_finished)
        direct_worker.error_occurred.connect(self._on_api_error)
        direct_worker.start()
        self.worker = direct_worker
