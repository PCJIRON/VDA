from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, QRect, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QWidget


class _IconButton(QPushButton):
    def __init__(self, text, tooltip="", parent=None):
        super().__init__(text, parent)
        self.setFixedSize(36, 36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._hovered = False
        if tooltip:
            self.setToolTip(tooltip)

    def enterEvent(self, e):
        self._hovered = True
        self.update()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._hovered = False
        self.update()
        super().leaveEvent(e)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        bg = QColor(255, 255, 255, 30) if self._hovered else QColor("transparent")
        p.setBrush(bg)
        p.setPen(Qt.PenStyle.NoPen)
        r = self.height() / 2.0
        p.drawRoundedRect(self.rect(), r, r)
        font = QFont("Segoe Fluent Icons, Segoe MDL2 Assets")
        font.setPixelSize(16)
        p.setFont(font)
        p.setPen(QColor("white"))
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.text())


class _SendButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__("", parent)
        self.setFixedSize(36, 36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._hovered = False
        self._enabled = False

    def enterEvent(self, e):
        self._hovered = True
        self.update()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._hovered = False
        self.update()
        super().leaveEvent(e)

    def set_button_enabled(self, enabled: bool):
        self._enabled = enabled
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self._enabled:
            bg = QColor("white") if not self._hovered else QColor("#e5e5e5")
        else:
            bg = QColor(255, 255, 255, 60)
        p.setBrush(bg)
        p.setPen(Qt.PenStyle.NoPen)
        r = self.height() / 2.0
        p.drawRoundedRect(self.rect(), r, r)
        p.setPen(QColor("black") if self._enabled else QColor(0, 0, 0, 100))
        font = QFont("Segoe Fluent Icons, Segoe MDL2 Assets")
        font.setPixelSize(16)
        p.setFont(font)
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "\u2191")


class FloatingWidget(QWidget):
    send_requested = pyqtSignal(str)
    settings_requested = pyqtSignal()
    voice_requested = pyqtSignal()
    vision_requested = pyqtSignal()
    crop_requested = pyqtSignal()

    COLLAPSED_W = 64
    EXPANDED_W = 460
    HEIGHT = 64

    def __init__(self, parent=None):
        super().__init__(parent)
        self._expanded = False
        self._animating = False
        self.setFixedHeight(self.HEIGHT)
        self.resize(self.COLLAPSED_W, self.HEIGHT)

        self._input = QLineEdit(self)
        self._input.setPlaceholderText("Ask anything...")
        self._input.setStyleSheet("""
            QLineEdit {
                background: transparent; border: none; outline: none;
                color: white; font-size: 15px; padding: 0 8px;
            }
            QLineEdit::placeholder { color: #737373; }
        """)
        self._input.setVisible(False)
        self._input.returnPressed.connect(self._on_send)

        self._send_btn = _SendButton(self)
        self._send_btn.setVisible(False)
        self._send_btn.clicked.connect(self._on_send)

        btn_defs = [
            ("\u2699", "Settings", self.settings_requested),
            ("\uD83C\uDF99", "Voice Input", self.voice_requested),
            ("\uD83D\uDC41", "Vision", self.vision_requested),
            ("\uD83D\uDCCB", "Crop/Screenshot", self.crop_requested),
        ]
        self._tool_btns = []
        for icon, tip, sig in btn_defs:
            btn = _IconButton(icon, tip, self)
            btn.setVisible(False)
            btn.clicked.connect(sig.emit)
            self._tool_btns.append(btn)

        self.setMouseTracking(True)

    def is_expanded(self):
        return self._expanded

    def set_expanded(self, expanded: bool):
        self._expanded = expanded
        target_w = self.EXPANDED_W if expanded else self.COLLAPSED_W
        self._animating = True
        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(300)
        self.anim.setStartValue(self.geometry())
        end_geo = QRect(self.x(), self.y(), target_w, self.HEIGHT)
        self.anim.setEndValue(end_geo)
        self.anim.setEasingCurve(QEasingCurve.Type.OutBack)
        self.anim.finished.connect(self._on_anim_done)
        self.anim.start()

    def _on_anim_done(self):
        self._animating = False
        self._input.setVisible(self._expanded)
        self._send_btn.setVisible(self._expanded)
        for btn in self._tool_btns:
            btn.setVisible(self._expanded)
        if self._expanded:
            self._input.setFocus()
            self._input.selectAll()

    def _on_send(self):
        text = self._input.text().strip()
        if text:
            self.send_requested.emit(text)
            self._input.clear()

    def enterEvent(self, e):
        if not self._expanded and not self._animating:
            self.set_expanded(True)
        super().enterEvent(e)

    def leaveEvent(self, e):
        if self._expanded and not self._animating and not self._input.hasFocus():
            self.set_expanded(False)
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.pos()
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if e.buttons() & Qt.MouseButton.LeftButton:
            if hasattr(self, "_drag_pos"):
                parent = self.parent()
                if parent:
                    parent.move(parent.pos() + e.pos() - self._drag_pos)
        super().mouseMoveEvent(e)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        r = self.HEIGHT / 2.0
        path.addRoundedRect(0, 0, self.width(), self.HEIGHT, r, r)
        p.fillPath(path, QColor("#1e1e24"))
        pen = QPen(QColor("#404040"))
        pen.setWidthF(1)
        p.setPen(pen)
        p.drawPath(path)

        if not self._expanded:
            font = QFont("Segoe Fluent Icons, Segoe MDL2 Assets")
            font.setPixelSize(24)
            p.setFont(font)
            p.setPen(QColor("white"))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "\u2728")

        super().paintEvent(e)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if self._expanded:
            self._input.setGeometry(50, 0, self.width() - 260, self.HEIGHT)
            x = self.width() - 210
            for i, btn in enumerate(self._tool_btns):
                btn.move(x + i * 42, (self.HEIGHT - 36) // 2)
            self._send_btn.move(self.width() - 52, (self.HEIGHT - 36) // 2)
