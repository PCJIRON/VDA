import re
import pathlib
path = 'qwen_desktop/ui/floating_assistant.py'
code = pathlib.Path(path).read_text('utf-8')
replacement = '''    def trigger_login(self):
        try:
            from qwen_desktop.auth.qwen_auth_gui import QwenAuthDialog
            from PyQt6.QtCore import Qt
            self.auth_dialog = QwenAuthDialog(self)
            self.auth_dialog.auth_success.connect(self._on_login_success)
            self.auth_dialog.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
            self.auth_dialog.show()
            self.auth_dialog.hide()
            self.auth_dialog._on_login_clicked()
        except Exception as e:
            print(f"Login trigger failed: {e}")'''
code = re.sub(r'    def trigger_login\(self\):.*?print\(f"Login trigger failed: \{e\}"\)', replacement, code, 1, re.DOTALL)
pathlib.Path(path).write_text(code, 'utf-8')
print('Done replacing trigger_login')
