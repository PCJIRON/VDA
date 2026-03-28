"""
Settings dialog for application preferences.

Enhanced with theme selection and qwen-dark styling.
"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QCheckBox,
    QSpinBox,
    QTabWidget,
    QWidget,
    QGroupBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from qwen_desktop.config.settings import Settings
from qwen_desktop.ui.theme_manager import ThemeManager


class SettingsDialog(QDialog):
    """Settings dialog for application preferences."""

    def __init__(self, settings: Settings, parent=None) -> None:
        """Initialize the settings dialog.

        Args:
            settings: Application settings.
            parent: Parent widget.
        """
        super().__init__(parent)

        self.settings = settings

        self._setup_ui()
        self._apply_styles()
        self._load_settings()

    def _setup_ui(self) -> None:
        """Set up the UI components."""
        self.setWindowTitle("Settings")
        self.setMinimumWidth(520)
        self.setMinimumHeight(450)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # General tab
        self.tabs.addTab(self._create_general_tab(), "General")

        # API tab
        self.tabs.addTab(self._create_api_tab(), "API")

        # Appearance tab
        self.tabs.addTab(self._create_appearance_tab(), "Appearance")

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)

    def _create_general_tab(self) -> QWidget:
        """Create the general settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        # Auto-save
        self.auto_save_checkbox = QCheckBox("Auto-save conversations")
        self.auto_save_checkbox.setToolTip("Automatically save conversation history")
        layout.addWidget(self.auto_save_checkbox)

        # Check for updates
        self.updates_checkbox = QCheckBox("Check for updates on startup")
        layout.addWidget(self.updates_checkbox)

        # Analytics
        self.analytics_checkbox = QCheckBox("Send anonymous analytics")
        layout.addWidget(self.analytics_checkbox)

        layout.addStretch()

        return widget

    def _create_api_tab(self) -> QWidget:
        """Create the API settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        # API Base URL
        self.api_base_url_input = QLineEdit()
        self.api_base_url_input.setPlaceholderText(
            "https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        form_layout.addRow("API Base URL:", self.api_base_url_input)

        # Model selection
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "qwen-coder-plus",
            "qwen-plus",
            "qwen-max",
            "qwen-turbo",
        ])
        form_layout.addRow("Default Model:", self.model_combo)

        # Timeout
        self.timeout_spinbox = QSpinBox()
        self.timeout_spinbox.setRange(10, 300)
        self.timeout_spinbox.setSuffix(" seconds")
        form_layout.addRow("Request Timeout:", self.timeout_spinbox)

        layout.addLayout(form_layout)
        layout.addStretch()

        return widget

    def _create_appearance_tab(self) -> QWidget:
        """Create the appearance settings tab."""
        tm = ThemeManager.instance()

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        # Theme selection with display names
        self.theme_combo = QComboBox()
        theme_names = tm.get_theme_display_names()
        for theme_id, display_name in theme_names.items():
            self.theme_combo.addItem(display_name, theme_id)
        form_layout.addRow("Theme:", self.theme_combo)

        # Font size
        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setRange(10, 24)
        self.font_size_spinbox.setSuffix(" px")
        form_layout.addRow("Font Size:", self.font_size_spinbox)

        layout.addLayout(form_layout)

        # Theme preview
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout(preview_group)

        self.preview_label = QLabel("Theme preview will appear here")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumHeight(60)
        preview_layout.addWidget(self.preview_label)

        layout.addWidget(preview_group)

        # Connect theme change for live preview
        self.theme_combo.currentIndexChanged.connect(self._on_theme_preview)

        layout.addStretch()

        return widget

    def _on_theme_preview(self, index: int) -> None:
        """Handle theme preview update.

        Args:
            index: Selected theme index.
        """
        theme_id = self.theme_combo.currentData()
        if theme_id:
            from qwen_desktop.ui.theme_manager import THEMES

            theme = THEMES.get(theme_id)
            if theme:
                c = theme.colors
                self.preview_label.setStyleSheet(f"""
                    background-color: {c.Background};
                    color: {c.Foreground};
                    border: 1px solid {c.Gray};
                    border-radius: 6px;
                    padding: 12px;
                    font-size: 12px;
                """)
                self.preview_label.setText(
                    f"Background: {c.Background}\n"
                    f"Text: {c.Foreground}\n"
                    f"Accent: {c.AccentYellow}"
                )

    def _apply_styles(self) -> None:
        """Apply styles to the dialog."""
        tm = ThemeManager.instance()
        c = tm.colors
        s = tm.semantic

        self.setStyleSheet(f"""
            SettingsDialog {{
                background-color: {s.background.primary};
                color: {s.text.primary};
            }}
            QTabWidget::pane {{
                border: 1px solid {s.border.default};
                border-radius: 6px;
                background-color: {s.background.primary};
            }}
            QTabBar::tab {{
                background-color: {s.background.secondary};
                color: {s.text.secondary};
                padding: 8px 16px;
                border: 1px solid {s.border.default};
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background-color: {s.background.primary};
                color: {s.text.primary};
            }}
            QTabBar::tab:hover {{
                background-color: {s.background.hover};
            }}
            QGroupBox {{
                border: 1px solid {s.border.default};
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 12px;
                color: {s.text.primary};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }}
            QLineEdit, QComboBox, QSpinBox {{
                background-color: {s.background.input};
                border: 1px solid {s.border.default};
                border-radius: 6px;
                padding: 6px 10px;
                color: {s.text.primary};
            }}
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
                border: 1px solid {s.border.focus};
            }}
            QCheckBox {{
                spacing: 8px;
                color: {s.text.primary};
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 1px solid {s.border.default};
                background-color: {s.background.input};
            }}
            QCheckBox::indicator:checked {{
                background-color: {c.AccentBlue};
                border-color: {c.AccentBlue};
            }}
            QPushButton {{
                background-color: {c.AccentBlue};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {c.LightBlue};
            }}
            QPushButton#cancelBtn {{
                background-color: {s.background.elevated};
                color: {s.text.primary};
                border: 1px solid {s.border.default};
            }}
            QPushButton#cancelBtn:hover {{
                background-color: {s.background.hover};
            }}
            QLabel {{
                color: {s.text.primary};
            }}
        """)

    def _load_settings(self) -> None:
        """Load settings into UI controls."""
        # General
        self.auto_save_checkbox.setChecked(
            self.settings.get("auto_save_conversations", True)
        )
        self.updates_checkbox.setChecked(
            self.settings.get("check_for_updates", True)
        )
        self.analytics_checkbox.setChecked(
            self.settings.get("send_analytics", False)
        )

        # API
        self.api_base_url_input.setText(
            self.settings.get(
                "api_base_url",
                "https://dashscope.aliyuncs.com/compatible-mode/v1",
            )
        )

        model = self.settings.get("api_model", "qwen-coder-plus")
        idx = self.model_combo.findText(model)
        if idx >= 0:
            self.model_combo.setCurrentIndex(idx)

        self.timeout_spinbox.setValue(self.settings.get("api_timeout", 60))

        # Appearance
        theme = self.settings.get("theme", "qwen-dark")
        for i in range(self.theme_combo.count()):
            if self.theme_combo.itemData(i) == theme:
                self.theme_combo.setCurrentIndex(i)
                break

        self.font_size_spinbox.setValue(self.settings.get("font_size", 12))

    def _save_settings(self) -> None:
        """Save settings from UI controls."""
        # General
        self.settings.set(
            "auto_save_conversations", self.auto_save_checkbox.isChecked()
        )
        self.settings.set(
            "check_for_updates", self.updates_checkbox.isChecked()
        )
        self.settings.set(
            "send_analytics", self.analytics_checkbox.isChecked()
        )

        # API
        self.settings.set("api_base_url", self.api_base_url_input.text())
        self.settings.set("api_model", self.model_combo.currentText())
        self.settings.set("api_timeout", self.timeout_spinbox.value())

        # Appearance
        theme_id = self.theme_combo.currentData()
        if theme_id:
            self.settings.set("theme", theme_id)

        self.settings.set("font_size", self.font_size_spinbox.value())

    def accept(self) -> None:
        """Handle dialog acceptance."""
        self._save_settings()
        super().accept()
