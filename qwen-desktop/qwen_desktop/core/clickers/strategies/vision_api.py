"""VLM-based click strategy — executes click at coordinates provided by VLM detection.

The VLM coordinate detection runs at a higher layer (vision_handler mixin).
This strategy simply executes the click and optionally verifies the result.
"""

import logging

import pyautogui

from qwen_desktop.core.clickers.engine import ClickStrategy, ClickResult

logger = logging.getLogger(__name__)


class VisionAPIClickStrategy(ClickStrategy):
    @property
    def name(self) -> str:
        return "vision_api"

    def click(self, x: int, y: int, **kwargs) -> ClickResult:
        logger.debug(f"VisionAPIClickStrategy: clicking ({x}, {y})")
        try:
            pyautogui.click(x, y)
            return ClickResult(True, x, y, self.name, 1.0)
        except Exception as e:
            logger.warning(f"VisionAPIClickStrategy failed at ({x}, {y}): {e}")
            return ClickResult(False, x, y, self.name, 0.0)
