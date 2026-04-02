import pathlib

path = pathlib.Path('qwen_desktop/ui/floating_assistant.py')
code = path.read_text('utf-8')

if "def show_settings_dialog" not in code:
    code = code.replace(
        "    def toggle_auth(self):",
        "    def show_settings_dialog(self):\n        print('Settings dialogue called')\n        pass\n\n    def toggle_auth(self):"
    )
    path.write_text(code, 'utf-8')
    print("Method added.")
else:
    print("Method already exists.")
