"""ThinkingPanel — expandable/collapsible step display for agent loop visualization.

Shows step-by-step reasoning with status icons (pending/running/success/failed)
and handles doom loop warnings and permission requests per D-01 through D-04.

Per D-01: Expandable panel below chat input, collapsible with QPropertyAnimation.
Per D-02: Medium detail: step label + status icon + one-line detail.
Per D-03: Step-by-step updates (not real-time streaming).
Per D-04: Doom loop = pause + red badge + Resume/Abort buttons.
"""

import logging

from PyQt6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    Qt,
    pyqtSignal,
)
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)

# Status icon map: (symbol, color_hex)
STATUS_ICONS = {
    "pending": ("○", "#9ca3af"),    # gray
    "running": ("⏳", "#3b82f6"),    # blue
    "success": ("✅", "#22c55e"),    # green
    "failed":  ("❌", "#ef4444"),    # red
    "warning": ("⚠️", "#f59e0b"),    # amber
}


class StepWidget(QFrame):
    """Single step display widget with icon, label, and detail.

    Compact design: ~24px height per step, 4px padding.
    """

    def __init__(self, label: str, detail: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setFixedHeight(28)
        self.setContentsMargins(0, 0, 0, 0)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(6)

        # Status icon
        self.icon_label = QLabel("○")
        self.icon_label.setFixedWidth(20)
        self.icon_label.setStyleSheet("color: #9ca3af; font-size: 14px;")
        layout.addWidget(self.icon_label)

        # Step label
        self.label_widget = QLabel(label)
        self.label_widget.setStyleSheet(
            "color: #e5e7eb; font-size: 12px; font-weight: 500;"
        )
        self.label_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        layout.addWidget(self.label_widget)

        # Detail text (one-line)
        self.detail_label = QLabel(detail)
        self.detail_label.setStyleSheet("color: #9ca3af; font-size: 11px;")
        self.detail_label.setMaximumWidth(200)
        self.detail_label.setWordWrap(False)
        layout.addWidget(self.detail_label)

        self.setStyleSheet(
            "StepWidget { background: transparent; border: none; }"
        )

    def set_status(self, status: str) -> None:
        """Update the status icon and color.

        Args:
            status: One of "pending", "running", "success", "failed", "warning".
        """
        icon, color = STATUS_ICONS.get(status, ("○", "#9ca3af"))
        self.icon_label.setText(icon)
        self.icon_label.setStyleSheet(f"color: {color}; font-size: 14px;")

    def set_detail(self, text: str) -> None:
        """Update the one-line detail text."""
        self.detail_label.setText(text)


class ThinkingPanel(QWidget):
    """Expandable/collapsible panel showing agent reasoning steps.

    Placed below the chat input area in FloatingAssistant. Shows step
    labels with status icons, doom loop warnings, and permission prompts.

    Signals:
        resume_requested: Emitted when user clicks Resume button.
        abort_requested: Emitted when user clicks Abort button.
        permission_response: (tool_name, allowed) when user clicks Allow/Deny.
    """

    resume_requested = pyqtSignal()
    abort_requested = pyqtSignal()
    permission_response = pyqtSignal(str, bool)

    PANEL_COLLAPSED = 36
    PANEL_MAX = 250
    ANIMATION_DURATION = 200

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._expanded = False
        self._doom_loop_active = False
        self._steps: list[StepWidget] = []

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header toggle button
        self._toggle_btn = QPushButton("🤔 Thinking  ▼")
        self._toggle_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.08);
                color: #e5e7eb;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 600;
                text-align: left;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.14);
            }
        """)
        self._toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_btn.clicked.connect(self.toggle)
        layout.addWidget(self._toggle_btn)

        # Scrollable step content area
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.05);
                width: 4px;
                border-radius: 2px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.2);
                border-radius: 2px;
            }
        """)

        # Content widget inside scroll area
        self._content_widget = QWidget()
        self._content_widget.setStyleSheet("background: transparent;")
        self._steps_layout = QVBoxLayout(self._content_widget)
        self._steps_layout.setContentsMargins(4, 4, 4, 4)
        self._steps_layout.setSpacing(2)
        self._steps_layout.addStretch()

        self._scroll_area.setWidget(self._content_widget)
        layout.addWidget(self._scroll_area)

        # Doom loop warning section (hidden by default)
        self._doom_loop_widget = QFrame()
        self._doom_loop_widget.setStyleSheet("""
            QFrame {
                background: rgba(239, 68, 68, 0.15);
                border: 1px solid #ef4444;
                border-radius: 6px;
            }
        """)
        doom_layout = QVBoxLayout(self._doom_loop_widget)
        doom_layout.setContentsMargins(8, 6, 8, 6)
        doom_layout.setSpacing(4)

        self._doom_label = QLabel("")
        self._doom_label.setStyleSheet(
            "color: #fca5a5; font-size: 12px; font-weight: 600; border: none;"
        )
        self._doom_label.setWordWrap(True)
        doom_layout.addWidget(self._doom_label)

        doom_btn_layout = QHBoxLayout()
        doom_btn_layout.setSpacing(8)

        self._resume_btn = QPushButton("▶ Resume")
        self._resume_btn.setStyleSheet("""
            QPushButton {
                background: #16a34a;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover { background: #15803d; }
        """)
        self._resume_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._resume_btn.clicked.connect(self.resume_requested.emit)
        doom_btn_layout.addWidget(self._resume_btn)

        self._abort_btn = QPushButton("✕ Abort")
        self._abort_btn.setStyleSheet("""
            QPushButton {
                background: #dc2626;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover { background: #b91c1c; }
        """)
        self._abort_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._abort_btn.clicked.connect(self.abort_requested.emit)
        doom_btn_layout.addWidget(self._abort_btn)

        doom_btn_layout.addStretch()
        doom_layout.addLayout(doom_btn_layout)
        self._doom_loop_widget.hide()
        layout.addWidget(self._doom_loop_widget)

        # Permission request bar (hidden by default)
        self._permission_widget = QFrame()
        self._permission_widget.setStyleSheet("""
            QFrame {
                background: rgba(99, 102, 241, 0.15);
                border: 1px solid #6366f1;
                border-radius: 6px;
            }
        """)
        perm_layout = QVBoxLayout(self._permission_widget)
        perm_layout.setContentsMargins(8, 6, 8, 6)
        perm_layout.setSpacing(4)

        self._perm_label = QLabel("")
        self._perm_label.setStyleSheet(
            "color: #c7d2fe; font-size: 12px; font-weight: 500; border: none;"
        )
        self._perm_label.setWordWrap(True)
        perm_layout.addWidget(self._perm_label)

        perm_btn_layout = QHBoxLayout()
        perm_btn_layout.setSpacing(8)

        self._allow_btn = QPushButton("✓ Allow")
        self._allow_btn.setStyleSheet("""
            QPushButton {
                background: #16a34a;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover { background: #15803d; }
        """)
        self._allow_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._allow_btn.clicked.connect(self._on_allow)
        perm_btn_layout.addWidget(self._allow_btn)

        self._deny_btn = QPushButton("✕ Deny")
        self._deny_btn.setStyleSheet("""
            QPushButton {
                background: #dc2626;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover { background: #b91c1c; }
        """)
        self._deny_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._deny_btn.clicked.connect(self._on_deny)
        perm_btn_layout.addWidget(self._deny_btn)

        self._current_perm_tool = ""
        perm_btn_layout.addStretch()
        perm_layout.addLayout(perm_btn_layout)
        self._permission_widget.hide()
        layout.addWidget(self._permission_widget)

        # Animation
        self._animation = QPropertyAnimation(self, b"maximumHeight")
        self._animation.setDuration(self.ANIMATION_DURATION)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Start collapsed — only the toggle button is visible
        self.setMinimumHeight(36)
        self.setMaximumHeight(36)

    # ---- Public API ----

    def add_step(self, label: str, description: str = "") -> None:
        """Add a new step widget to the panel.

        Args:
            label: Short step name (e.g. "Search the web").
            description: One-line detail about what the step is doing.
        """
        step = StepWidget(label, description)
        # Insert before the stretch
        self._steps_layout.insertWidget(
            self._steps_layout.count() - 1, step
        )
        self._steps.append(step)

        # Auto-scroll to bottom
        self._scroll_to_bottom()

    def update_step(
        self, label: str, status: str, result_preview: str = ""
    ) -> None:
        """Update a step's status icon and detail text.

        Per D-03: step-by-step updates (not streaming).

        Args:
            label: Label of the step to update (matched by text).
            status: One of "pending", "running", "success", "failed", "warning".
            result_preview: Optional result text to show as detail.
        """
        for step in self._steps:
            if step.label_widget.text() == label:
                step.set_status(status)
                if result_preview:
                    step.set_detail(result_preview)
                return
        logger.debug(
            "[ThinkingPanel] Step '%s' not found for status update", label
        )

    def set_plan(self, steps: list[dict]) -> None:
        """Clear current steps and populate with plan steps as pending.

        Args:
            steps: List of step dicts, each with at least a "step" key.
        """
        self.clear()
        for step_data in steps:
            step_label = step_data.get("step", "Unknown step")
            tool = step_data.get("tool", "")
            detail = f"Using {tool}" if tool else ""
            self.add_step(step_label, detail)
            # Mark as pending (gray ○)
            for sw in self._steps:
                if sw.label_widget.text() == step_label:
                    sw.set_status("pending")
                    break

    def show_doom_loop(self, tool_name: str, args_summary: str) -> None:
        """Display doom loop warning with Resume/Abort buttons.

        Per D-04: red warning badge + Resume/Abort buttons.

        Args:
            tool_name: Name of the tool caught in the loop.
            args_summary: Summary of tool arguments.
        """
        self._doom_loop_active = True
        self._doom_label.setText(
            f"⚠️ Doom loop detected: {tool_name} ({args_summary})"
        )
        self._doom_loop_widget.show()

        # Expand if collapsed
        if not self._expanded:
            self.toggle()

    def show_permission_request(
        self, tool_name: str, args: str, agent_type: str
    ) -> None:
        """Display an inline permission request with Allow/Deny buttons.

        Args:
            tool_name: Name of the tool requiring permission.
            args: Tool arguments for context.
            agent_type: Type of agent making the request.
        """
        self._current_perm_tool = tool_name
        self._perm_label.setText(
            f"🔒 {agent_type} agent wants to use '{tool_name}': {args}"
        )
        self._permission_widget.show()

        # Expand if collapsed
        if not self._expanded:
            self.toggle()

    def clear(self) -> None:
        """Remove all step widgets, hide doom loop and permission sections."""
        # Remove all step widgets
        for step in self._steps:
            self._steps_layout.removeWidget(step)
            step.deleteLater()
        self._steps.clear()

        # Hide doom loop and permission
        self._doom_loop_active = False
        self._doom_loop_widget.hide()
        self._permission_widget.hide()

    def toggle(self) -> None:
        """Animate collapse/expand using QPropertyAnimation.

        Per D-01: 200ms, OutCubic easing.
        Collapsed state keeps the toggle button visible (36px) so the user
        can re-expand the panel at any time.
        """
        self._animation.stop()

        if self._expanded:
            # Collapse back to toggle button only
            self._animation.setStartValue(self.maximumHeight())
            self._animation.setEndValue(self.PANEL_COLLAPSED)
            self._animation.finished.connect(self._on_collapsed)
            self._toggle_btn.setText("🤔 Thinking  ▲")
        else:
            # Expand to full content height (toggle button + steps)
            content_height = self._calculate_content_height() + self.PANEL_COLLAPSED
            self._animation.setStartValue(self.PANEL_COLLAPSED)
            self._animation.setEndValue(content_height)
            self.setMaximumHeight(content_height)
            self._toggle_btn.setText("🤔 Thinking  ▼")

        self._expanded = not self._expanded
        self._animation.start()

    # ---- Internal helpers ----

    def _calculate_content_height(self) -> int:
        """Calculate the total content height for the expanded state.

        Returns:
            Height in pixels, clamped to PANEL_MAX.
        """
        height = 0

        # Step widgets
        step_count = len(self._steps)
        if step_count > 0:
            height += step_count * 30  # 28px step + 2px spacing

        # Doom loop widget if visible
        if self._doom_loop_widget.isVisible():
            height += 60

        # Permission widget if visible
        if self._permission_widget.isVisible():
            height += 60

        # Padding
        height += 12

        return min(height, self.PANEL_MAX)

    def _on_collapsed(self) -> None:
        """Clean up after collapse animation completes — keep toggle button visible."""
        try:
            self._animation.finished.disconnect(self._on_collapsed)
        except Exception:
            pass
        self.setMaximumHeight(self.PANEL_COLLAPSED)
        self.setMinimumHeight(self.PANEL_COLLAPSED)
        self.setFixedHeight(self.PANEL_COLLAPSED)

    def _scroll_to_bottom(self) -> None:
        """Scroll the scroll area to show the latest step."""
        scrollbar = self._scroll_area.verticalScrollBar()
        if scrollbar:
            scrollbar.setValue(scrollbar.maximum())

    def _on_allow(self) -> None:
        """Emit permission_response for allow."""
        tool = self._current_perm_tool
        self._permission_widget.hide()
        self.permission_response.emit(tool, True)

    def _on_deny(self) -> None:
        """Emit permission_response for deny."""
        tool = self._current_perm_tool
        self._permission_widget.hide()
        self.permission_response.emit(tool, False)
