"""Panel showing detected UI components.

Displays a grid of component thumbnails with labels.
Allows user to select components for automation.
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QScrollArea, QWidget, QFrame, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor


class UIEDResultsPanel(QDialog):
    """Panel showing detected UI components with thumbnails and labels."""

    component_selected = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(500, 400)
        self._components = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        container = QFrame()
        container.setStyleSheet("""
            QFrame { background-color: white; border-radius: 16px; border: 1px solid #e5e7eb; }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #9333ea, stop:1 #2563eb);
                border-top-left-radius: 16px; border-top-right-radius: 16px;
            }
        """)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 16, 12)
        title = QLabel("\U0001f3af Detected UI Components")
        title.setStyleSheet("color: white; font-weight: bold; font-size: 14px; background: transparent;")
        header_layout.addWidget(title)
        self.count_label = QLabel("")
        self.count_label.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 11px; background: transparent;")
        header_layout.addWidget(self.count_label)
        container_layout.addWidget(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { border: none; background: transparent; width: 6px; }
            QScrollBar::handle:vertical { background: #d1d5db; min-height: 30px; border-radius: 3px; }
            QScrollBar::handle:vertical:hover { background: #9ca3af; }
        """)
        self.components_widget = QWidget()
        self.components_layout = QVBoxLayout(self.components_widget)
        self.components_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.components_layout.setContentsMargins(12, 12, 12, 12)
        self.components_layout.setSpacing(8)
        self.scroll.setWidget(self.components_widget)
        container_layout.addWidget(self.scroll)
        layout.addWidget(container)

    def set_components(self, components: list):
        """Set and display detected components."""
        self._components = components
        self.count_label.setText(f"{len(components)} elements detected")
        while self.components_layout.count():
            item = self.components_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for comp in components:
            self.components_layout.addWidget(self._create_component_card(comp))
        self.components_layout.addStretch()

    def _create_component_card(self, component: dict) -> QFrame:
        """Create a clickable card for a component."""
        card = QFrame()
        card.setFixedHeight(60)
        card.setStyleSheet("""
            QFrame { background-color: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; }
            QFrame:hover { background-color: #eff6ff; border-color: #3b82f6; }
        """)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.mousePressEvent = lambda e: self._on_component_clicked(component)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(12, 8, 12, 8)
        icon = self._get_type_icon(component.get("component_type", "other"))
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-family: 'Segoe Fluent Icons'; font-size: 20px; color: #6b7280; background: transparent;")
        icon_label.setFixedWidth(30)
        layout.addWidget(icon_label)

        info = QVBoxLayout()
        lbl = QLabel(component.get("label", "Unknown"))
        lbl.setStyleSheet("font-weight: 600; color: #1f2937; background: transparent;")
        info.addWidget(lbl)
        details = QLabel(f"{component.get('component_type', 'other')} \u2022 {component.get('width', 0)}x{component.get('height', 0)} ({component.get('x', 0)}, {component.get('y', 0)})")
        details.setStyleSheet("font-size: 11px; color: #6b7280; background: transparent;")
        info.addWidget(details)
        layout.addLayout(info, 1)

        confidence = component.get("confidence", 0)
        conf_color = "#16a34a" if confidence > 0.8 else "#eab308" if confidence > 0.5 else "#ef4444"
        conf_label = QLabel(f"{int(confidence * 100)}%")
        conf_label.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {conf_color}; background: transparent;")
        layout.addWidget(conf_label)
        return card

    @staticmethod
    def _get_type_icon(component_type: str) -> str:
        icons = {
            "button": "\uE700", "input": "\uE70B", "text": "\uE8E6",
            "label": "\uE893", "icon": "\uE73A", "image": "\uE73A",
            "checkbox": "\uE73A", "dropdown": "\uE70D", "menu": "\uE700",
            "tab": "\uE7C4", "link": "\uE71B", "other": "\uE73A",
        }
        return icons.get(component_type, "\uE73A")

    def _on_component_clicked(self, component: dict):
        self.component_selected.emit(component)
        self.hide()

    def show_at_cursor(self):
        pos = QCursor.pos()
        pos.setY(pos.y() - self.height() - 10)
        self.move(pos)
        self.show()
