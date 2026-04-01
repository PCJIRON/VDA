from PyQt6.QtWidgets import QPushButton, QMenu
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt
import logging

logger = logging.getLogger(__name__)

AVAILABLE_MODELS = [
    "qwen-coder-plus",          
    "qwen3-coder-plus",
    "qwen2.5-coder-32b-instruct",
    "qwen-plus"
]

class ModelSelector(QPushButton):
    """Dropdown arrow for selecting the Qwen model. Placed inside the input bar visually."""
    
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Select Model")
        
        # Load saved model or default
        saved_model = self.settings.get("api_model", "qwen-coder-plus")
        if saved_model not in AVAILABLE_MODELS:
            saved_model = "qwen-coder-plus"
            
        self.current_model = saved_model
        
        # Build menu
        self._menu = QMenu(self)
        self._menu.setStyleSheet("""
            QMenu {
                background-color: #1f2937;
                color: white;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px 6px 20px;
                border-radius: 4px;
                font-family: 'Segoe UI';
                font-size: 12px;
            }
            QMenu::item:selected {
                background-color: #4f46e5;
            }
        """)
        
        for m in AVAILABLE_MODELS:
            act = QAction(m, self)
            act.triggered.connect(lambda checked, model=m: self._on_model_changed(model))
            self._menu.addAction(act)
            
        self.setMenu(self._menu)
        
        # Style as a clean label + arrow inside the chat input
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #a78bfa;
                border: none;
                padding: 0px 8px;
                font-size: 11px;
                font-family: 'Segoe UI', 'Segoe Fluent Icons';
                font-weight: bold;
            }
            QPushButton:hover {
                color: #c4b5fd;
            }
            QPushButton::menu-indicator {
                image: none;
            }
        """)
        
        self._update_text()
        
    def _update_text(self):
        # We show the model name and a tiny chevron down unicode
        display_name = self.current_model
        if len(display_name) > 10:
            display_name = display_name[:10] + ".."
        self.setText(f"{display_name} \uE70D")
        self.setToolTip(f"Current Model: {self.current_model}")

    def _on_model_changed(self, new_model):
        self.current_model = new_model
        self.settings.set("api_model", new_model)
        self._update_text()
        logger.info(f"Model changed to {new_model}")
        
        if hasattr(self.settings, 'save'):
            self.settings.save()
