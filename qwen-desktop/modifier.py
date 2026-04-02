import os
from pathlib import Path
import re

path = Path("C:/Users/Hp/OneDrive/Desktop/files/qwen_code_desktop/qwen_desktop/qwen-desktop/qwen_desktop/ui/floating_assistant.py")
code = path.read_text(encoding="utf-8")

# Add imports
if "from qwen_desktop.ui.components.model_selector import ModelSelector" not in code:
    code = code.replace(
        "from qwen_desktop.ui.components.vision_button import VisionButton",
        "from qwen_desktop.ui.components.model_selector import ModelSelector\nfrom qwen_desktop.ui.components.mic_button import MicButton\nfrom qwen_desktop.ui.components.vision_button import VisionButton"
    )

new_setup_ui = """    def _setup_ui(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 4, 0)
        self.main_layout.setSpacing(0)

        self.input_wrapper = QWidget()
        self.input_layout = QHBoxLayout(self.input_wrapper)
        self.input_layout.setContentsMargins(20, 0, 15, 0)
        self.input_layout.setSpacing(6)

        try:
            self.model_selector = ModelSelector(self.settings, self)
            self.model_selector.setStyleSheet(\"\"\"
                QPushButton {
                    background: transparent;
                    color: rgba(255, 255, 255, 0.9);
                    font-size: 14px;
                    font-weight: bold;
                    border: none;
                }
                QPushButton:hover {
                    color: white;
                }
            \"\"\")
            self.input_layout.addWidget(self.model_selector)
        except Exception:
            pass
            
        separ_label = QLabel("|")
        separ_label.setStyleSheet("color: rgba(255, 255, 255, 0.4); font-size: 16px;")
        self.input_layout.addWidget(separ_label)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Message...")
        self.input_field.setStyleSheet(\"\"\"
            QLineEdit {
                background-color: transparent;
                color: rgba(255, 255, 255, 0.9);
                border: none;
                padding-left: 8px;
                font-size: 14px;
            }
            QLineEdit:focus { color: white; }
        \"\"\")
        self.input_field.returnPressed.connect(self.submit_message)
        self.input_layout.addWidget(self.input_field, 1)

        self.mic_btn = MicButton()
        self.input_layout.addWidget(self.mic_btn)

        self.vision_btn = VisionButton()
        self.vision_btn.clicked.connect(self.toggle_vision)
        self.input_layout.addWidget(self.vision_btn)

        self.attach_btn = AttachButton()
        self.attach_btn.clicked.connect(self.select_files)
        self.input_layout.addWidget(self.attach_btn)

        self.send_btn = SendButton()
        self.send_btn.clicked.connect(self.submit_message)
        self._is_sending = False
        self.input_layout.addWidget(self.send_btn)

        self.input_wrapper.setFixedWidth(self.expanded_size - self.collapsed_size)
        self.input_wrapper.hide()

        self.sparkle_wrapper = QWidget()
        self.sparkle_wrapper.setFixedSize(self.collapsed_size, self.collapsed_size)

        self.main_layout.addWidget(self.input_wrapper)
        self.main_layout.addWidget(self.sparkle_wrapper)"""

code = re.sub(
    r"    def _setup_ui\(self\):.*?    def _setup_context_menu\(self\):",
    new_setup_ui + "\n\n    def _setup_context_menu(self):",
    code,
    flags=re.DOTALL
)

# Replace Title
code = re.sub(
    r'title \= QLabel\(\".*?\"\)',
    r'title = QLabel("✨ Welcome to Qwen")',
    code
)

code = re.sub(
    r'title\.setStyleSheet\(\"color: white; font-weight: bold; background: transparent;\"\)',
    r'title.setStyleSheet("color: white; font-weight: bold; background: transparent; font-size: 14px;")',
    code
)

# For AI Message bubbles, add a clear white rounded box with a shadow
ai_style = r"""
            self.frame.setStyleSheet(\"\"\"
                QFrame {
                    background-color: white;
                    color: #1f2937;
                    border: 1px solid #e2e8f0;
                    border-radius: 12px;
                }
            \"\"\")
"""
code = re.sub(
    r"            self\.frame\.setStyleSheet\(\"\"\"\s*QFrame \{\s*background-color: #f3f4f6;\s*color: #1f2937;\s*border-radius: 16px;\s*\}\s*\"\"\"\)",
    ai_style,
    code
)

# User bubble, maybe adapt as well if needed, but it's already purple gradient.

path.write_text(code, encoding="utf-8")
print("Done styling update!")