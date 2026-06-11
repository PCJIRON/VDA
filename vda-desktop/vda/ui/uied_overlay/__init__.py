"""UIED overlay package.

Provides the original public symbols ``UIEDOverlayWidget``, ``DraggableToolbar``
and ``LabelEditorDialog`` so existing imports (e.g. ``from vda.ui.uied_overlay
import UIEDOverlayWidget``) continue to work.
"""

from .overlay import UIEDOverlayWidget
from .toolbar import DraggableToolbar
from .label_editor import LabelEditorDialog

__all__ = ["UIEDOverlayWidget", "DraggableToolbar", "LabelEditorDialog"]
