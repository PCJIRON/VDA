"""
UIED Overlay Widget - Interactive Component Editor v2.

Figma-style toolbar with tools:
- Move Tool (V) - Move and resize boxes
- Box Tool (B) - Create new boxes
- Delete Tool (D) - Delete boxes

Features:
- Draggable toolbar
- Double-click to edit labels
- Drag to move boxes
- Drag corners to resize
- Click+drag to create new boxes
- Right-click or Delete tool to remove
"""

from PyQt6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, 
    QLabel, QComboBox, QFrame, QGraphicsDropShadowEffect, QApplication,
    QToolButton
)
from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal, QSize
from PyQt6.QtGui import (
    QColor, QPainter, QPen, QBrush, QFont, QCursor, QKeyEvent, QMouseEvent,
    QPaintEvent, QResizeEvent
)

from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class ToolButton(QToolButton):
    """Styled tool button for the toolbar."""
    
    def __init__(self, icon: str, tooltip: str, shortcut: str = "", parent=None):
        super().__init__(parent)
        self.setText(icon)
        self.setToolTip(f"{tooltip} ({shortcut})" if shortcut else tooltip)
        self.setFixedSize(50, 50)
        self.setIconSize(QSize(28, 28))
        self.setStyleSheet("""
            QToolButton {
                background-color: #374151;
                color: white;
                border: 2px solid #4b5563;
                border-radius: 8px;
                font-size: 24px;
            }
            QToolButton:hover {
                background-color: #4b5563;
                border-color: #6366f1;
            }
            QToolButton:checked {
                background-color: #6366f1;
                border-color: #4f46e5;
            }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class LabelEditorDialog(QDialog):
    """Popup dialog for editing component labels."""
    
    label_saved = pyqtSignal(str, str)
    
    def __init__(self, parent=None, current_label: str = "", current_type: str = "icon"):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(350, 200)
        self._setup_ui(current_label, current_type)
    
    def _setup_ui(self, current_label: str, current_type: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #1f2937;
                border-radius: 12px;
                border: 2px solid #6366f1;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(16, 16, 16, 16)
        container_layout.setSpacing(12)
        
        title = QLabel("✏️ Edit Component Label")
        title.setStyleSheet("color: white; font-weight: bold; font-size: 14px; background: transparent;")
        container_layout.addWidget(title)
        
        self.label_input = QLineEdit(current_label)
        self.label_input.setPlaceholderText("Enter detailed label...")
        self.label_input.setStyleSheet("""
            QLineEdit {
                background-color: #374151;
                color: white;
                border: 1px solid #4b5563;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus { border: 1px solid #6366f1; }
        """)
        container_layout.addWidget(self.label_input)
        
        type_row = QHBoxLayout()
        type_label = QLabel("Type:")
        type_label.setStyleSheet("color: #9ca3af; background: transparent;")
        type_row.addWidget(type_label)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "app_icon", "symbol_icon", "button", "text_label",
            "input_field", "container_panel", "menu_item", "tab",
            "checkbox_toggle", "scrollbar", "decorative", "other"
        ])
        self.type_combo.setCurrentText(current_type)
        self.type_combo.setStyleSheet("""
            QComboBox {
                background-color: #374151;
                color: white;
                border: 1px solid #4b5563;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
            }
        """)
        type_row.addWidget(self.type_combo, 1)
        container_layout.addLayout(type_row)
        
        button_row = QHBoxLayout()
        button_row.setSpacing(8)
        
        self.save_btn = QPushButton("💾 Save")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #4f46e5; }
        """)
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.cancel_btn = QPushButton("✕ Cancel")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #374151;
                color: #9ca3af;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #4b5563;
                color: white;
            }
        """)
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        button_row.addWidget(self.save_btn)
        button_row.addWidget(self.cancel_btn)
        button_row.addStretch()
        container_layout.addLayout(button_row)
        
        layout.addWidget(container)
        
        self.save_btn.clicked.connect(self._on_save)
        self.cancel_btn.clicked.connect(self.reject)
        self.label_input.returnPressed.connect(self._on_save)
    
    def _on_save(self):
        new_label = self.label_input.text().strip()
        new_type = self.type_combo.currentText()
        if new_label:
            self.label_saved.emit(new_label, new_type)
            self.accept()


class DraggableToolbar(QWidget):
    """Figma-style draggable toolbar."""
    
    tool_changed = pyqtSignal(str)
    done_clicked = pyqtSignal()
    exit_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        screen = QApplication.primaryScreen().geometry()
        self.setFixedSize(520, 80)
        self.move(screen.width() // 2 - 260, screen.height() - 120)
        
        self.current_tool = 'move'
        self.is_dragging_toolbar = False
        self.drag_offset = QPoint()
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: rgba(31, 41, 55, 240);
                border-radius: 16px;
                border: 2px solid #6366f1;
            }
        """)
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(12, 8, 12, 8)
        container_layout.setSpacing(6)
        
        self.move_btn = ToolButton("🖱️", "Move Tool", "V")
        self.move_btn.setCheckable(True)
        self.move_btn.setChecked(True)
        self.move_btn.clicked.connect(lambda: self._on_tool_clicked('move'))
        container_layout.addWidget(self.move_btn)
        
        self.box_btn = ToolButton("⬜", "Box Tool", "B")
        self.box_btn.setCheckable(True)
        self.box_btn.clicked.connect(lambda: self._on_tool_clicked('box'))
        container_layout.addWidget(self.box_btn)
        
        self.delete_btn = ToolButton("🗑️", "Delete Tool", "D")
        self.delete_btn.setCheckable(True)
        self.delete_btn.clicked.connect(lambda: self._on_tool_clicked('delete'))
        container_layout.addWidget(self.delete_btn)
        
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setStyleSheet("background-color: #4b5563;")
        separator.setFixedWidth(2)
        container_layout.addWidget(separator)
        
        self.done_btn = QPushButton("✅ Done")
        self.done_btn.setFixedSize(100, 45)
        self.done_btn.setStyleSheet("""
            QPushButton {
                background-color: #16a34a;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #15803d; }
        """)
        self.done_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.done_btn.clicked.connect(self._on_done_clicked)
        container_layout.addWidget(self.done_btn)
        
        self.exit_btn = QPushButton("✕ Exit")
        self.exit_btn.setFixedSize(100, 45)
        self.exit_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc2626;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #b91c1c; }
        """)
        self.exit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.exit_btn.clicked.connect(self._on_exit_clicked)
        container_layout.addWidget(self.exit_btn)
        
        layout.addWidget(container)
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 5)
        container.setGraphicsEffect(shadow)
    
    def _on_done_clicked(self):
        """Emit done signal and save all components."""
        logger.info("Done button clicked - saving all components")
        # Hide toolbar first
        self.hide()
        self.done_clicked.emit()
    
    def _on_exit_clicked(self):
        """Emit exit signal."""
        logger.info("Exit button clicked")
        # Hide toolbar first
        self.hide()
        self.exit_clicked.emit()
    
    def _on_tool_clicked(self, tool: str):
        self.current_tool = tool
        self.move_btn.setChecked(tool == 'move')
        self.box_btn.setChecked(tool == 'box')
        self.delete_btn.setChecked(tool == 'delete')
        self.tool_changed.emit(tool)
    
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            child = self.childAt(pos)
            if isinstance(child, QFrame) or child is None:
                self.is_dragging_toolbar = True
                self.drag_offset = pos
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        if self.is_dragging_toolbar:
            new_pos = event.globalPosition().toPoint() - self.drag_offset
            screen = QApplication.primaryScreen().geometry()
            new_pos.setX(max(0, min(new_pos.x(), screen.width() - self.width())))
            new_pos.setY(max(0, min(new_pos.y(), screen.height() - self.height())))
            self.move(new_pos)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        self.is_dragging_toolbar = False
        self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def set_tool(self, tool: str):
        self._on_tool_clicked(tool)


class UIEDOverlayWidget(QWidget):
    """Full-screen overlay with Figma-style toolbar."""
    
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
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        # Get screen geometry - widget will cover entire screen
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        
        # Store screen origin for coordinate conversion
        self.screen_origin = screen.topLeft()
        
        logger.info(f"UIED Overlay v2 initialized - Screen: {screen.x()}, {screen.y()}, {screen.width()}x{screen.height()}")

        self.components: List[Dict] = []
        self.hovered_index = -1
        self.hovered_resize_handle = -1  # 0-7 for 8 handles
        self.selected_index = -1

        # Tool state
        self.current_tool = 'move'

        # Interaction states
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

        # Create toolbar
        self.toolbar = DraggableToolbar(self)
        self.toolbar.tool_changed.connect(self._on_tool_changed)
        self.toolbar.done_clicked.connect(self.close_requested.emit)
        self.toolbar.exit_clicked.connect(self.close_requested.emit)
        self.toolbar.show()

        logger.info("UIED Overlay v2 initialized")
    
    def _on_tool_changed(self, tool: str):
        """Handle tool change from toolbar."""
        self.current_tool = tool
        self.setCursor(self._get_tool_cursor())
        logger.info(f"Tool changed to: {tool}")
    
    def _get_tool_cursor(self) -> Qt.CursorShape:
        """Get cursor for current tool."""
        if self.current_tool == 'move':
            return Qt.CursorShape.OpenHandCursor
        elif self.current_tool == 'box':
            return Qt.CursorShape.CrossCursor
        elif self.current_tool == 'delete':
            return Qt.CursorShape.ForbiddenCursor
        return Qt.CursorShape.ArrowCursor
    
    def set_components(self, components: List[Dict]):
        self.components = components
        self.update()
    
    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Semi-transparent background
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))
        
        # Draw components
        for i, comp in enumerate(self.components):
            self._draw_component(painter, i, comp)
        
        # Draw drawing/resize rectangle
        if self.is_drawing or self.is_resizing:
            self._draw_interaction_rect(painter)
        
        # Draw instructions
        self._draw_instructions(painter)
    
    def _draw_component(self, painter: QPainter, index: int, comp: Dict):
        """Draw component with resize handles if selected."""
        x = comp.get('x', 0)
        y = comp.get('y', 0)
        w = comp.get('width', 0)
        h = comp.get('height', 0)
        label = comp.get('label', 'Unknown')
        comp_type = comp.get('component_type', 'other')
        
        rect = QRect(x, y, w, h)
        
        # Colors based on state
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
        
        # Draw resize handles if selected and using move tool
        if index == self.selected_index and self.current_tool == 'move':
            self._draw_resize_handles(painter, rect)
        
        # Draw label
        if label and w > 40 and h > 30:
            self._draw_label(painter, rect, label, comp_type, border_color)
    
    def _draw_resize_handles(self, painter: QPainter, rect: QRect):
        """Draw 8 resize handles around selected component."""
        painter.setBrush(QBrush(QColor("#6366f1")))
        painter.setPen(QPen(QColor("#4f46e5"), 2))
        
        handle_size = self.RESIZE_HANDLE_SIZE
        
        # 8 handles: corners + midpoints
        handles = [
            QRect(rect.left() - handle_size//2, rect.top() - handle_size//2, handle_size, handle_size),  # Top-left
            QRect(rect.right() - handle_size//2, rect.top() - handle_size//2, handle_size, handle_size),  # Top-right
            QRect(rect.right() - handle_size//2, rect.bottom() - handle_size//2, handle_size, handle_size),  # Bottom-right
            QRect(rect.left() - handle_size//2, rect.bottom() - handle_size//2, handle_size, handle_size),  # Bottom-left
            QRect(rect.center().x() - handle_size//2, rect.top() - handle_size//2, handle_size, handle_size),  # Top-center
            QRect(rect.right() - handle_size//2, rect.center().y() - handle_size//2, handle_size, handle_size),  # Right-center
            QRect(rect.center().x() - handle_size//2, rect.bottom() - handle_size//2, handle_size, handle_size),  # Bottom-center
            QRect(rect.left() - handle_size//2, rect.center().y() - handle_size//2, handle_size, handle_size),  # Left-center
        ]
        
        for handle in handles:
            painter.drawRoundedRect(handle, 3, 3)
    
    def _draw_label(self, painter: QPainter, rect: QRect, label: str, comp_type: str, border_color: QColor):
        """Draw label and type badge."""
        label_text = f"{label[:40]}{'...' if len(label) > 40 else ''}"
        font = QFont("Segoe UI", 10)
        painter.setFont(font)
        
        text_rect = painter.boundingRect(
            QRect(rect.x(), rect.y() - 25, rect.width(), 25),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            label_text
        )
        
        label_bg_rect = QRect(
            rect.x(), rect.y() - 25,
            max(rect.width(), text_rect.width() + 10),
            25
        )
        painter.setBrush(QBrush(QColor(0, 0, 0, 200)))
        painter.setPen(QPen(border_color, 2))
        painter.drawRoundedRect(label_bg_rect, 6, 6)
        
        painter.setPen(QColor("#ffffff"))
        painter.drawText(
            QRect(rect.x() + 5, rect.y() - 25, rect.width(), 25),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            label_text
        )
        
        # Type badge
        type_rect = painter.boundingRect(
            QRect(0, 0, 100, 20),
            Qt.AlignmentFlag.AlignCenter,
            comp_type
        )
        
        painter.setBrush(QBrush(QColor("#6366f1")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(
            QRect(rect.right() - type_rect.width() - 8, rect.y() - 25, type_rect.width() + 8, 20),
            6, 6
        )
        
        painter.setPen(QColor("#ffffff"))
        painter.setFont(QFont("Segoe UI", 9))
        painter.drawText(
            QRect(rect.right() - type_rect.width() - 8, rect.y() - 25, type_rect.width() + 8, 20),
            Qt.AlignmentFlag.AlignCenter,
            comp_type
        )
    
    def _draw_interaction_rect(self, painter: QPainter):
        """Draw rectangle for drawing or resizing."""
        if self.is_drawing:
            rect = QRect(self.draw_start, self.draw_current).normalized()
            painter.setBrush(QBrush(QColor(0, 255, 0, 30)))
            painter.setPen(QPen(QColor("#00ff00"), 2, Qt.PenStyle.DashLine))
            painter.drawRect(rect)
            
            w = rect.width()
            h = rect.height()
            painter.setPen(QColor("#00ff00"))
            painter.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
            painter.drawText(
                QRect(rect.x(), rect.y() - 25, w, 25),
                Qt.AlignmentFlag.AlignCenter,
                f"{w}×{h}px"
            )
        
        elif self.is_resizing:
            painter.setBrush(QBrush(QColor(0, 255, 0, 30)))
            painter.setPen(QPen(QColor("#00ff00"), 3))
            painter.drawRect(self.resize_start_rect)
    
    def _draw_instructions(self, painter: QPainter):
        """Draw instruction panel."""
        instructions = [
            f"🛠️ Tool: {self.current_tool.upper()}",
            "🖱️ Drag: Move box",
            "🔲 Drag corner: Resize",
            "✏️ Double-click: Edit label",
            "🗑️ Right-click: Delete",
            f"📦 Components: {len(self.components)}"
        ]
        
        panel_width = 280
        panel_height = 25 + 28 * len(instructions)
        panel_rect = QRect(
            self.width() - panel_width - 20,
            20,
            panel_width,
            panel_height
        )
        
        painter.setBrush(QBrush(QColor(31, 41, 55, 230)))
        painter.setPen(QPen(QColor(99, 102, 241), 2))
        painter.drawRoundedRect(panel_rect, 12, 12)
        
        painter.setPen(QColor("#ffffff"))
        painter.setFont(QFont("Segoe UI", 11))
        
        for i, instruction in enumerate(instructions):
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
                instruction
            )
    
    def _get_resize_handle_at(self, pos: QPoint, rect: QRect) -> int:
        """Get resize handle index at position (0-7, or -1 if none)."""
        handle_size = self.RESIZE_HANDLE_SIZE
        
        handles = [
            QRect(rect.left() - handle_size, rect.top() - handle_size, handle_size * 2, handle_size * 2),
            QRect(rect.right() - handle_size, rect.top() - handle_size, handle_size * 2, handle_size * 2),
            QRect(rect.right() - handle_size, rect.bottom() - handle_size, handle_size * 2, handle_size * 2),
            QRect(rect.left() - handle_size, rect.bottom() - handle_size, handle_size * 2, handle_size * 2),
            QRect(rect.center().x() - handle_size, rect.top() - handle_size, handle_size * 2, handle_size * 2),
            QRect(rect.right() - handle_size, rect.center().y() - handle_size, handle_size * 2, handle_size * 2),
            QRect(rect.center().x() - handle_size, rect.bottom() - handle_size, handle_size * 2, handle_size * 2),
            QRect(rect.left() - handle_size, rect.center().y() - handle_size, handle_size * 2, handle_size * 2),
        ]
        
        for i, handle in enumerate(handles):
            if handle.contains(pos):
                return i
        return -1
    
    def _get_resize_cursor(self, handle_index: int) -> QCursor:
        """Get appropriate cursor for resize handle."""
        cursors = {
            0: Qt.CursorShape.SizeFDiagCursor,  # Top-left
            1: Qt.CursorShape.SizeBDiagCursor,  # Top-right
            2: Qt.CursorShape.SizeFDiagCursor,  # Bottom-right
            3: Qt.CursorShape.SizeBDiagCursor,  # Bottom-left
            4: Qt.CursorShape.SizeVerCursor,    # Top
            5: Qt.CursorShape.SizeHorCursor,    # Right
            6: Qt.CursorShape.SizeVerCursor,    # Bottom
            7: Qt.CursorShape.SizeHorCursor,    # Left
        }
        return QCursor(cursors.get(handle_index, Qt.CursorShape.ArrowCursor))
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move for all interactions."""
        pos = event.position().toPoint()
        
        # Handle dragging toolbar
        if self.toolbar.underMouse():
            return
        
        # Handle resizing
        if self.is_resizing and self.resize_component_index >= 0:
            self._handle_resize(pos)
            return
        
        # Handle dragging component
        if self.is_dragging and self.drag_component_index >= 0:
            self._handle_drag(pos)
            return
        
        # Handle drawing
        if self.is_drawing:
            self.draw_current = pos
            self.update()
            return
        
        # Check resize handles first (only for selected component with move tool)
        if self.current_tool == 'move' and self.selected_index >= 0:
            comp = self.components[self.selected_index]
            rect = QRect(comp['x'], comp['y'], comp['width'], comp['height'])
            handle = self._get_resize_handle_at(pos, rect)
            
            if handle >= 0:
                self.hovered_resize_handle = handle
                self.setCursor(self._get_resize_cursor(handle))
                return
        
        # Check component hover
        self.hovered_index = -1
        self.hovered_resize_handle = -1
        
        for i, comp in enumerate(self.components):
            rect = QRect(comp['x'], comp['y'], comp['width'], comp['height'])
            if rect.contains(pos):
                self.hovered_index = i
                break
        
        self.setCursor(self._get_tool_cursor())
        self.update()
    
    def _handle_drag(self, pos: QPoint):
        """Handle component dragging."""
        comp = self.components[self.drag_component_index]
        new_x = pos.x() - self.drag_offset.x()
        new_y = pos.y() - self.drag_offset.y()

        new_x = max(0, min(new_x, self.width() - comp['width']))
        new_y = max(0, min(new_y, self.height() - comp['height']))

        comp['x'] = new_x
        comp['y'] = new_y
        comp['center_x'] = new_x + comp['width'] // 2
        comp['center_y'] = new_y + comp['height'] // 2
        
        # ✅ CRITICAL: Recapture template using Qt grabWindow (same coordinate system)
        try:
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtCore import QBuffer, QIODevice
            from PIL import Image
            import cv2
            import numpy as np
            import io
            
            # ✅ Hide overlay BEFORE capturing to avoid capturing the box/toolbar
            self.hide()
            QApplication.processEvents()
            import time
            time.sleep(0.05)
            
            # Use Qt's grabWindow - NO DPI scaling issues!
            screen = QApplication.primaryScreen()
            pixmap = screen.grabWindow(0, new_x, new_y, comp['width'], comp['height'])
            
            # ✅ Show overlay again AFTER capturing
            self.show()
            QApplication.processEvents()
            
            if not pixmap.isNull():
                # Convert QPixmap to OpenCV format
                buffer = QBuffer()
                buffer.open(QIODevice.OpenModeFlag.ReadWrite)
                pixmap.save(buffer, "PNG")
                
                img = Image.open(io.BytesIO(bytes(buffer.data())))
                template_rgb = np.array(img)
                template_bgr = cv2.cvtColor(template_rgb, cv2.COLOR_RGB2BGR)
                
                comp['_template_rgb'] = template_bgr
                comp['_template_gray'] = cv2.cvtColor(template_bgr, cv2.COLOR_BGR2GRAY)
                logger.debug(f"Template recaptured at ({new_x}, {new_y}) {template_bgr.shape}")
                
        except Exception as e:
            logger.error(f"Failed to recapture template during drag: {e}")

        self.update()

    def _handle_resize(self, pos: QPoint):
        """Handle component resizing."""
        comp = self.components[self.resize_component_index]
        handle = self.hovered_resize_handle

        x, y, w, h = comp['x'], comp['y'], comp['width'], comp['height']

        # Resize based on handle
        if handle in [0, 3, 7]:  # Left handles
            delta_x = pos.x() - (self.draw_start.x() if handle in [0, 3, 7] else x)
            new_x = min(x + w - 20, pos.x())
            new_w = w + (x - new_x)
            comp['x'] = new_x
            comp['width'] = new_w

        if handle in [0, 1, 4]:  # Top handles
            new_y = min(y + h - 20, pos.y())
            comp['y'] = new_y
            comp['height'] = h + (y - new_y)

        if handle in [1, 2, 5]:  # Right handles
            comp['width'] = max(20, pos.x() - x)

        if handle in [2, 3, 6]:  # Bottom handles
            comp['height'] = max(20, pos.y() - y)

        # Update center
        comp['center_x'] = comp['x'] + comp['width'] // 2
        comp['center_y'] = comp['y'] + comp['height'] // 2
        
        # ✅ CRITICAL: Recapture template using Qt grabWindow
        try:
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtCore import QBuffer, QIODevice
            from PIL import Image
            import cv2
            import numpy as np
            import io
            
            # ✅ Hide overlay BEFORE capturing to avoid capturing the box/toolbar
            self.hide()
            QApplication.processEvents()
            import time
            time.sleep(0.05)
            
            # Use Qt's grabWindow - NO DPI scaling issues!
            screen = QApplication.primaryScreen()
            pixmap = screen.grabWindow(0, comp['x'], comp['y'], comp['width'], comp['height'])
            
            # ✅ Show overlay again AFTER capturing
            self.show()
            QApplication.processEvents()
            
            if not pixmap.isNull():
                # Convert QPixmap to OpenCV format
                buffer = QBuffer()
                buffer.open(QIODevice.OpenModeFlag.ReadWrite)
                pixmap.save(buffer, "PNG")
                
                img = Image.open(io.BytesIO(bytes(buffer.data())))
                template_rgb = np.array(img)
                template_bgr = cv2.cvtColor(template_rgb, cv2.COLOR_RGB2BGR)
                
                comp['_template_rgb'] = template_bgr
                comp['_template_gray'] = cv2.cvtColor(template_bgr, cv2.COLOR_BGR2GRAY)
                logger.debug(f"Template recaptured at ({comp['x']}, {comp['y']}) {comp['width']}x{comp['height']} {template_bgr.shape}")
                
        except Exception as e:
            logger.error(f"Failed to recapture template during resize: {e}")

        self.update()
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press."""
        if self.toolbar.underMouse():
            return
        
        pos = event.position().toPoint()
        
        if event.button() == Qt.MouseButton.LeftButton:
            # Check resize handle
            if self.current_tool == 'move' and self.selected_index >= 0:
                comp = self.components[self.selected_index]
                rect = QRect(comp['x'], comp['y'], comp['width'], comp['height'])
                handle = self._get_resize_handle_at(pos, rect)
                
                if handle >= 0:
                    self.is_resizing = True
                    self.resize_component_index = self.selected_index
                    self.resize_start_rect = QRect(comp['x'], comp['y'], comp['width'], comp['height'])
                    self.draw_start = pos
                    return
            
            # Check component click
            if self.hovered_index >= 0:
                if self.current_tool == 'move':
                    # Start dragging
                    self.is_dragging = True
                    self.drag_component_index = self.hovered_index
                    comp = self.components[self.hovered_index]
                    self.drag_offset = pos - QPoint(comp['x'], comp['y'])
                    self.selected_index = self.hovered_index
                elif self.current_tool == 'delete':
                    # Delete immediately
                    self.component_deleted.emit(self.hovered_index)
                    del self.components[self.hovered_index]
                    self.hovered_index = -1
                self.update()
            else:
                # Start drawing new component
                if self.current_tool == 'box':
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
        """Handle mouse release."""
        if self.is_drawing:
            self.is_drawing = False
            rect = QRect(self.draw_start, self.draw_current).normalized()

            if rect.width() >= 10 and rect.height() >= 10:
                # Widget covers ENTIRE screen - widget coordinates ARE screen coordinates
                # No conversion needed!
                screen_x = rect.x()
                screen_y = rect.y()
                screen_w = rect.width()
                screen_h = rect.height()
                
                logger.info(f"🖱️ User drew box: ({screen_x}, {screen_y}) {screen_w}x{screen_h}")
                
                self._show_label_editor(screen_x, screen_y, screen_w, screen_h)
            self.update()

        elif self.is_resizing:
            self.is_resizing = False
            self.resize_component_index = -1

        elif self.is_dragging:
            self.is_dragging = False
            self.drag_component_index = -1
    
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Handle double-click to edit label."""
        if self.hovered_index >= 0:
            comp = self.components[self.hovered_index]
            self._show_label_editor_for_component(self.hovered_index, comp)
    
    def _show_label_editor_for_component(self, index: int, comp: Dict):
        """Show label editor dialog."""
        dialog = LabelEditorDialog(self, comp.get('label', ''), comp.get('component_type', 'other'))
        
        comp_rect = QRect(comp['x'], comp['y'], comp['width'], comp['height'])
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
        dialog.label_saved.connect(lambda label, comp_type: self.component_edited.emit(index, label, comp_type))
        dialog.exec()
    
    def _show_label_editor(self, x: int, y: int, w: int, h: int):
        """Show label editor for new component."""
        dialog = LabelEditorDialog(self, "New component", "icon")
        
        screen_rect = QApplication.primaryScreen().geometry()
        dialog_x = max(screen_rect.left(), min(x, screen_rect.right() - dialog.width()))
        dialog_y = max(screen_rect.top(), min(y, screen_rect.bottom() - dialog.height()))
        
        dialog.move(dialog_x, dialog_y)
        dialog.label_saved.connect(lambda label, comp_type: self.component_added.emit(x, y, w, h, label, comp_type))
        dialog.exec()
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard shortcuts."""
        if event.key() == Qt.Key.Key_V:
            self.toolbar.set_tool('move')
        elif event.key() == Qt.Key.Key_B:
            self.toolbar.set_tool('box')
        elif event.key() == Qt.Key.Key_D:
            self.toolbar.set_tool('delete')
        elif event.key() == Qt.Key.Key_Delete or event.key() == Qt.Key.Key_Backspace:
            if self.hovered_index >= 0:
                # Emit signal for floating_assistant to handle
                self.component_deleted.emit(self.hovered_index)
                # Also delete locally for immediate visual feedback
                del self.components[self.hovered_index]
                self.hovered_index = -1
                self.selected_index = -1
                self.update()
        elif event.key() == Qt.Key.Key_Escape:
            self.close_requested.emit()
            self.close()
