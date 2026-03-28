"""
Typing indicator component.

Port of qwen-code's LoadingIndicator.tsx.
Shows spinner + thinking text + elapsed time + token count.
"""

import time

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont

from qwen_desktop.ui.theme_manager import ThemeManager


# Loading phrases (from qwen-code's Tips.tsx)
LOADING_PHRASES = [
    "Thinking...",
    "Analyzing your request...",
    "Generating response...",
    "Processing...",
    "Working on it...",
    "Almost there...",
    "Crunching the code...",
    "Consulting the AI...",
]


class TypingIndicator(QFrame):
    """Animated typing indicator matching qwen-code's LoadingIndicator.

    Shows: [spinner] Thinking... (3.2s)
    """

    def __init__(self, parent: None = None) -> None:
        """Initialize the typing indicator.

        Args:
            parent: Parent widget.
        """
        super().__init__(parent)

        self._start_time: float = 0
        self._phrase_index: int = 0
        self._spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self._spinner_index: int = 0

        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self) -> None:
        """Set up the UI components."""
        tm = ThemeManager.instance()
        c = tm.colors
        s = tm.semantic

        self.setFrameShape(QFrame.Shape.NoFrame)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(8)

        # Spinner
        self.spinner_label = QLabel(self._spinner_frames[0])
        self.spinner_label.setFont(QFont("Consolas", 14))
        self.spinner_label.setStyleSheet(f"color: {c.AccentYellow}; background: transparent;")
        self.spinner_label.setFixedWidth(20)
        layout.addWidget(self.spinner_label)

        # Thinking text
        self.text_label = QLabel("Thinking...")
        self.text_label.setFont(QFont("Segoe UI", 11))
        self.text_label.setStyleSheet(f"color: {s.text.secondary}; background: transparent;")
        layout.addWidget(self.text_label)

        layout.addStretch()

        # Elapsed time
        self.time_label = QLabel("")
        self.time_label.setFont(QFont("Consolas", 10))
        self.time_label.setStyleSheet(f"color: {c.Comment}; background: transparent;")
        layout.addWidget(self.time_label)

        # Animation timer
        self.timer = QTimer()
        self.timer.timeout.connect(self._animate)

        # Phrase change timer
        self.phrase_timer = QTimer()
        self.phrase_timer.timeout.connect(self._change_phrase)

    def _apply_styles(self) -> None:
        """Apply styles to the indicator."""
        tm = ThemeManager.instance()
        s = tm.semantic

        self.setStyleSheet(f"""
            TypingIndicator {{
                background-color: {s.background.secondary};
                border-top: 1px solid {s.border.subtle};
            }}
        """)

    def _animate(self) -> None:
        """Animate the spinner and update elapsed time."""
        tm = ThemeManager.instance()
        c = tm.colors

        # Update spinner
        self._spinner_index = (self._spinner_index + 1) % len(self._spinner_frames)
        self.spinner_label.setText(self._spinner_frames[self._spinner_index])

        # Color cycle for spinner
        colors = [c.AccentYellow, c.AccentBlue, c.AccentCyan, c.AccentGreen]
        color = colors[self._spinner_index % len(colors)]
        self.spinner_label.setStyleSheet(f"color: {color}; background: transparent;")

        # Update elapsed time
        if self._start_time > 0:
            elapsed = time.time() - self._start_time
            self.time_label.setText(f"{elapsed:.1f}s")

    def _change_phrase(self) -> None:
        """Change the loading phrase."""
        self._phrase_index = (self._phrase_index + 1) % len(LOADING_PHRASES)
        self.text_label.setText(LOADING_PHRASES[self._phrase_index])

    def show_indicator(self) -> None:
        """Show the typing indicator and start animation."""
        self._start_time = time.time()
        self._spinner_index = 0
        self._phrase_index = 0
        self.text_label.setText(LOADING_PHRASES[0])
        self.time_label.setText("0.0s")

        self.show()

        if not self.timer.isActive():
            self.timer.start(100)  # Spinner: every 100ms

        if not self.phrase_timer.isActive():
            self.phrase_timer.start(4000)  # Change phrase every 4s

    def hide_indicator(self) -> None:
        """Hide the typing indicator and stop animation."""
        self.hide()
        self.timer.stop()
        self.phrase_timer.stop()
        self._start_time = 0

    def closeEvent(self, event) -> None:
        """Handle widget close event.

        Args:
            event: Close event.
        """
        self.timer.stop()
        self.phrase_timer.stop()
        super().closeEvent(event)
