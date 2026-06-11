from .base_button import BaseButton

class SettingsButton(BaseButton):
    def __init__(self, parent=None):
        super().__init__("\uE713", parent)
