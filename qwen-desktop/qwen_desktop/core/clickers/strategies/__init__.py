"""Click strategy implementations."""

from qwen_desktop.core.clickers.strategies.template import TemplateClickStrategy
from qwen_desktop.core.clickers.strategies.vision_api import VisionAPIClickStrategy
from qwen_desktop.core.clickers.strategies.local_vision import LocalVisionClickStrategy

__all__ = ["TemplateClickStrategy", "VisionAPIClickStrategy", "LocalVisionClickStrategy"]
