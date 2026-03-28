"""
Model selection dialog.

Matches qwen-code's /model command flow.
Allows users to switch between Qwen models dynamically.
"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QFrame,
    QPushButton,
    QButtonGroup,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from qwen_desktop.config.settings import Settings
from qwen_desktop.ui.theme_manager import ThemeManager


class ModelDialog(QDialog):
    """Dialog for selecting active model."""

    def __init__(self, settings: Settings, parent=None):
        """Initialize model dialog.

        Args:
            settings: App settings.
            parent: Parent widget.
        """
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Select Model")
        self.setMinimumWidth(350)
        
        self.models = [
            {"id": "qwen-coder-plus", "name": "Qwen Coder Plus", "desc": "Best for coding and complex logic"},
            {"id": "qwen-plus", "name": "Qwen Plus", "desc": "Balanced performance and speed"},
            {"id": "qwen-max", "name": "Qwen Max", "desc": "Highest capability, slower speed"},
            {"id": "qwen-turbo", "name": "Qwen Turbo", "desc": "Fastest response, basic tasks"},
        ]
        
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

        header = QLabel("🧠 Select AI Model")
        header.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        header.setStyleSheet(f"color: {s.text.primary};")
        layout.addWidget(header)

        self.btn_group = QButtonGroup(self)
        current_model = self.settings.get("api_model", "qwen-coder-plus")

        # Create model radio buttons
        for i, model in enumerate(self.models):
            frame = QFrame()
            frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {s.background.elevated};
                    border: 1px solid {s.border.default};
                    border-radius: 8px;
                }}
                QFrame:hover {{
                    border: 1px solid {c.AccentBlue};
                }}
            """)
            
            f_layout = QVBoxLayout(frame)
            f_layout.setContentsMargins(12, 12, 12, 12)
            f_layout.setSpacing(4)
            
            radio = QRadioButton(model["name"])
            radio.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            radio.setStyleSheet(f"""
                QRadioButton {{ color: {s.text.primary}; font-weight: bold; }}
                QRadioButton::indicator {{
                    width: 16px;
                    height: 16px;
                    border-radius: 8px;
                    border: 1px solid {c.Gray};
                }}
                QRadioButton::indicator:checked {{
                    background-color: {c.AccentBlue};
                    border: 4px solid {s.background.primary};
                    outline: 1px solid {c.AccentBlue};
                }}
            """)
            
            self.btn_group.addButton(radio, i)
            if model["id"] == current_model:
                radio.setChecked(True)
                
            f_layout.addWidget(radio)
            
            desc = QLabel(model["desc"])
            desc.setFont(QFont("Segoe UI", 9))
            desc.setStyleSheet(f"color: {c.Comment}; margin-left: 24px;")
            f_layout.addWidget(desc)
            
            layout.addWidget(frame)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {s.background.elevated};
                color: {s.text.primary};
                border: 1px solid {s.border.default};
                border-radius: 4px;
                padding: 6px 16px;
            }}
            QPushButton:hover {{ background-color: {s.background.hover}; }}
        """)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c.AccentBlue};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {c.LightBlue}; }}
        """)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)

    def _apply_styles(self):
        """Apply base dialog styles."""
        tm = ThemeManager.instance()
        s = tm.semantic
        
        self.setStyleSheet(f"""
            ModelDialog {{
                background-color: {s.background.primary};
            }}
        """)

    def get_selected_model(self) -> str:
        """Get the ID of the selected model."""
        idx = self.btn_group.checkedId()
        if idx >= 0:
            return self.models[idx]["id"]
        return "qwen-coder-plus"
