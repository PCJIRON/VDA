"""
UIED Button - Triggers UI Element Detection.

This button captures a screenshot, detects UI components using OpenCV,
and labels them using Qwen Vision LLM for 100% accurate template matching.
"""

from PyQt6.QtWidgets import QPushButton, QMenu, QDialog, QVBoxLayout, QLabel, QScrollArea, QWidget, QFrame, QHBoxLayout
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QTimer, QPoint, QPropertyAnimation, QEasingCurve, QVariantAnimation, pyqtSignal, QRect
from PyQt6.QtGui import QColor, QPainter, QBrush, QFont, QCursor, QPixmap, QPainterPath

from .base_button import BaseButton
import logging

logger = logging.getLogger(__name__)


class UIEDButton(BaseButton):
    """
    Button to trigger UI element detection.
    
    Icon: Grid/Component icon (Fluent Icon: \uE73A - GridView)
    States:
        - Normal: Grid icon
        - Hover: Glowing effect
        - Detecting: Spinning animation
        - Ready: Green glow (components detected)
    """
    
    def __init__(self, parent=None):
        super().__init__("\uE73A", parent)  # GridView icon
        self._is_detecting = False
        self._has_results = False
        self._detection_count = 0
        self._rotation_angle = 0
        self._pulse_alpha = 50
        
        # Tooltip
        self.setToolTip("UI Element Detection - Capture and label screen components")
        
        # Pulse animation for detecting state
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._on_pulse_timer)
        self._pulse_direction = 1
    
    def _on_pulse_timer(self):
        """Update pulse animation."""
        self._pulse_alpha += 30 * self._pulse_direction
        if self._pulse_alpha >= 80:
            self._pulse_direction = -1
        elif self._pulse_alpha <= 50:
            self._pulse_direction = 1
        self.update()
    
    def set_detecting(self, is_detecting: bool):
        """Set detecting state with animation."""
        self._is_detecting = is_detecting
        if is_detecting:
            self._start_rotation_animation()
            self._pulse_timer.start(50)  # 20 FPS pulse
        else:
            self._rotation_angle = 0
            self._pulse_timer.stop()
            self._pulse_alpha = 50
        self.update()
    
    def set_has_results(self, has_results: bool, count: int = 0):
        """Set state when detection results are available."""
        self._has_results = has_results
        self._detection_count = count
        self.update()
    
    def _start_rotation_animation(self):
        """Start rotating animation while detecting."""
        if hasattr(self, '_anim') and self._anim is not None:
            try:
                self._anim.stop()
            except:
                pass
        
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(1000)
        self._anim.setStartValue(0)
        self._anim.setEndValue(360)
        self._anim.setLoopCount(-1)  # Infinite loop
        
        def on_value_changed(value):
            self._rotation_angle = int(value)
            self.update()
        
        self._anim.valueChanged.connect(on_value_changed)
        self._anim.start()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background
        if self._has_results:
            # Green background when results ready
            bg_color = QColor("#16a34a") if not self._hovered else QColor("#15803d")
        elif self._is_detecting:
            # Pulsing blue while detecting
            bg_color = QColor(37, 99, 235, self._pulse_alpha)
        else:
            # Normal state
            bg_color = QColor(255, 255, 255, 40) if not self._hovered else QColor(255, 255, 255, 70)
        
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 8, 8)
        
        # Icon with optional rotation
        painter.save()
        
        if self._is_detecting:
            # Rotate around center
            center_x = self.width() / 2
            center_y = self.height() / 2
            painter.translate(center_x, center_y)
            painter.rotate(self._rotation_angle)
            painter.translate(-center_x, -center_y)
        
        # Icon color
        if self._has_results:
            painter.setPen(QColor("white"))
        elif self._is_detecting:
            painter.setPen(QColor("#60a5fa"))  # Light blue
        else:
            painter.setPen(QColor("white"))
        
        font = QFont("Segoe Fluent Icons")
        font.setPixelSize(16)
        font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.fluent_icon)
        
        painter.restore()
        
        # Draw count badge if has results
        if self._has_results and self._detection_count > 0:
            # Small badge at top-right
            badge_size = 14
            badge_x = self.width() - badge_size - 2
            badge_y = 2
            
            painter.setBrush(QBrush(QColor("#ef4444")))  # Red badge
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(badge_x, badge_y, badge_size, badge_size)
            
            # Number text
            painter.setPen(QColor("white"))
            font = QFont("Segoe UI")
            font.setPixelSize(9)
            font.setBold(True)
            painter.setFont(font)
            count_text = str(min(self._detection_count, 99))
            if self._detection_count > 99:
                count_text = "99+"
            
            text_rect = painter.boundingRect(
                QRect(badge_x, badge_y, badge_size, badge_size),
                Qt.AlignmentFlag.AlignCenter,
                count_text
            )
            
            # Center the text in the badge
            offset_x = (badge_size - text_rect.width()) / 2 - text_rect.x()
            offset_y = (badge_size - text_rect.height()) / 2 - text_rect.y()
            painter.drawText(
                int(badge_x + offset_x),
                int(badge_y + offset_y),
                count_text
            )


