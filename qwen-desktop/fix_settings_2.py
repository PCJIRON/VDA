import pathlib

path = pathlib.Path('qwen_desktop/ui/floating_assistant.py')
code = path.read_text('utf-8')

old_method = """    def show_settings_dialog(self):
        print('Settings dialogue called')
        pass"""

new_method = """    def show_settings_dialog(self):
        try:
            from qwen_desktop.ui.settings_dialog import SettingsDialog
            if not hasattr(self, 'settings_dialog'):
                self.settings_dialog = SettingsDialog(self)
                if hasattr(self, 'oauth') and self.oauth:
                    self.settings_dialog.login_btn.clicked.connect(self.trigger_login)
                    self.settings_dialog.logout_btn.clicked.connect(self.oauth.logout)
            self.settings_dialog.show()
            self.settings_dialog.raise_()
            self.settings_dialog.activateWindow()
        except Exception as e:
            print(f"Error opening settings dialog: {e}")"""

if old_method in code:
    code = code.replace(old_method, new_method)
    path.write_text(code, 'utf-8')
    print("Method updated.")
else:
    print("Old method not found.")
