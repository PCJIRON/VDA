"""
Header widget for Qwen Desktop.

Port of qwen-code's Header.tsx component.
Displays gradient ASCII art logo, version, auth type, model, and working dir.
"""

import os
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QLinearGradient, QColor, QPainter, QPalette

from qwen_desktop.ui.theme_manager import ThemeManager


# Short ASCII logo (from qwen-code's AsciiArt.ts)
SHORT_ASCII_LOGO = r"""
  ____                      
 / __ \_      _____ _ __    
| |  | \ \ /\ / / _ \ '_ \  
| |__| |\ V  V /  __/ | | | 
 \___\_\ \_/\_/ \___|_| |_| 
"""


class GradientLabel(QLabel):
    """Label with gradient text effect."""

    def __init__(self, text: str, colors: list[str], parent=None):
        super().__init__(text, parent)
        self._gradient_colors = colors
        self.setFont(QFont("Consolas", 9, QFont.Weight.Bold))

    def paintEvent(self, event):
        """Custom paint with gradient text."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setFont(self.font())

        # Create gradient
        gradient = QLinearGradient(0, 0, self.width(), 0)
        for i, color_hex in enumerate(self._gradient_colors):
            gradient.setColorAt(
                i / max(len(self._gradient_colors) - 1, 1),
                QColor(color_hex),
            )

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(gradient)

        # Draw each line
        lines = self.text().split("\n")
        fm = painter.fontMetrics()
        y = fm.ascent()
        for line in lines:
            # Use the gradient as pen
            from PyQt6.QtGui import QPen
            pen = QPen()
            pen.setBrush(gradient)
            pen.setWidth(1)
            painter.setPen(pen)
            painter.drawText(4, y, line)
            y += fm.height()

        painter.end()


class HeaderWidget(QWidget):
    """Header widget matching qwen-code's Header component.

    Shows: ASCII logo | Version, Auth, Model, Directory
    """

    def __init__(self, parent=None) -> None:
        """Initialize header widget."""
        super().__init__(parent)

        self._version = "0.5.0"
        self._auth_type = "Not logged in"
        self._model = "qwen-coder-plus"
        self._working_dir = str(Path.home())

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the header UI."""
        tm = ThemeManager.instance()
        c = tm.colors
        s = tm.semantic

        self.setFixedHeight(110)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(12)

        # Left: ASCII Logo with gradient
        self.logo_label = GradientLabel(
            SHORT_ASCII_LOGO.strip(),
            c.GradientColors or ["#FFD700", "#da7959"],
        )
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.logo_label)

        # Right: Info panel in a bordered frame
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.Shape.Box)
        info_frame.setStyleSheet(f"""
            QFrame {{
                border: 1px solid {s.border.default};
                border-radius: 8px;
                background-color: {s.background.secondary};
                padding: 8px;
            }}
        """)

        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(12, 8, 12, 8)
        info_layout.setSpacing(4)

        # Title: >_ Qwen Desktop (v0.5.0)
        title_layout = QHBoxLayout()
        title_layout.setSpacing(4)

        prompt_label = QLabel(">_")
        prompt_label.setFont(QFont("Consolas", 14, QFont.Weight.Bold))
        prompt_label.setStyleSheet(f"color: {c.AccentYellow}; background: transparent; border: none;")
        title_layout.addWidget(prompt_label)

        title_label = QLabel("Qwen Desktop")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {c.AccentYellow}; background: transparent; border: none;")
        title_layout.addWidget(title_label)

        self.version_label = QLabel(f"(v{self._version})")
        self.version_label.setFont(QFont("Segoe UI", 10))
        self.version_label.setStyleSheet(f"color: {s.text.secondary}; background: transparent; border: none;")
        title_layout.addWidget(self.version_label)

        title_layout.addStretch()
        info_layout.addLayout(title_layout)

        # Spacer
        spacer = QLabel("")
        spacer.setFixedHeight(2)
        spacer.setStyleSheet("background: transparent; border: none;")
        info_layout.addWidget(spacer)

        # Auth & Model line
        self.auth_model_label = QLabel(f"{self._auth_type} | {self._model}")
        self.auth_model_label.setFont(QFont("Segoe UI", 10))
        self.auth_model_label.setStyleSheet(f"color: {s.text.secondary}; background: transparent; border: none;")
        info_layout.addWidget(self.auth_model_label)

        # Working directory
        self.dir_label = QLabel(self._shorten_path(self._working_dir))
        self.dir_label.setFont(QFont("Consolas", 9))
        self.dir_label.setStyleSheet(f"color: {s.text.secondary}; background: transparent; border: none;")
        info_layout.addWidget(self.dir_label)

        layout.addWidget(info_frame, 1)

        # Apply background
        self.setStyleSheet(f"""
            HeaderWidget {{
                background-color: {s.background.primary};
                border-bottom: 1px solid {s.border.default};
            }}
        """)

    def _shorten_path(self, path: str, max_len: int = 60) -> str:
        """Shorten a path for display.

        Args:
            path: Full path.
            max_len: Maximum characters.

        Returns:
            Shortened path string.
        """
        # Replace home dir with ~
        home = str(Path.home())
        if path.startswith(home):
            path = "~" + path[len(home):]

        if len(path) <= max_len:
            return path

        parts = path.split(os.sep)
        if len(parts) <= 3:
            return path[:max_len - 3] + "..."

        # Keep first and last 2 parts
        shortened = os.sep.join(parts[:2]) + os.sep + "..." + os.sep + os.sep.join(parts[-2:])
        if len(shortened) > max_len:
            return shortened[:max_len - 3] + "..."
        return shortened

    def set_version(self, version: str) -> None:
        """Update displayed version."""
        self._version = version
        self.version_label.setText(f"(v{version})")

    def set_auth_type(self, auth_type: str) -> None:
        """Update displayed auth type."""
        self._auth_type = auth_type
        self._update_auth_model()

    def set_model(self, model: str) -> None:
        """Update displayed model."""
        self._model = model
        self._update_auth_model()

    def set_working_directory(self, directory: str) -> None:
        """Update displayed working directory."""
        self._working_dir = directory
        self.dir_label.setText(self._shorten_path(directory))

    def _update_auth_model(self) -> None:
        """Update the auth/model label."""
        self.auth_model_label.setText(f"{self._auth_type} | {self._model}")
