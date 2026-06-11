from .base_button import BaseButton

class SendButton(BaseButton):
    def __init__(self, parent=None):
        super().__init__("\uE724", parent, is_primary=True)
