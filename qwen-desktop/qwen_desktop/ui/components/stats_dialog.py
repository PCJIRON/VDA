"""
Stats Dialog for displaying context usage and rate limits.

Matches the qwen-code /stats command functionality.
"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QFrame,
    QPushButton,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from qwen_desktop.ui.theme_manager import ThemeManager


class StatsDialog(QDialog):
    """Dialog showing API usage statistics."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Usage Statistics")
        self.setMinimumWidth(400)
        
        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self):
        """Set up the UI components."""
        tm = ThemeManager.instance()
        c = tm.colors
        s = tm.semantic

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header
        header = QLabel("📈 Session Statistics")
        header.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        header.setStyleSheet(f"color: {s.text.primary};")
        layout.addWidget(header)

        # Context Window Section
        context_group = QFrame()
        context_group.setStyleSheet(f"""
            QFrame {{
                background-color: {s.background.elevated};
                border: 1px solid {s.border.default};
                border-radius: 8px;
            }}
        """)
        c_layout = QVBoxLayout(context_group)
        c_layout.setContentsMargins(16, 16, 16, 16)
        c_layout.setSpacing(8)

        # Context Title
        c_title_layout = QHBoxLayout()
        ctx_title = QLabel("Context Window Usage")
        ctx_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        ctx_title.setStyleSheet(f"color: {s.text.primary};")
        c_title_layout.addWidget(ctx_title)

        ctx_value = QLabel("45K / 128K (35%)")
        ctx_value.setFont(QFont("Consolas", 10))
        ctx_value.setStyleSheet(f"color: {c.AccentBlue};")
        c_title_layout.addWidget(ctx_value, alignment=Qt.AlignmentFlag.AlignRight)
        c_layout.addLayout(c_title_layout)

        # Context Progress Bar
        ctx_bar = QProgressBar()
        ctx_bar.setRange(0, 100)
        ctx_bar.setValue(35)
        ctx_bar.setTextVisible(False)
        ctx_bar.setFixedHeight(8)
        ctx_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {s.background.input};
                border: none;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {c.AccentBlue};
                border-radius: 4px;
            }}
        """)
        c_layout.addWidget(ctx_bar)
        layout.addWidget(context_group)

        # Rate Limit Section
        rate_group = QFrame()
        rate_group.setStyleSheet(f"""
            QFrame {{
                background-color: {s.background.elevated};
                border: 1px solid {s.border.default};
                border-radius: 8px;
            }}
        """)
        r_layout = QVBoxLayout(rate_group)
        r_layout.setContentsMargins(16, 16, 16, 16)
        r_layout.setSpacing(8)

        # Rate Limits Title
        r_title_layout = QHBoxLayout()
        rl_title = QLabel("API Rate Limits")
        rl_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        rl_title.setStyleSheet(f"color: {s.text.primary};")
        r_title_layout.addWidget(rl_title)
        
        rl_value = QLabel("940 / 1000 remaining")
        rl_value.setFont(QFont("Consolas", 10))
        rl_value.setStyleSheet(f"color: {c.AccentGreen};")
        r_title_layout.addWidget(rl_value, alignment=Qt.AlignmentFlag.AlignRight)
        r_layout.addLayout(r_title_layout)

        # Rate Limits Progress Bar
        rl_bar = QProgressBar()
        rl_bar.setRange(0, 100)
        rl_bar.setValue(94)
        rl_bar.setTextVisible(False)
        rl_bar.setFixedHeight(8)
        rl_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {s.background.input};
                border: none;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {c.AccentGreen};
                border-radius: 4px;
            }}
        """)
        r_layout.addWidget(rl_bar)
        layout.addWidget(rate_group)

        # Close button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.setMinimumWidth(80)
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c.AccentBlue};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {c.LightBlue};
            }}
        """)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)

    def _apply_styles(self):
        """Apply base dialog styles."""
        tm = ThemeManager.instance()
        s = tm.semantic
        
        self.setStyleSheet(f"""
            StatsDialog {{
                background-color: {s.background.primary};
            }}
        """)
