"""Click strategy implementations."""

from vda.core.clickers.strategies.local_vision import LocalVisionClickStrategy
from vda.core.clickers.strategies.template import TemplateClickStrategy
from vda.core.clickers.strategies.vision_api import VisionAPIClickStrategy

__all__ = ["TemplateClickStrategy", "VisionAPIClickStrategy", "LocalVisionClickStrategy"]
