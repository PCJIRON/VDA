"""Self-calibrator — empirical screenshot-to-screen ratio measurement.

Works on any OS / DPI without hard-coded values.
"""

import json
import logging
from typing import Tuple

import pyautogui

from qwen_desktop.utils.screen import ScreenEnv

logger = logging.getLogger(__name__)


class SelfCalibrator:
    """Empirical measurement: ratio = pag_size / ss_size"""

    def __init__(self, env: ScreenEnv):
        self.env = env
        self.calibration: dict = None

    def calibrate(self) -> dict:
        """Measure actual screenshot → screen ratio."""
        logger.info("[CALIBRATE] Running empirical calibration...")

        pag_w, pag_h = pyautogui.size()
        ss = pyautogui.screenshot()
        ss_w, ss_h = ss.size

        ratio_x = pag_w / ss_w if ss_w > 0 else 1.0
        ratio_y = pag_h / ss_h if ss_h > 0 else 1.0

        self.calibration = {
            "pyautogui_w": pag_w,
            "pyautogui_h": pag_h,
            "screenshot_w": ss_w,
            "screenshot_h": ss_h,
            "ratio_x": ratio_x,
            "ratio_y": ratio_y,
            "os": self.env.os,
            "is_hidpi": self.env.is_hidpi,
        }

        logger.info(f"[CALIBRATE] pyautogui:  {pag_w}×{pag_h}")
        logger.info(f"[CALIBRATE] screenshot: {ss_w}×{ss_h}")
        logger.info(f"[CALIBRATE] ratio:      {ratio_x:.6f} × {ratio_y:.6f}")
        return self.calibration

    def screenshot_px_to_screen(
        self, ss_x: float, ss_y: float, region_offset: Tuple[int, int] = (0, 0)
    ) -> Tuple[int, int]:
        """Convert screenshot pixel to screen coordinate."""
        if self.calibration is None:
            self.calibrate()

        c = self.calibration
        rel_screen_x = ss_x * c["ratio_x"]
        rel_screen_y = ss_y * c["ratio_y"]
        screen_x = rel_screen_x + region_offset[0]
        screen_y = rel_screen_y + region_offset[1]

        screen_x = max(0.0, min(screen_x, c["pyautogui_w"] - 1))
        screen_y = max(0.0, min(screen_y, c["pyautogui_h"] - 1))

        return round(screen_x), round(screen_y)

    def save(self, path: str = "calibration.json") -> None:
        if self.calibration:
            with open(path, "w") as f:
                json.dump(self.calibration, f, indent=2)
            logger.info(f"[CALIBRATE] Saved to {path}")

    def load(self, path: str = "calibration.json") -> bool:
        try:
            with open(path) as f:
                self.calibration = json.load(f)
            logger.info(f"[CALIBRATE] Loaded from {path}")
            return True
        except Exception as exc:
            logger.debug(f"Calibration load failed: {exc}")
            return False
