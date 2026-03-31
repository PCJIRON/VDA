from .base_button import BaseButton

class SendButton(BaseButton):
    def __init__(self, parent=None):
        super().__init__("\uE724", parent, is_primary=True)
        self._is_stop_mode = False
    
    def set_stop_mode(self, is_stop: bool):
        """Toggle between send (arrow) and stop (square) icons."""
        self._is_stop_mode = is_stop
        self.is_stop = is_stop  # Use BaseButton's stop styling
        
        if is_stop:
            # Stop icon: Unicode BLACK SQUARE (■)
            self.fluent_icon = "\u25A0"
        else:
            # Send icon: Unicode arrow (➤) or Fluent icon
            self.fluent_icon = "\uE724"
        
        self.update()  # Trigger repaint
