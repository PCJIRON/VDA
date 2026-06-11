"""Label editor dialog for UI‑ED overlay.

Provides a small popup where the user can edit a component's label and select its
type (icon, button, etc.). The dialog emits ``label_saved`` with the new label
and type when the user clicks Save or presses Enter.
"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFrame,
    QLabel,
    QLineEdit,
    QComboBox,
    QHBoxLayout,
    QPushButton,
)
from PyQt6.QtCore import Qt, pyqtSignal


class LabelEditorDialog(QDialog):
    """Popup dialog for editing component labels."""

    label_saved = pyqtSignal(str, str)

    def __init__(self, parent=None, current_label: str = "", current_type: str = "icon"):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(350, 200)
        self._setup_ui(current_label, current_type)

    def _setup_ui(self, current_label: str, current_type: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        container = QFrame()
        container.setStyleSheet(
            """
            QFrame {
                background-color: #1f2937;
                border-radius: 12px;
                border: 2px solid #6366f1;
            }
            """
        )
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(16, 16, 16, 16)
        container_layout.setSpacing(12)

        title = QLabel("✏️ Edit Component Label")
        title.setStyleSheet(
            "color: white; font-weight: bold; font-size: 14px; background: transparent;"
        )
        container_layout.addWidget(title)

        self.label_input = QLineEdit(current_label)
        self.label_input.setPlaceholderText("Enter detailed label...")
        self.label_input.setStyleSheet(
            """
            QLineEdit {
                background-color: #374151;
                color: white;
                border: 1px solid #4b5563;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus { border: 1px solid #6366f1; }
            """
        )
        container_layout.addWidget(self.label_input)

        type_row = QHBoxLayout()
        type_label = QLabel("Type:")
        type_label.setStyleSheet("color: #9ca3af; background: transparent;")
        type_row.addWidget(type_label)

        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "app_icon",
            "symbol_icon",
            "button",
            "text_label",
            "input_field",
            "container_panel",
            "menu_item",
            "tab",
            "checkbox_toggle",
            "scrollbar",
            "decorative",
            "other",
        ])
        self.type_combo.setCurrentText(current_type)
        self.type_combo.setStyleSheet(
            """
            QComboBox {
                background-color: #374151;
                color: white;
                border: 1px solid #4b5563;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
            }
            """
        )
        type_row.addWidget(self.type_combo, 1)
        container_layout.addLayout(type_row)

        button_row = QHBoxLayout()
        button_row.setSpacing(8)

        self.save_btn = QPushButton("💾 Save")
        self.save_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #6366f1;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #4f46e5; }
            """
        )
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.cancel_btn = QPushButton("✕ Cancel")
        self.cancel_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #374151;
                color: #9ca3af;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #4b5563;
                color: white;
            }
            """
        )
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        button_row.addWidget(self.save_btn)
        button_row.addWidget(self.cancel_btn)
        button_row.addStretch()
        container_layout.addLayout(button_row)

        layout.addWidget(container)

        # Connect signals
        self.save_btn.clicked.connect(self._on_save)
        self.cancel_btn.clicked.connect(self.reject)
        self.label_input.returnPressed.connect(self._on_save)

    def _on_save(self):
        new_label = self.label_input.text().strip()
        new_type = self.type_combo.currentText()
        if new_label:
            self.accept()  # Close dialog first
            self.label_saved.emit(new_label, new_type)
