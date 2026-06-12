import os
from .base_button import BaseButton


class VoiceButton(BaseButton):

    def __init__(self, parent=None):
        svg_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "resources",
                "icons",
                "mic.svg",
            )
        )
        super().__init__(svg_path, parent)
