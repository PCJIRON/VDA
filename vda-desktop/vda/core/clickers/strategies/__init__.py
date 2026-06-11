"""Click strategy implementations."""

from vda.core.clickers.strategies.template import TemplateClickStrategy
from vda.core.clickers.strategies.vision_api import VisionAPIClickStrategy
from vda.core.clickers.strategies.local_vision import LocalVisionClickStrategy

__all__ = ["TemplateClickStrategy", "VisionAPIClickStrategy", "LocalVisionClickStrategy"]
