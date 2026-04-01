import pathlib
import sys
import re

def apply_fix():
    path = pathlib.Path('qwen_desktop/ui/floating_assistant.py')
    code = path.read_text('utf-8')

    # 1. Expand width
    code = code.replace("self.expanded_size = 450", "self.expanded_size = 750")

    # 2. Add imports
    if "from qwen_desktop.core.voice_service import VoiceService" not in code:
        code = code.replace("from qwen_desktop.core.pyautogui_executor import PyAutoGUIExecutor", 
                            "from qwen_desktop.core.pyautogui_executor import PyAutoGUIExecutor\nfrom qwen_desktop.core.voice_service import VoiceService")

    # 3. Add VoiceService initialization
    if "self.voice_service = VoiceService()" not in code:
        code = code.replace("self.session_id = str(uuid.uuid4())",
                            "self.voice_service = VoiceService()\n        self.is_voice_recording = False\n        self.session_id = str(uuid.uuid4())")

    # 4. Model selector font size
    code = code.replace("font-size: 14px", "font-size: 11px")

    # 5. Fix mic button in _setup_ui
    old_mic = """        self.mic_btn = MicButton()
        try:
            self.mic_btn.setStyleSheet("QToolButton { background: transparent; border: none; }")
        except: pass
        self.text_layout.addWidget(self.mic_btn)"""

    new_mic = """        self.mic_btn = MicButton()
        self.mic_btn.setFixedSize(36, 36)
        self.mic_btn.clicked.connect(self.toggle_voice)
        try:
            self.mic_btn.setStyleSheet("QToolButton { background: transparent; border: none; } QToolButton:hover { background-color: rgba(255, 255, 255, 0.1); border-radius: 18px; }")
        except: pass
        self.text_layout.addWidget(self.mic_btn)"""
    
    if old_mic in code:
        code = code.replace(old_mic, new_mic)

    # 6. Add toggle_voice and handlers
    voice_methods = """    def toggle_voice(self):
        if not self.is_voice_recording:
            try:
                success = self.voice_service.start_recording()
                if success:
                    self.is_voice_recording = True
                    self.mic_btn.setStyleSheet("QToolButton { background-color: #ef4444; border-radius: 18px; border: none; color: white; }")
                    recorder = self.voice_service.get_recorder()
                    if recorder:
                        try: recorder.transcription_ready.disconnect()
                        except: pass
                        try: recorder.error_occurred.disconnect()
                        except: pass
                        recorder.transcription_ready.connect(self._on_voice_transcribed)
                        recorder.error_occurred.connect(self._on_voice_error)
                else:
                    self.history_popup.add_message("Could not access microphone.", "ai")
            except Exception as e:
                logger.error(f"Voice err: {e}")
        else:
            self._stop_voice()

    def _stop_voice(self):
        self.is_voice_recording = False
        self.voice_service.stop_recording()
        self.mic_btn.setStyleSheet("QToolButton { background: transparent; border: none; } QToolButton:hover { background-color: rgba(255, 255, 255, 0.1); border-radius: 18px; }")

    def _on_voice_transcribed(self, text):
        current_text = self.input_field.text()
        space = " " if current_text else ""
        self.input_field.setText(f"{current_text}{space}{text}".strip())
        self._stop_voice()

    def _on_voice_error(self, err):
        self._stop_voice()
        self.history_popup.add_message(f"Voice Error: {err}", "ai")

"""
    if "def toggle_voice" not in code:
        code = code.replace("    def toggle_vision(self):", voice_methods + "    def toggle_vision(self):")

    path.write_text(code, 'utf-8')
    print("Fixes applied successfully.")

if __name__ == '__main__':
    apply_fix()
