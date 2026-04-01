from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QColor, QPainter, QBrush, QFont

class BaseButton(QPushButton):
    """Base button with translucent hover effects for icons."""
    def __init__(self, fluent_icon="", parent=None, is_primary=False, is_green=False, is_stop=False):
        super().__init__("", parent)
        self.is_primary = is_primary
        self.is_green = is_green
        self.is_stop = is_stop  # Special stop button mode
        self.fluent_icon = fluent_icon
        self.setFixedSize(36, 36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
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

        # Background
        if self.is_stop:
            # Stop button: Solid red background
            bg_color = QColor("#ef4444") if not self._hovered else QColor("#dc2626")
        elif self.is_green:
            bg_color = QColor("#10b981") if not self._hovered else QColor("#059669")
        elif self.is_primary:
            bg_color = QColor(0, 0, 0, 80) if not self._hovered else QColor(0, 0, 0, 110)
        else:
            bg_color = QColor(0, 0, 0, 40) if not self._hovered else QColor(0, 0, 0, 70)

        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        
        if self.is_stop:
            # Stop button: Rectangle (no rounded corners)
            painter.drawRect(self.rect())
        else:
            # Normal buttons: Rounded rectangle
            painter.drawRoundedRect(self.rect(), 8, 8)

        # Icon
        painter.setPen(QColor("white"))

        # Use Windows native high-quality icon fonts
        font = QFont("Segoe Fluent Icons")
        font.setPixelSize(16)
        font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)

        # Fallback to MDL2 Assets if Fluent isn't available (Win 10 vs Win 11)
        font.insertSubstitution("Segoe Fluent Icons", "Segoe MDL2 Assets")

        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.fluent_icon)
