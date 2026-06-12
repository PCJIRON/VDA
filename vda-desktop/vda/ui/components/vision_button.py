import os
from .base_button import BaseButton


class VisionButton(BaseButton):

    def __init__(self, parent=None):
        svg_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "resources",
                "icons",
                "vision.svg",
            )
        )
        super().__init__(svg_path, parent)
