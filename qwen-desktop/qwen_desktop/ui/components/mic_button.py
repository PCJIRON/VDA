from .base_button import BaseButton

class MicButton(BaseButton):
    """Microphone button with toggle on/off state.
    
    States:
    - Default: microphone icon, translucent background
    - Recording (is_green=True): red background, mic icon
    """
    def __init__(self, parent=None):
        super().__init__("\uE720", parent)
        self.is_recording = False

    def toggle_recording(self):
        """Toggle between recording and idle states."""
        self.is_recording = not self.is_recording
        self.is_green = self.is_recording
        self.update()
