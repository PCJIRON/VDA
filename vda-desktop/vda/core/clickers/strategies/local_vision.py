"""Local vision click strategy — OpenCV contour detection for UI element centering."""

import logging

import cv2
import numpy as np
import pyautogui

from vda.core.clickers.engine import ClickStrategy, ClickResult

logger = logging.getLogger(__name__)


class LocalVisionClickStrategy(ClickStrategy):
    @property
    def name(self) -> str:
        return "local_vision"

    def click(self, x: int, y: int, **kwargs) -> ClickResult:
        try:
            region_size = kwargs.get("region_size", 40)
            x1 = max(0, x - region_size)
            y1 = max(0, y - region_size)
            x2 = x + region_size
            y2 = y + region_size

            screenshot = pyautogui.screenshot(region=(x1, y1, x2 - x1, y2 - y1))
            img = np.array(screenshot)
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edged = cv2.Canny(blurred, 30, 150)
            contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if contours:
                largest = max(contours, key=cv2.contourArea)
                M = cv2.moments(largest)
                if M["m00"] > 0:
                    cx = int(M["m10"] / M["m00"]) + x1
                    cy = int(M["m01"] / M["m00"]) + y1
                    pyautogui.click(cx, cy)
                    logger.info(f"LocalVision click at ({cx}, {cy})")
                    return ClickResult(True, cx, cy, self.name, 1.0)

            pyautogui.click(x, y)
            return ClickResult(True, x, y, self.name, 0.8)

        except Exception as e:
            logger.warning(f"LocalVisionClickStrategy failed: {e}")
            try:
                pyautogui.click(x, y)
                return ClickResult(True, x, y, self.name, 0.5)
            except Exception:
                return ClickResult(False, x, y, self.name, 0.0)
