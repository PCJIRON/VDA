"""UIED overlay widget – full‑screen editor for UI element detection.

The widget displays a translucent dark background, shows existing components as
colored boxes, lets the user draw new boxes, move/resize them, edit labels, and
delete components. It emits signals that the assistant UI consumes.
"""

import logging
from typing import List, Dict

from PyQt6.QtWidgets import (
    QWidget,
    QApplication,
    QGraphicsDropShadowEffect,
)
from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush, QFont, QCursor, QKeyEvent, QMouseEvent, QPaintEvent

# Local imports – sibling modules in this package
from .label_editor import LabelEditorDialog
from .toolbar import DraggableToolbar

logger = logging.getLogger(__name__)


class UIEDOverlayWidget(QWidget):
    """Full‑screen overlay with Figma‑style toolbar.

    Signals:
        component_edited(int, str, str) – (index, new_label, new_type)
        component_added(int, int, int, int, str, str) – (x, y, w, h, label, type)
        component_deleted(int) – index of removed component
        component_moved(int, int, int) – (index, new_x, new_y)
        component_resized(int, int, int, int, int) – (index, new_x, new_y, new_w, new_h)
        close_requested – toolbar Done/Exit pressed
    """

    component_edited = pyqtSignal(int, str, str)
    component_added = pyqtSignal(int, int, int, int, str, str)
    component_deleted = pyqtSignal(int)
    component_moved = pyqtSignal(int, int, int)
    component_resized = pyqtSignal(int, int, int, int, int)
    close_requested = pyqtSignal()

    RESIZE_HANDLE_SIZE = 10

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        # Cover the entire primary screen
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        self.screen_origin = screen.topLeft()
        logger.info(
            f"UIED Overlay v2 initialized - Screen: {screen.x()}, {screen.y()}, {screen.width()}x{screen.height()}"
        )

        self.components: List[Dict] = []
        self.hovered_index = -1
        self.hovered_resize_handle = -1
        self.selected_index = -1

        # Tool state
        self.current_tool = "move"
        # Interaction state flags
        self.is_drawing = False
        self.is_dragging = False
        self.is_resizing = False
        self.draw_start = QPoint()
        self.draw_current = QPoint()
        self.drag_component_index = -1
        self.drag_offset = QPoint()
        self.resize_component_index = -1
        self.resize_start_rect = QRect()

        self.setMouseTracking(True)

        # Toolbar – emits tool change and Done/Exit signals
        self.toolbar = DraggableToolbar(self)
        self.toolbar.tool_changed.connect(self._on_tool_changed)
        self.toolbar.done_clicked.connect(self.close_requested.emit)
        self.toolbar.exit_clicked.connect(self.close_requested.emit)
        self.toolbar.show()

        logger.info("UIED Overlay v2 initialized")

    # ---------------------------------------------------------------------
    # Toolbar handling
    # ---------------------------------------------------------------------
    def _on_tool_changed(self, tool: str):
        """React to toolbar tool changes."""
        self.current_tool = tool
        self.setCursor(self._get_tool_cursor())
        logger.info(f"Tool changed to: {tool}")

    def _get_tool_cursor(self) -> Qt.CursorShape:
        """Return a cursor appropriate for the active tool."""
        if self.current_tool == "move":
            return Qt.CursorShape.OpenHandCursor
        if self.current_tool == "box":
            return Qt.CursorShape.CrossCursor
        if self.current_tool == "delete":
            return Qt.CursorShape.ForbiddenCursor
        return Qt.CursorShape.ArrowCursor

    # ---------------------------------------------------------------------
    # Component list management
    # ---------------------------------------------------------------------
    def set_components(self, components: List[Dict]):
        self.components = components
        self.update()

    # ---------------------------------------------------------------------
    # Painting helpers
    # ---------------------------------------------------------------------
    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Dim the background
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))
        # Draw each component box
        for i, comp in enumerate(self.components):
            self._draw_component(painter, i, comp)
        # Draw interaction rectangle (drawing new box or resizing)
        if self.is_drawing or self.is_resizing:
            self._draw_interaction_rect(painter)
        # Draw instruction panel on the side
        self._draw_instructions(painter)

    def _draw_component(self, painter: QPainter, index: int, comp: Dict):
        x, y, w, h = comp.get("x", 0), comp.get("y", 0), comp.get("width", 0), comp.get("height", 0)
        label = comp.get("label", "Unknown")
        comp_type = comp.get("component_type", "other")
        rect = QRect(x, y, w, h)
        # Choose colours based on state
        if index == self.selected_index:
            border_color = QColor("#00ff00")
            fill_color = QColor(0, 255, 0, 40)
            border_width = 4
        elif index == self.hovered_index:
            border_color = QColor("#ffff00")
            fill_color = QColor(255, 255, 0, 60)
            border_width = 4
        else:
            border_color = QColor("#ff0000")
            fill_color = QColor(255, 0, 0, 20)
            border_width = 2
        painter.setBrush(QBrush(fill_color))
        painter.setPen(QPen(border_color, border_width))
        painter.drawRect(rect)
        # Resize handles if selected and using move tool
        if index == self.selected_index and self.current_tool == "move":
            self._draw_resize_handles(painter, rect)
        # Draw label if box is large enough
        if label and w > 40 and h > 30:
            self._draw_label(painter, rect, label, comp_type, border_color)

    def _draw_resize_handles(self, painter: QPainter, rect: QRect):
        painter.setBrush(QBrush(QColor("#6366f1")))
        painter.setPen(QPen(QColor("#4f46e5"), 2))
        hs = self.RESIZE_HANDLE_SIZE
        handles = [
            QRect(rect.left() - hs // 2, rect.top() - hs // 2, hs, hs),
            QRect(rect.right() - hs // 2, rect.top() - hs // 2, hs, hs),
            QRect(rect.right() - hs // 2, rect.bottom() - hs // 2, hs, hs),
            QRect(rect.left() - hs // 2, rect.bottom() - hs // 2, hs, hs),
            QRect(rect.center().x() - hs // 2, rect.top() - hs // 2, hs, hs),
            QRect(rect.right() - hs // 2, rect.center().y() - hs // 2, hs, hs),
            QRect(rect.center().x() - hs // 2, rect.bottom() - hs // 2, hs, hs),
            QRect(rect.left() - hs // 2, rect.center().y() - hs // 2, hs, hs),
        ]
        for handle in handles:
            painter.drawRoundedRect(handle, 3, 3)

    def _draw_label(
        self,
        painter: QPainter,
        rect: QRect,
        label: str,
        comp_type: str,
        border_color: QColor,
    ):
        label_text = f"{label[:40]}{'...' if len(label) > 40 else ''}"
        font = QFont("Segoe UI", 10)
        painter.setFont(font)
        text_rect = painter.boundingRect(
            QRect(rect.x(), rect.y() - 25, rect.width(), 25),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            label_text,
        )
        label_bg_rect = QRect(
            rect.x(), rect.y() - 25, max(rect.width(), text_rect.width() + 10), 25
        )
        painter.setBrush(QBrush(QColor(0, 0, 0, 200)))
        painter.setPen(QPen(border_color, 2))
        painter.drawRoundedRect(label_bg_rect, 6, 6)
        painter.setPen(QColor("#ffffff"))
        painter.drawText(
            QRect(rect.x() + 5, rect.y() - 25, rect.width(), 25),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            label_text,
        )
        # Type badge on the right side
        type_rect = painter.boundingRect(
            QRect(0, 0, 100, 20), Qt.AlignmentFlag.AlignCenter, comp_type
        )
        painter.setBrush(QBrush(QColor("#6366f1")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(
            QRect(
                rect.right() - type_rect.width() - 8,
                rect.y() - 25,
                type_rect.width() + 8,
                20,
            ),
            6,
            6,
        )
        painter.setPen(QColor("#ffffff"))
        painter.setFont(QFont("Segoe UI", 9))
        painter.drawText(
            QRect(
                rect.right() - type_rect.width() - 8,
                rect.y() - 25,
                type_rect.width() + 8,
                20,
            ),
            Qt.AlignmentFlag.AlignCenter,
            comp_type,
        )

    def _draw_interaction_rect(self, painter: QPainter):
        if self.is_drawing:
            rect = QRect(self.draw_start, self.draw_current).normalized()
            painter.setBrush(QBrush(QColor(0, 255, 0, 30)))
            painter.setPen(QPen(QColor("#00ff00"), 2, Qt.PenStyle.DashLine))
            painter.drawRect(rect)
            w, h = rect.width(), rect.height()
            painter.setPen(QColor("#00ff00"))
            painter.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
            painter.drawText(
                QRect(rect.x(), rect.y() - 25, w, 25),
                Qt.AlignmentFlag.AlignCenter,
                f"{w}×{h}px",
            )
        elif self.is_resizing:
            painter.setBrush(QBrush(QColor(0, 255, 0, 30)))
            painter.setPen(QPen(QColor("#00ff00"), 3))
            painter.drawRect(self.resize_start_rect)

    def _draw_instructions(self, painter: QPainter):
        instructions = [
            f"🛠️ Tool: {self.current_tool.upper()}",
            "🖱️ Drag: Move box",
            "🔲 Drag corner: Resize",
            "✏️ Double-click: Edit label",
            "🗑️ Right-click: Delete",
            f"📦 Components: {len(self.components)}",
        ]
        panel_w, panel_h = 280, 25 + 28 * len(instructions)
        panel_rect = QRect(
            self.width() - panel_w - 20, 20, panel_w, panel_h
        )
        painter.setBrush(QBrush(QColor(31, 41, 55, 230)))
        painter.setPen(QPen(QColor(99, 102, 241), 2))
        painter.drawRoundedRect(panel_rect, 12, 12)
        painter.setPen(QColor("#ffffff"))
        painter.setFont(QFont("Segoe UI", 11))
        for i, instr in enumerate(instructions):
            y = 35 + i * 28
            if i == 0:
                painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
                painter.setPen(QColor("#6366f1"))
            else:
                painter.setFont(QFont("Segoe UI", 10))
                painter.setPen(QColor("#e5e7eb"))
            painter.drawText(
                QRect(panel_rect.x() + 15, panel_rect.y() + y - 10, panel_rect.width() - 30, 25),
                Qt.AlignmentFlag.AlignLeft,
                instr,
            )

    # ---------------------------------------------------------------------
    # Mouse handling – drawing, dragging, resizing, clicking
    # ---------------------------------------------------------------------
    def _get_resize_handle_at(self, pos: QPoint, rect: QRect) -> int:
        hs = self.RESIZE_HANDLE_SIZE
        handles = [
            QRect(rect.left() - hs, rect.top() - hs, hs * 2, hs * 2),
            QRect(rect.right() - hs, rect.top() - hs, hs * 2, hs * 2),
            QRect(rect.right() - hs, rect.bottom() - hs, hs * 2, hs * 2),
            QRect(rect.left() - hs, rect.bottom() - hs, hs * 2, hs * 2),
            QRect(rect.center().x() - hs, rect.top() - hs, hs * 2, hs * 2),
            QRect(rect.right() - hs, rect.center().y() - hs, hs * 2, hs * 2),
            QRect(rect.center().x() - hs, rect.bottom() - hs, hs * 2, hs * 2),
            QRect(rect.left() - hs, rect.center().y() - hs, hs * 2, hs * 2),
        ]
        for i, h in enumerate(handles):
            if h.contains(pos):
                return i
        return -1

    def _get_resize_cursor(self, handle_index: int) -> QCursor:
        cursors = {
            0: Qt.CursorShape.SizeFDiagCursor,
            1: Qt.CursorShape.SizeBDiagCursor,
            2: Qt.CursorShape.SizeFDiagCursor,
            3: Qt.CursorShape.SizeBDiagCursor,
            4: Qt.CursorShape.SizeVerCursor,
            5: Qt.CursorShape.SizeHorCursor,
            6: Qt.CursorShape.SizeVerCursor,
            7: Qt.CursorShape.SizeHorCursor,
        }
        return QCursor(cursors.get(handle_index, Qt.CursorShape.ArrowCursor))

    def mouseMoveEvent(self, event: QMouseEvent):
        pos = event.position().toPoint()
        # Ignore when hovering over the toolbar itself
        if self.toolbar.underMouse():
            return
        # Resizing
        if self.is_resizing and self.resize_component_index >= 0:
            self._handle_resize(pos)
            return
        # Dragging a component
        if self.is_dragging and self.drag_component_index >= 0:
            self._handle_drag(pos)
            return
        # Drawing a new box
        if self.is_drawing:
            self.draw_current = pos
            self.update()
            return
        # Resize handle hover (only when a component is selected and move tool active)
        if self.current_tool == "move" and self.selected_index >= 0:
            comp = self.components[self.selected_index]
            rect = QRect(comp["x"], comp["y"], comp["width"], comp["height"])
            handle = self._get_resize_handle_at(pos, rect)
            if handle >= 0:
                self.hovered_resize_handle = handle
                self.setCursor(self._get_resize_cursor(handle))
                return
        # Component hover detection
        self.hovered_index = -1
        self.hovered_resize_handle = -1
        for i, comp in enumerate(self.components):
            rect = QRect(comp["x"], comp["y"], comp["width"], comp["height"])
            if rect.contains(pos):
                self.hovered_index = i
                break
        self.setCursor(self._get_tool_cursor())
        self.update()

    def _handle_drag(self, pos: QPoint):
        comp = self.components[self.drag_component_index]
        new_x = pos.x() - self.drag_offset.x()
        new_y = pos.y() - self.drag_offset.y()
        # Clamp within screen bounds
        new_x = max(0, min(new_x, self.width() - comp["width"]))
        new_y = max(0, min(new_y, self.height() - comp["height"]))
        comp["x"] = new_x
        comp["y"] = new_y
        comp["center_x"] = new_x + comp["width"] // 2
        comp["center_y"] = new_y + comp["height"] // 2
        # Re‑capture template after moving – same logic as original implementation
        try:
            import cv2, numpy as np, pyautogui as _pag, time
            from PyQt6.QtWidgets import QApplication
            self.hide()
            QApplication.processEvents()
            time.sleep(0.15)
            screenshot = _pag.screenshot()
            img_np = np.array(screenshot)
            img_h, img_w = img_np.shape[:2]
            screen = QApplication.primaryScreen()
            geom = screen.geometry()
            sx, sy = img_w / geom.width(), img_h / geom.height()
            x1 = max(0, int(new_x * sx))
            y1 = max(0, int(new_y * sy))
            x2 = min(img_w, int((new_x + comp["width"]) * sx))
            y2 = min(img_h, int((new_y + comp["height"]) * sy))
            tpl_rgb = img_np[y1:y2, x1:x2]
            if tpl_rgb.size > 0:
                tpl_bgr = cv2.cvtColor(tpl_rgb, cv2.COLOR_RGB2BGR)
                comp["_template_rgb"] = tpl_bgr
                comp["_template_gray"] = cv2.cvtColor(tpl_bgr, cv2.COLOR_BGR2GRAY)
                logger.debug(f"Template recaptured at ({new_x}, {new_y}) {tpl_bgr.shape}")
            self.show()
            QApplication.processEvents()
        except Exception as e:
            logger.error(f"Failed to recapture template during drag: {e}")
        self.update()

    def _handle_resize(self, pos: QPoint):
        comp = self.components[self.resize_component_index]
        handle = self.hovered_resize_handle
        x, y, w, h = comp["x"], comp["y"], comp["width"], comp["height"]
        # Left handles – adjust x and width
        if handle in (0, 3, 7):
            new_x = min(x + w - 20, pos.x())
            new_w = w + (x - new_x)
            comp["x"] = new_x
            comp["width"] = new_w
        # Top handles – adjust y and height
        if handle in (0, 1, 4):
            new_y = min(y + h - 20, pos.y())
            comp["y"] = new_y
            comp["height"] = h + (y - new_y)
        # Right handles – adjust width only
        if handle in (1, 2, 5):
            comp["width"] = max(20, pos.x() - x)
        # Bottom handles – adjust height only
        if handle in (2, 3, 6):
            comp["height"] = max(20, pos.y() - y)
        comp["center_x"] = comp["x"] + comp["width"] // 2
        comp["center_y"] = comp["y"] + comp["height"] // 2
        # Re‑capture template after resize (same logic as drag)
        try:
            import cv2, numpy as np, pyautogui as _pag, time
            from PyQt6.QtWidgets import QApplication
            self.hide()
            QApplication.processEvents()
            time.sleep(0.15)
            screenshot = _pag.screenshot()
            img_np = np.array(screenshot)
            img_h, img_w = img_np.shape[:2]
            screen = QApplication.primaryScreen()
            geom = screen.geometry()
            sx, sy = img_w / geom.width(), img_h / geom.height()
            x1 = max(0, int(comp["x"] * sx))
            y1 = max(0, int(comp["y"] * sy))
            x2 = min(img_w, int((comp["x"] + comp["width"]) * sx))
            y2 = min(img_h, int((comp["y"] + comp["height"]) * sy))
            tpl_rgb = img_np[y1:y2, x1:x2]
            if tpl_rgb.size > 0:
                tpl_bgr = cv2.cvtColor(tpl_rgb, cv2.COLOR_RGB2BGR)
                comp["_template_rgb"] = tpl_bgr
                comp["_template_gray"] = cv2.cvtColor(tpl_bgr, cv2.COLOR_BGR2GRAY)
                logger.debug(
                    f"Template recaptured at ({comp['x']}, {comp['y']}) {comp['width']}x{comp['height']} {tpl_bgr.shape}"
                )
            self.show()
            QApplication.processEvents()
        except Exception as e:
            logger.error(f"Failed to recapture template during resize: {e}")
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        if self.toolbar.underMouse():
            return
        pos = event.position().toPoint()
        if event.button() == Qt.MouseButton.LeftButton:
            # Resize handle activation
            if self.current_tool == "move" and self.selected_index >= 0:
                comp = self.components[self.selected_index]
                rect = QRect(comp["x"], comp["y"], comp["width"], comp["height"])
                handle = self._get_resize_handle_at(pos, rect)
                if handle >= 0:
                    self.is_resizing = True
                    self.resize_component_index = self.selected_index
                    self.resize_start_rect = QRect(comp["x"], comp["y"], comp["width"], comp["height"])
                    self.draw_start = pos
                    return
            # Component click handling
            if self.hovered_index >= 0:
                if self.current_tool == "move":
                    self.is_dragging = True
                    self.drag_component_index = self.hovered_index
                    comp = self.components[self.hovered_index]
                    self.drag_offset = pos - QPoint(comp["x"], comp["y"])
                    self.selected_index = self.hovered_index
                elif self.current_tool == "delete":
                    self.component_deleted.emit(self.hovered_index)
                    del self.components[self.hovered_index]
                    self.hovered_index = -1
                self.update()
            else:
                # Start drawing a new box if Box tool is active
                if self.current_tool == "box":
                    self.is_drawing = True
                    self.draw_start = pos
                    self.draw_current = pos
                    self.update()
        elif event.button() == Qt.MouseButton.RightButton:
            if self.hovered_index >= 0:
                self.component_deleted.emit(self.hovered_index)
                del self.components[self.hovered_index]
                self.hovered_index = -1
                self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self.is_drawing:
            self.is_drawing = False
            rect = QRect(self.draw_start, self.draw_current).normalized()
            if rect.width() >= 10 and rect.height() >= 10:
                # Coordinates are already screen coordinates because the widget covers the screen
                self._show_label_editor(rect.x(), rect.y(), rect.width(), rect.height())
            self.update()
        elif self.is_resizing:
            self.is_resizing = False
            self.resize_component_index = -1
        elif self.is_dragging:
            self.is_dragging = False
            self.drag_component_index = -1

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if self.hovered_index >= 0:
            comp = self.components[self.hovered_index]
            self._show_label_editor_for_component(self.hovered_index, comp)

    def _show_label_editor_for_component(self, index: int, comp: Dict):
        dialog = LabelEditorDialog(self, comp.get("label", ""), comp.get("component_type", "other"))
        comp_rect = QRect(comp["x"], comp["y"], comp["width"], comp["height"])
        ideal_x = comp_rect.center().x() - dialog.width() // 2
        ideal_y = comp_rect.center().y() - dialog.height() // 2
        screen_rect = QApplication.primaryScreen().geometry()
        if ideal_x < screen_rect.left():
            ideal_x = screen_rect.left() + 10
        elif ideal_x + dialog.width() > screen_rect.right():
            ideal_x = screen_rect.right() - dialog.width() - 10
        if ideal_y < screen_rect.top():
            ideal_y = comp_rect.bottom() + 10
            if ideal_y + dialog.height() > screen_rect.bottom():
                ideal_y = screen_rect.top() + 10
        dialog.move(ideal_x, ideal_y)
        dialog.label_saved.connect(lambda label, ctype: self.component_edited.emit(index, label, ctype))
        dialog.exec()

    def _show_label_editor(self, x: int, y: int, w: int, h: int):
        dialog = LabelEditorDialog(self, "New component", "icon")
        screen_rect = QApplication.primaryScreen().geometry()
        dialog_x = max(screen_rect.left(), min(x, screen_rect.right() - dialog.width()))
        dialog_y = max(screen_rect.top(), min(y, screen_rect.bottom() - dialog.height()))
        dialog.move(dialog_x, dialog_y)
        dialog.label_saved.connect(lambda label, ctype: self.component_added.emit(x, y, w, h, label, ctype))
        dialog.exec()

    # ---------------------------------------------------------------------
    # Keyboard shortcuts
    # ---------------------------------------------------------------------
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_V:
            self.toolbar.set_tool("move")
        elif event.key() == Qt.Key.Key_B:
            self.toolbar.set_tool("box")
        elif event.key() == Qt.Key.Key_D:
            self.toolbar.set_tool("delete")
        elif event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            if self.hovered_index >= 0:
                self.component_deleted.emit(self.hovered_index)
                del self.components[self.hovered_index]
                self.hovered_index = -1
                self.selected_index = -1
                self.update()
        elif event.key() == Qt.Key.Key_Escape:
            self.close_requested.emit()
            self.close()
