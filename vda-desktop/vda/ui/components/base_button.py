import os
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor, QPainter, QBrush, QFont
from PyQt6.QtSvg import QSvgRenderer


class BaseButton(QPushButton):
    """Base button supporting both vector SVGs (QSvgRenderer) and traditional fonts with hover effects."""

    def __init__(self, icon_or_path="", parent=None, is_primary=False, is_green=False):
        super().__init__("", parent)
        self.is_primary = is_primary
        self.is_green = is_green
        self.fluent_icon = icon_or_path
        self.setFixedSize(36, 36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._hovered = False

        self.svg_renderer = None
        # Check if the icon is a path to an SVG file
        if isinstance(icon_or_path, str) and icon_or_path.endswith('.svg') and os.path.exists(icon_or_path):
            self.svg_renderer = QSvgRenderer(icon_or_path)

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
        if self.is_green:
            bg_color = QColor("#16a34a") if not self._hovered else QColor("#15803d")
        elif self.is_primary:
            bg_color = QColor("white") if not self._hovered else QColor("#e5e5e5")
        else:
            bg_color = QColor("transparent") if not self._hovered else QColor(255, 255, 255, 30)

        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        # Circular radius
        r = self.rect().height() / 2.0
        painter.drawRoundedRect(self.rect(), r, r)

        # Draw Icon (SVG or Font character)
        # If the button has text (e.g. stop mode square symbol \u25A0), render text instead of SVG
        if not self.text() and self.svg_renderer and self.svg_renderer.isValid():
            # Pad the icon inside the 36x36 circular button
            icon_size = 18.0
            x = (self.width() - icon_size) / 2.0
            y = (self.height() - icon_size) / 2.0
            target_rect = QRectF(x, y, icon_size, icon_size)
            self.svg_renderer.render(painter, target_rect)
        else:
            if self.is_primary:
                painter.setPen(QColor("black"))
            else:
                painter.setPen(QColor("white"))

            # Fallback to Segoe MDL2 Assets / Segoe Fluent Icons
            font = QFont("Segoe Fluent Icons")
            font.setPixelSize(16)
            font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
            font.insertSubstitution("Segoe Fluent Icons", "Segoe MDL2 Assets")

            painter.setFont(font)
            icon_text = self.text() if self.text() else self.fluent_icon
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, icon_text)