class UIEDResultsPanel(QDialog):
    """
    Panel showing detected UI components.
    
    Displays a grid of component thumbnails with labels.
    Allows user to select components for automation.
    """
    
    component_selected = pyqtSignal(dict)  # Emits selected component dict
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Popup
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(500, 400)
        
        self._components = []
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Main container
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 16px;
                border: 1px solid #e5e7eb;
            }
        """)
        
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #9333ea, stop:1 #2563eb);
                border-top-left-radius: 16px;
                border-top-right-radius: 16px;
            }
        """)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 16, 12)
        
        title = QLabel("🎯 Detected UI Components")
        title.setStyleSheet("color: white; font-weight: bold; font-size: 14px; background: transparent;")
        header_layout.addWidget(title)
        
        self.count_label = QLabel("")
        self.count_label.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 11px; background: transparent;")
        header_layout.addWidget(self.count_label)
        
        container_layout.addWidget(header)
        
        # Components grid
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { border: none; background: transparent; width: 6px; margin: 0px; }
            QScrollBar::handle:vertical { background: #d1d5db; min-height: 30px; border-radius: 3px; }
            QScrollBar::handle:vertical:hover { background: #9ca3af; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
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
        
        # Clear existing
        while self.components_layout.count():
            item = self.components_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add component cards
        for comp in components:
            card = self._create_component_card(comp)
            self.components_layout.addWidget(card)
        
        self.components_layout.addStretch()
    
    def _create_component_card(self, component: dict) -> QFrame:
        """Create a clickable card for a component."""
        card = QFrame()
        card.setFixedHeight(60)
        card.setStyleSheet("""
            QFrame {
                background-color: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
            }
            QFrame:hover {
                background-color: #eff6ff;
                border-color: #3b82f6;
            }
        """)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Click to select
        card.mousePressEvent = lambda e: self._on_component_clicked(component)
        
        layout = QHBoxLayout(card)
        layout.setContentsMargins(12, 8, 12, 8)
        
        # Type icon
        type_icon = self._get_type_icon(component.get('component_type', 'other'))
        icon_label = QLabel(type_icon)
        icon_label.setStyleSheet("""
            font-family: 'Segoe Fluent Icons';
            font-size: 20px;
            color: #6b7280;
            background: transparent;
        """)
        icon_label.setFixedWidth(30)
        layout.addWidget(icon_label)
        
        # Label and details
        info_layout = QVBoxLayout()
        
        label = QLabel(component.get('label', 'Unknown'))
        label.setStyleSheet("""
            font-weight: 600;
            color: #1f2937;
            background: transparent;
        """)
        info_layout.addWidget(label)
        
        details = QLabel(
            f"{component.get('component_type', 'other')} • "
            f"{component.get('width', 0)}x{component.get('height', 0)} • "
            f"({component.get('x', 0)}, {component.get('y', 0)})"
        )
        details.setStyleSheet("""
            font-size: 11px;
            color: #6b7280;
            background: transparent;
        """)
        info_layout.addWidget(details)
        
        layout.addLayout(info_layout, 1)
        
        # Confidence indicator
        confidence = component.get('confidence', 0)
        conf_color = "#16a34a" if confidence > 0.8 else "#eab308" if confidence > 0.5 else "#ef4444"
        
        conf_label = QLabel(f"{int(confidence * 100)}%")
        conf_label.setStyleSheet(f"""
            font-size: 11px;
            font-weight: bold;
            color: {conf_color};
            background: transparent;
        """)
        layout.addWidget(conf_label)
        
        return card
    
    def _get_type_icon(self, component_type: str) -> str:
        """Get Fluent icon for component type."""
        icons = {
            'button': '\uE700',  # Button
            'input': '\uE70B',  # Edit
            'text': '\uE8E6',  # Document
            'label': '\uE893',  # Label
            'icon': '\uE73A',  # GridView
            'image': '\uE73A',  # Picture
            'checkbox': '\uE73A',  # Checkbox
            'dropdown': '\uE70D',  # Dropdown
            'menu': '\uE700',  # Menu
            'tab': '\uE7C4',  # Tab
            'link': '\uE71B',  # Link
            'other': '\uE73A'  # Generic
        }
        return icons.get(component_type, '\uE73A')
    
    def _on_component_clicked(self, component: dict):
        """Handle component selection."""
        self.component_selected.emit(component)
        self.hide()
    
    def show_at_cursor(self):
        """Show panel at cursor position."""
        pos = QCursor.pos()
        # Adjust to show above cursor
        pos.setY(pos.y() - self.height() - 10)
        self.move(pos)
        self.show()
