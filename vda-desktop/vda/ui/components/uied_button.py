"""UIED Button - Triggers UI Element Detection.

Captures a screenshot and triggers UI detection with
animated states (detecting, ready, etc.).
"""

import logging

from PyQt6.QtCore import QRect, QRectF, Qt, QTimer, QVariantAnimation
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter

from .base_button import BaseButton

logger = logging.getLogger(__name__)


class UIEDButton(BaseButton):
    """Button to trigger UI element detection.

    States: Normal -> Detecting (spinning animation) -> Ready (green glow).
    """

    def __init__(self, parent=None):
        import os
        svg_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "resources",
                "icons",
                "crop.svg",
            )
        )
        super().__init__(svg_path, parent)
        self._is_detecting = False
        self._has_results = False
        self._detection_count = 0
        self._rotation_angle = 0
        self._pulse_alpha = 50
        self.setToolTip("Crop/Screenshot - Capture and label screen components")

        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._on_pulse_timer)
        self._pulse_direction = 1
        self._anim = None

    def _on_pulse_timer(self):
        self._pulse_alpha += 30 * self._pulse_direction
        if self._pulse_alpha >= 80:
            self._pulse_direction = -1
        elif self._pulse_alpha <= 50:
            self._pulse_direction = 1
        self.update()

    def set_detecting(self, is_detecting: bool):
        self._is_detecting = is_detecting
        if is_detecting:
            self._start_rotation_animation()
            self._pulse_timer.start(50)
        else:
            if self._anim is not None:
                try:
                    self._anim.stop()
                except Exception:
                    pass
                self._anim = None
            self._rotation_angle = 0
            self._pulse_timer.stop()
            self._pulse_alpha = 50
        self.update()

    def set_has_results(self, has_results: bool, count: int = 0):
        self._has_results = has_results
        self._detection_count = count
        self.update()

    def _start_rotation_animation(self):
        if self._anim is not None:
            try:
                self._anim.stop()
            except Exception:
                pass
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(1000)
        self._anim.setStartValue(0)
        self._anim.setEndValue(360)
        self._anim.setLoopCount(-1)
        self._anim.valueChanged.connect(lambda v: setattr(self, "_rotation_angle", int(v)) or self.update())
        self._anim.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._has_results:
            bg_color = QColor("#16a34a") if not self._hovered else QColor("#15803d")
        elif self._is_detecting:
            bg_color = QColor(37, 99, 235, self._pulse_alpha)
        else:
            bg_color = QColor("transparent") if not self._hovered else QColor(255, 255, 255, 30)

        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        # Circular radius
        r = self.rect().height() / 2.0
        painter.drawRoundedRect(self.rect(), r, r)

        painter.save()
        if self._is_detecting:
            cx, cy = self.width() / 2, self.height() / 2
            painter.translate(cx, cy)
            painter.rotate(self._rotation_angle)
            painter.translate(-cx, -cy)

        if self.svg_renderer and self.svg_renderer.isValid():
            icon_size = 18.0
            x = (self.width() - icon_size) / 2.0
            y = (self.height() - icon_size) / 2.0
            target_rect = QRectF(x, y, icon_size, icon_size)
            self.svg_renderer.render(painter, target_rect)
        else:
            icon_color = "white"
            if self._is_detecting:
                icon_color = "#60a5fa"
            painter.setPen(QColor(icon_color))
            font = QFont("Segoe Fluent Icons")
            font.setPixelSize(16)
            font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.fluent_icon)
        painter.restore()

        if self._has_results and self._detection_count > 0:
            self._draw_count_badge(painter)

    def _draw_count_badge(self, painter: QPainter):
        badge_size = 14
        badge_x = self.width() - badge_size - 2
        badge_y = 2
        painter.setBrush(QBrush(QColor("#ef4444")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(badge_x, badge_y, badge_size, badge_size)
        painter.setPen(QColor("white"))
        font = QFont("Segoe UI")
        font.setPixelSize(9)
        font.setBold(True)
        painter.setFont(font)
        count_text = str(min(self._detection_count, 99))
        if self._detection_count > 99:
            count_text = "99+"
        painter.drawText(QRect(badge_x, badge_y, badge_size, badge_size), Qt.AlignmentFlag.AlignCenter, count_text)
