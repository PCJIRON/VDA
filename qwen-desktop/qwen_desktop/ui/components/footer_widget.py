"""
Footer widget for Qwen Desktop.

Port of qwen-code's Footer.tsx component.
Shows keyboard shortcut hints, context usage, and status indicators.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QProgressBar,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from qwen_desktop.ui.theme_manager import ThemeManager


class ContextUsageBar(QProgressBar):
    """Compact context window usage bar."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextVisible(False)
        self.setFixedHeight(4)
        self.setFixedWidth(60)
        self.setRange(0, 100)
        self.setValue(0)
        self._apply_style()

    def _apply_style(self):
        """Apply theme styling."""
        tm = ThemeManager.instance()
        c = tm.colors
        self.setStyleSheet(f"""
            QProgressBar {{
                background-color: {c.Gray};
                border: none;
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background-color: {c.AccentBlue};
                border-radius: 2px;
            }}
        """)

    def set_usage(self, used: int, total: int) -> None:
        """Set context usage.

        Args:
            used: Tokens used.
            total: Total context window size.
        """
        if total > 0:
            pct = min(int(used / total * 100), 100)
            self.setValue(pct)

            # Change color based on usage
            tm = ThemeManager.instance()
            c = tm.colors
            if pct > 90:
                color = c.AccentRed
            elif pct > 70:
                color = c.AccentYellow
            else:
                color = c.AccentBlue

            self.setStyleSheet(f"""
                QProgressBar {{
                    background-color: {c.Gray};
                    border: none;
                    border-radius: 2px;
                }}
                QProgressBar::chunk {{
                    background-color: {color};
                    border-radius: 2px;
                }}
            """)


class FooterWidget(QWidget):
    """Footer bar matching qwen-code's Footer component.

    Layout: [shortcut hints] ────── [context usage | rate info]
    """

    def __init__(self, parent=None) -> None:
        """Initialize footer widget."""
        super().__init__(parent)
        self._setup_ui()
        self._ctrl_c_pressed = False

    def _setup_ui(self) -> None:
        """Set up the footer UI."""
        tm = ThemeManager.instance()
        c = tm.colors
        s = tm.semantic

        self.setFixedHeight(28)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 2, 12, 2)
        layout.setSpacing(8)

        # Left: Hint text
        self.hint_label = QLabel("? for shortcuts")
        self.hint_label.setFont(QFont("Segoe UI", 9))
        self.hint_label.setStyleSheet(f"color: {s.text.secondary};")
        layout.addWidget(self.hint_label)

        layout.addStretch()

        # Right: Context usage
        self.context_label = QLabel("")
        self.context_label.setFont(QFont("Segoe UI", 9))
        self.context_label.setStyleSheet(f"color: {s.text.accent};")
        layout.addWidget(self.context_label)

        self.context_bar = ContextUsageBar()
        self.context_bar.hide()
        layout.addWidget(self.context_bar)

        # Rate limit
        self.rate_label = QLabel("")
        self.rate_label.setFont(QFont("Segoe UI", 9))
        self.rate_label.setStyleSheet(f"color: {s.text.secondary};")
        layout.addWidget(self.rate_label)

        # Apply styling
        self.setStyleSheet(f"""
            FooterWidget {{
                background-color: {s.background.secondary};
                border-top: 1px solid {s.border.default};
            }}
        """)

    def set_hint(self, text: str) -> None:
        """Set the hint text on the left.

        Args:
            text: Hint text to display.
        """
        self.hint_label.setText(text)

    def show_exit_warning(self) -> None:
        """Show Ctrl+C exit warning."""
        tm = ThemeManager.instance()
        s = tm.semantic
        self.hint_label.setText("Press Ctrl+C again to exit.")
        self.hint_label.setStyleSheet(f"color: {s.status.warning};")

        # Reset after 1 second
        QTimer.singleShot(1500, self._reset_hint)

    def _reset_hint(self) -> None:
        """Reset hint to default."""
        tm = ThemeManager.instance()
        s = tm.semantic
        self.hint_label.setText("? for shortcuts")
        self.hint_label.setStyleSheet(f"color: {s.text.secondary};")

    def set_context_usage(self, used: int, total: int) -> None:
        """Set context window usage.

        Args:
            used: Tokens used.
            total: Total context window.
        """
        if total > 0:
            pct = used / total * 100
            self.context_label.setText(f"{used:,}/{total:,} tokens ({pct:.0f}%)")
            self.context_bar.set_usage(used, total)
            self.context_bar.show()
        else:
            self.context_label.setText("")
            self.context_bar.hide()

    def set_rate_limit(self, remaining: int, total: int = 1000) -> None:
        """Set rate limit display.

        Args:
            remaining: Remaining requests.
            total: Total requests allowed.
        """
        tm = ThemeManager.instance()
        c = tm.colors

        if remaining < 10:
            color = c.AccentRed
        elif remaining < 100:
            color = c.AccentYellow
        else:
            color = c.AccentGreen

        self.rate_label.setText(f"API: {remaining}/{total}")
        self.rate_label.setStyleSheet(f"color: {color};")
