import pathlib
import sys

def apply_fixes():
    # 1. Fix ModelSelector text truncation
    ms_path = pathlib.Path('qwen_desktop/ui/components/model_selector.py')
    ms_code = ms_path.read_text('utf-8')
    ms_target = '    def _update_text(self):\n        # We show the model name and a tiny chevron down unicode\n        self.setText(f"{self.current_model} \\uE70D")'
    ms_repl = '    def _update_text(self):\n        # We show the model name and a tiny chevron down unicode\n        display_name = self.current_model\n        if len(display_name) > 10:\n            display_name = display_name[:10] + ".."\n        self.setText(f"{display_name} \\uE70D")'
    if ms_target in ms_code:
        ms_code = ms_code.replace(ms_target, ms_repl)
        ms_path.write_text(ms_code, 'utf-8')
        print("ModelSelector updated.")

    # 2. Fix FloatingAssistant Mic issues
    fa_path = pathlib.Path('qwen_desktop/ui/floating_assistant.py')
    fa_code = fa_path.read_text('utf-8')

    # Continuous recording (don't stop on transcribed)
    fa_code = fa_code.replace("""    def _on_voice_transcribed(self, text):
        current_text = self.input_field.text()
        space = " " if current_text else ""
        self.input_field.setText(f"{current_text}{space}{text}".strip())
        self._stop_voice()""", """    def _on_voice_transcribed(self, text):
        current_text = self.input_field.text()
        space = " " if current_text else ""
        self.input_field.setText(f"{current_text}{space}{text}".strip())""")

    # Make Sure Mic Button gets the correct styling that makes it a red circle
    fa_code = fa_code.replace("""self.mic_btn.setStyleSheet("QToolButton { background-color: #ef4444; border-radius: 18px; border: none; color: white; }")""", """self.mic_btn.setStyleSheet("QToolButton { background-color: #ef4444; border-radius: 18px; border: none; color: white; padding: 0px; margin: 0px; }")""")

    # Ensure MicButton uses set_recording_state to display properly if internal painter overrides it
    if "self.mic_btn.set_recording_state(True)" not in fa_code:
        fa_code = fa_code.replace("""self.is_voice_recording = True""", """self.is_voice_recording = True\n                    if hasattr(self.mic_btn, 'set_recording_state'): self.mic_btn.set_recording_state(True)""")
    if "self.mic_btn.set_recording_state(False)" not in fa_code:
        fa_code = fa_code.replace("""self.is_voice_recording = False""", """self.is_voice_recording = False\n        if hasattr(self.mic_btn, 'set_recording_state'): self.mic_btn.set_recording_state(False)""")

    fa_path.write_text(fa_code, 'utf-8')
    print("FloatingAssistant updated.")

if __name__ == '__main__':
    apply_fixes()
