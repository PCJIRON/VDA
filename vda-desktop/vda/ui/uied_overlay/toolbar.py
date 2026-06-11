"""Toolbar components for the UI‑ED overlay.

The toolbar mimics a Figma‑style floating toolbar that lets the user pick the
current editing tool (move, box, delete) and provides Done/Exit actions.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QToolButton,
    QHBoxLayout,
    QFrame,
    QPushButton,
    QGraphicsDropShadowEffect,
    QApplication,
)
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QSize
from PyQt6.QtGui import QColor, QCursor


class ToolButton(QToolButton):
    """Styled tool button for the toolbar."""

    def __init__(self, icon: str, tooltip: str, shortcut: str = "", parent=None):
        super().__init__(parent)
        self.setText(icon)
        self.setToolTip(f"{tooltip} ({shortcut})" if shortcut else tooltip)
        self.setFixedSize(50, 50)
        self.setIconSize(QSize(28, 28))
        self.setStyleSheet(
            """
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
            """
        )
        self.setCursor(Qt.CursorShape.PointingHandCursor)


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
                background-color: rgba(31, 41, 55, 240);
                border-radius: 16px;
                border: 2px solid #6366f1;
            }
            """
        )
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(12, 8, 12, 8)
        container_layout.setSpacing(6)

        self.move_btn = ToolButton("🖱️", "Move Tool", "V")
        self.move_btn.setCheckable(True)
        self.move_btn.setChecked(True)
        self.move_btn.clicked.connect(lambda: self._on_tool_clicked("move"))
        container_layout.addWidget(self.move_btn)

        self.box_btn = ToolButton("⬜", "Box Tool", "B")
        self.box_btn.setCheckable(True)
        self.box_btn.clicked.connect(lambda: self._on_tool_clicked("box"))
        container_layout.addWidget(self.box_btn)

        self.delete_btn = ToolButton("🗑️", "Delete Tool", "D")
        self.delete_btn.setCheckable(True)
        self.delete_btn.clicked.connect(lambda: self._on_tool_clicked("delete"))
        container_layout.addWidget(self.delete_btn)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setStyleSheet("background-color: #4b5563;")
        separator.setFixedWidth(2)
        container_layout.addWidget(separator)

        # Done button
        self.done_btn = QPushButton("✅ Done")
        self.done_btn.setFixedSize(100, 45)
        self.done_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #16a34a;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #15803d; }
            """
        )
        self.done_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.done_btn.clicked.connect(self._on_done_clicked)
        container_layout.addWidget(self.done_btn)

        # Exit button
        self.exit_btn = QPushButton("✕ Exit")
        self.exit_btn.setFixedSize(100, 45)
        self.exit_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #dc2626;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #b91c1c; }
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
