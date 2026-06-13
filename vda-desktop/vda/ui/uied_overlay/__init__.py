"""UIED overlay package.

Provides the original public symbols ``UIEDOverlayWidget``, ``DraggableToolbar``
and ``LabelEditorDialog`` so existing imports (e.g. ``from vda.ui.uied_overlay
import UIEDOverlayWidget``) continue to work.
"""

from .label_editor import LabelEditorDialog
from .overlay import UIEDOverlayWidget
from .toolbar import DraggableToolbar

__all__ = ["UIEDOverlayWidget", "DraggableToolbar", "LabelEditorDialog"]
