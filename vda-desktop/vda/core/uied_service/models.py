"""Data models for UIED service.

Only the ``UIComponent`` dataclass is needed by the rest of the service.
"""

import logging
from dataclasses import asdict, dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class UIComponent:
    """Represents a detected UI component.

    Attributes:
        id: Unique identifier (string).
        label: Human‑readable label (e.g., "Search button").
        component_type: Type such as "button", "input", "icon", etc.
        x, y, width, height: Bounding box coordinates in screen space.
        confidence: Detection confidence (0.0‑1.0).
        template_path: Optional path to a saved template image.
        center_x, center_y: Cached centre coordinates for clicking.
    """

    id: str
    label: str
    component_type: str
    x: int
    y: int
    width: int
    height: int
    confidence: float
    template_path: Optional[str] = None
    center_x: Optional[int] = None
    center_y: Optional[int] = None

    def __post_init__(self) -> None:
        if self.center_x is None:
            self.center_x = self.x + self.width // 2
        if self.center_y is None:
            self.center_y = self.y + self.height // 2

    def to_dict(self) -> dict:
        return asdict(self)
