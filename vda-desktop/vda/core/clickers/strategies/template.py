"""OpenCV template matching click strategy."""

import logging
import os
from typing import Optional

import cv2
import numpy as np
import pyautogui

from vda.core.clickers.engine import ClickStrategy, ClickResult

logger = logging.getLogger(__name__)


class TemplateClickStrategy(ClickStrategy):
    @property
    def name(self) -> str:
        return "template"

    def click(self, x: int, y: int, **kwargs) -> ClickResult:
        template_path = kwargs.get("template_path")
        threshold = kwargs.get("threshold", 0.7)
        target_name = kwargs.get("target_name")

        if template_path and os.path.exists(template_path):
            try:
                template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
                if template is None:
                    return ClickResult(False, x, y, self.name, 0.0)
                screenshot = pyautogui.screenshot()
                screen_np = np.array(screenshot)
                screen_gray = cv2.cvtColor(screen_np, cv2.COLOR_RGB2GRAY)
                result = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(result)
                if max_val >= threshold:
                    h, w = template.shape
                    cx = max_loc[0] + w // 2
                    cy = max_loc[1] + h // 2
                    pyautogui.click(cx, cy)
                    logger.info(f"Template click at ({cx}, {cy}) confidence {max_val:.3f}")
                    return ClickResult(True, cx, cy, self.name, float(max_val))
                logger.debug(f"Template match below threshold: {max_val:.3f}")
            except Exception as e:
                logger.warning(f"Template matching failed: {e}")
        if target_name:
            logger.info(f"No template for '{target_name}', falling through")
        return ClickResult(False, x, y, self.name, 0.0)
