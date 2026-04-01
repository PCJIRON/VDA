import pathlib
import sys

def apply_fix():
    path = pathlib.Path('qwen_desktop/ui/floating_assistant.py')
    code = path.read_text('utf-8')
    import re
    
    new_setup_ui = """    def _setup_ui(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 4, 0)
        self.main_layout.setSpacing(0)

        self.input_wrapper = QWidget()
        self.input_layout = QHBoxLayout(self.input_wrapper)
        self.input_layout.setContentsMargins(10, 8, 10, 8)
        self.input_layout.setSpacing(8)

        # 1. SETTINGS BUTTON BLOCK
        self.settings_btn = SettingsButton()
        self.settings_btn.clicked.connect(self.show_settings_dialog)
        self.settings_btn.setFixedSize(40, 40)
        try:
            self.settings_btn.setStyleSheet("QToolButton { background-color: rgba(255, 255, 255, 0.15); border-radius: 12px; } QToolButton:hover { background-color: rgba(255, 255, 255, 0.25); }")
        except: pass
        self.input_layout.addWidget(self.settings_btn)

        # 2. TEXT CONTAINER PILL (Model, Separator, Input, Mic)
        self.text_container = QWidget()
        self.text_container.setObjectName("TextContainer")
        self.text_container.setStyleSheet("QWidget#TextContainer { background-color: rgba(255, 255, 255, 0.12); border-radius: 14px; }")
        self.text_layout = QHBoxLayout(self.text_container)
        self.text_layout.setContentsMargins(12, 0, 8, 0)
        self.text_layout.setSpacing(6)
        self.text_container.setFixedHeight(40)

        try:
            self.model_selector = ModelSelector(self.settings, self)
            self.model_selector.setStyleSheet("QPushButton { background: transparent; color: rgba(255, 255, 255, 0.9); font-size: 14px; font-weight: bold; border: none; } QPushButton:hover { color: white; }")
            self.text_layout.addWidget(self.model_selector)
        except Exception:
            pass

        separ_label = QLabel("|")
        separ_label.setStyleSheet("color: rgba(255, 255, 255, 0.3); font-size: 16px; background: transparent;")
        self.text_layout.addWidget(separ_label)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Message...")
        self.input_field.setStyleSheet("QLineEdit { background-color: transparent; color: rgba(255, 255, 255, 0.9); border: none; font-size: 14px; } QLineEdit:focus { color: white; }")
        self.input_field.returnPressed.connect(self.submit_message)
        self.text_layout.addWidget(self.input_field, 1)

        self.mic_btn = MicButton()
        try:
            self.mic_btn.setStyleSheet("QToolButton { background: transparent; border: none; }")
        except: pass
        self.text_layout.addWidget(self.mic_btn)

        self.input_layout.addWidget(self.text_container, 1)

        # BUTTON STYLESHEET HELPER
        btn_style = "QToolButton { background-color: rgba(255, 255, 255, 0.15); border-radius: 12px; } QToolButton:hover { background-color: rgba(255, 255, 255, 0.25); }"

        # 3. VISION BUTTON BLOCK (EYE SLASH)
        self.vision_btn = VisionButton()
        self.vision_btn.clicked.connect(self.toggle_vision)
        self.vision_btn.setFixedSize(40, 40)
        try: self.vision_btn.setStyleSheet(btn_style)
        except: pass
        self.input_layout.addWidget(self.vision_btn)

        # 4. ATTACH BUTTON BLOCK (PAPERCLIP)
        self.attach_btn = AttachButton()
        self.attach_btn.clicked.connect(self.select_files)
        self.attach_btn.setFixedSize(40, 40)
        try: self.attach_btn.setStyleSheet(btn_style)
        except: pass
        self.input_layout.addWidget(self.attach_btn)

        # 5. SEND BUTTON BLOCK (PAPER PLANE)
        self.send_btn = SendButton()
        self.send_btn.clicked.connect(self.submit_message)
        self.send_btn.setFixedSize(40, 40)
        self._is_sending = False
        try: self.send_btn.setStyleSheet(btn_style)
        except: pass
        self.input_layout.addWidget(self.send_btn)

        # EXTRA: UIED BUTTON BLOCK (If needed by user)
        self.uied_btn = UIEDButton()
        self.uied_btn.clicked.connect(self.trigger_uied_detection)
        self.uied_btn.setFixedSize(40, 40)
        try: self.uied_btn.setStyleSheet(btn_style)
        except: pass
        self.input_layout.addWidget(self.uied_btn)

        self.input_wrapper.setFixedWidth(self.expanded_size - self.collapsed_size)
        self.input_wrapper.hide()

        self.sparkle_wrapper = QWidget()
        self.sparkle_wrapper.setFixedSize(self.collapsed_size, self.collapsed_size)

        self.main_layout.addWidget(self.input_wrapper)
        self.main_layout.addWidget(self.sparkle_wrapper)"""

    m = re.search(r'    def _setup_ui\(self\):.*?    def _setup_context_menu\(self\):', code, re.DOTALL)
    if m:
        code = code.replace(m.group(0), new_setup_ui + "\n\n    def _setup_context_menu(self):")
        path.write_text(code, 'utf-8')
        print("Success")
    else:
        print("Could not match.")

if __name__ == '__main__':
    apply_fix()
