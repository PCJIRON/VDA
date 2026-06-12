"""Toolbar components for the UI‑ED overlay.

The toolbar mimics a Figma‑style floating toolbar that lets the user pick the
current editing tool (move, box, delete) and provides Done/Exit actions.
"""

import os
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QFrame,
    QPushButton,
    QGraphicsDropShadowEffect,
    QApplication,
)
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QSize, QRectF
from PyQt6.QtGui import QColor, QCursor, QPainter, QBrush, QIcon
from PyQt6.QtSvg import QSvgRenderer


class ToolButton(QPushButton):
    """Styled tool button for the toolbar that renders a vector SVG icon."""

    def __init__(self, svg_name: str, tooltip: str, shortcut: str = "", parent=None):
        super().__init__("", parent)
        self.setToolTip(f"{tooltip} ({shortcut})" if shortcut else tooltip)
        self.setFixedSize(40, 40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Resolve icon path
        svg_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "resources",
                "icons",
                svg_name,
            )
        )
        self.svg_renderer = None
        if os.path.exists(svg_path):
            self.svg_renderer = QSvgRenderer(svg_path)

        self._hovered = False

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background color depending on states
        if self.isChecked():
            bg_color = QColor("#2563eb")  # Blue active
        elif self._hovered:
            bg_color = QColor("#404040")  # Charcoal hover
        else:
            bg_color = QColor("transparent")

        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        r = self.height() / 2.0
        painter.drawRoundedRect(self.rect(), r, r)

        # Render SVG Icon
        if self.svg_renderer and self.svg_renderer.isValid():
            icon_size = 18.0
            x = (self.width() - icon_size) / 2.0
            y = (self.height() - icon_size) / 2.0
            self.svg_renderer.render(painter, QRectF(x, y, icon_size, icon_size))


class DraggableToolbar(QWidget):
    """Figma‑style draggable toolbar used by the UI‑ED overlay."""

    tool_changed = pyqtSignal(str)
    done_clicked = pyqtSignal()
    exit_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        screen = QApplication.primaryScreen().geometry()
        self.setFixedSize(520, 80)
        self.move(screen.width() // 2 - 260, screen.height() - 120)

        self.current_tool = "move"
        self.is_dragging_toolbar = False
        self.drag_offset = QPoint()

        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        container = QFrame()
        container.setStyleSheet(
            """
            QFrame {
                background-color: rgba(30, 30, 36, 240);
                border-radius: 16px;
                border: 1px solid #404040;
            }
            """
        )
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(12, 8, 12, 8)
        container_layout.setSpacing(6)

        # Move tool using mouse-pointer.svg
        self.move_btn = ToolButton("mouse-pointer.svg", "Move Tool", "V")
        self.move_btn.setCheckable(True)
        self.move_btn.setChecked(True)
        self.move_btn.clicked.connect(lambda: self._on_tool_clicked("move"))
        container_layout.addWidget(self.move_btn)

        # Box tool using square.svg
        self.box_btn = ToolButton("square.svg", "Box Tool", "B")
        self.box_btn.setCheckable(True)
        self.box_btn.clicked.connect(lambda: self._on_tool_clicked("box"))
        container_layout.addWidget(self.box_btn)

        # Delete tool using trash.svg
        self.delete_btn = ToolButton("trash.svg", "Delete Tool", "D")
        self.delete_btn.setCheckable(True)
        self.delete_btn.clicked.connect(lambda: self._on_tool_clicked("delete"))
        container_layout.addWidget(self.delete_btn)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setStyleSheet("background-color: #404040;")
        separator.setFixedWidth(2)
        container_layout.addWidget(separator)

        # Done button (loads check.svg icon)
        icons_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "resources", "icons"))
        self.done_btn = QPushButton(" Done")
        self.done_btn.setIcon(QIcon(os.path.join(icons_dir, "check.svg")))
        self.done_btn.setFixedSize(100, 40)
        self.done_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 20px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #1d4ed8; }
            """
        )
        self.done_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.done_btn.clicked.connect(self._on_done_clicked)
        container_layout.addWidget(self.done_btn)

        # Exit button (loads x.svg icon)
        self.exit_btn = QPushButton(" Exit")
        self.exit_btn.setIcon(QIcon(os.path.join(icons_dir, "x.svg")))
        self.exit_btn.setFixedSize(100, 40)
        self.exit_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #262626;
                color: #e5e5e5;
                border: 1px solid #404040;
                border-radius: 20px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #ef4444; border-color: #ef4444; color: white; }
            """
        )
        self.exit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.exit_btn.clicked.connect(self._on_exit_clicked)
        container_layout.addWidget(self.exit_btn)

        layout.addWidget(container)

        # Drop shadow for the whole toolbar container
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 5)
        container.setGraphicsEffect(shadow)

    def _on_done_clicked(self):
        """Emit done signal and hide the toolbar."""
        self.hide()
        self.done_clicked.emit()

    def _on_exit_clicked(self):
        """Emit exit signal and hide the toolbar."""
        self.hide()
        self.exit_clicked.emit()

    def _on_tool_clicked(self, tool: str):
        self.current_tool = tool
        self.move_btn.setChecked(tool == "move")
        self.box_btn.setChecked(tool == "box")
        self.delete_btn.setChecked(tool == "delete")
        self.tool_changed.emit(tool)

    # Mouse handling for dragging the toolbar itself
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            child = self.childAt(pos)
            if isinstance(child, QFrame) or child is None:
                self.is_dragging_toolbar = True
                self.drag_offset = pos
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_dragging_toolbar:
            new_pos = event.globalPosition().toPoint() - self.drag_offset
            screen = QApplication.primaryScreen().geometry()
            new_pos.setX(max(0, min(new_pos.x(), screen.width() - self.width())))
            new_pos.setY(max(0, min(new_pos.y(), screen.height() - self.height())))
            self.move(new_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.is_dragging_toolbar = False
        self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseReleaseEvent(event)

    def set_tool(self, tool: str):
        self._on_tool_clicked(tool)
