from PyQt6.QtCore import pyqtSignal
from .base_button import BaseButton

class MicButton(BaseButton):
    """Microphone button for voice input."""
    
    def __init__(self, parent=None):
        super().__init__("\uE720", parent)  # Microphone icon (\uE720 in Fluent Icons)
        self._is_recording = False
    
    def set_recording_state(self, is_recording: bool):
        """Toggle between mic (listening) and stop recording states."""
        self._is_recording = is_recording
        
        if is_recording:
            # Light up red for recording
            self.is_stop = True
            self.fluent_icon = "\uE720"  # Keep mic icon (or switch to animated stop)
        else:
            # Normal state
            self.is_stop = False
            self.fluent_icon = "\uE720"
        
        self.update()