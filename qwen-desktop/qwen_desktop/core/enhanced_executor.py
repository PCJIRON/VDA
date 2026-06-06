import json
import logging
import os
import re
import time
from typing import Optional, Tuple

import cv2
import numpy as np
import pyautogui

from qwen_desktop.utils.safety import restore_failsafe

logger = logging.getLogger(__name__)


def detect_coordinate_range(x: float, y: float, screen_w: int, screen_h: int) -> str:
    if x == 0 and y == 0:
        return "unknown"
    if 0.0 <= x <= 1.0 and 0.0 <= y <= 1.0:
        return "normalized_0_1"
    if 0.0 <= x <= 1000.0 and 0.0 <= y <= 1000.0:
        return "normalized_0_1000"
    if x <= screen_w and y <= screen_h:
        return "absolute_pixel"
    return "unknown"


def convert_to_screen(x: float, y: float, img_w: int, img_h: int,
                      screen_w: int, screen_h: int,
                      dpi_scale: float = 1.0) -> Tuple[int, int]:
    range_type = detect_coordinate_range(x, y, screen_w, screen_h)

    if range_type == "normalized_0_1":
        sx = x * img_w
        sy = y * img_h
        sx = int(sx * (screen_w / img_w) * dpi_scale)
        sy = int(sy * (screen_h / img_h) * dpi_scale)
    elif range_type == "normalized_0_1000":
        sx = int((x / 1000.0) * screen_w * dpi_scale)
        sy = int((y / 1000.0) * screen_h * dpi_scale)
    elif range_type == "absolute_pixel":
        sx = int(x * dpi_scale)
        sy = int(y * dpi_scale)
    else:
        sx = int(x)
        sy = int(y)

    sx = max(5, min(sx, screen_w - 5))
    sy = max(5, min(sy, screen_h - 5))
    return sx, sy


class ClickValidator:
    @staticmethod
    def capture_region(x: int, y: int, size: int = 10) -> np.ndarray:
        screenshot = pyautogui.screenshot(region=(x - size, y - size, size * 2, size * 2))
        return np.array(screenshot)

    @staticmethod
    def verify_pixel_change(before: np.ndarray, after: np.ndarray, threshold: float = 0.01) -> bool:
        if before.shape != after.shape:
            return False
        diff = cv2.absdiff(before, after)
        change_pct = np.sum(diff > 30) / diff.size
        return change_pct > threshold

    @staticmethod
    def click_and_verify(x: int, y: int, action: str = "click",
                         retries: int = 2) -> bool:
        for attempt in range(retries + 1):
            with restore_failsafe():
                try:
                    before = ClickValidator.capture_region(x, y)
                    if action == "click":
                        pyautogui.click(x, y)
                    elif action == "double_click":
                        pyautogui.doubleClick(x, y)
                    elif action == "right_click":
                        pyautogui.rightClick(x, y)
                    else:
                        pyautogui.click(x, y)
                    time.sleep(0.15)
                    after = ClickValidator.capture_region(x, y)
                    if ClickValidator.verify_pixel_change(before, after):
                        return True
                    if attempt < retries:
                        time.sleep(0.1)
                except Exception as e:
                    logger.warning(f"Click attempt {attempt + 1} failed: {e}")
        return False


class EnhancedExecutor:
    CLICK = "click"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    MOVE = "move"
    TYPE = "type"

    def __init__(self, mode: str = "ask_first"):
        self.mode = mode
        self.screen_w, self.screen_h = pyautogui.size()
        self.dpi_scale = self._detect_dpi()

    def _detect_dpi(self) -> float:
        try:
            import ctypes
            user32 = ctypes.windll.user32
            user32.SetProcessDPIAware()
            actual_w = user32.GetSystemMetrics(0)
            if actual_w and self.screen_w:
                return actual_w / self.screen_w
        except Exception:
            pass
        return 1.0

    def parse_coordinates(self, text: str, img_w: int, img_h: int) -> Optional[dict]:
        try:
            data = json.loads(text) if isinstance(text, str) else text
        except json.JSONDecodeError:
            match = re.search(r'\{[^}]*"action"[^}]*\}', text, re.DOTALL)
            if not match:
                return None
            try:
                data = json.loads(match.group(0))
            except json.JSONDecodeError:
                return None

        action = data.get("action", "click")
        target = data.get("target") or data.get("target_normalized") or data.get("coordinates")
        if not target or len(target) < 2:
            return None

        sx, sy = convert_to_screen(
            float(target[0]), float(target[1]),
            img_w, img_h,
            self.screen_w, self.screen_h,
            self.dpi_scale,
        )
        return {
            "action": action,
            "x": sx,
            "y": sy,
            "target_name": data.get("target_name", ""),
            "description": data.get("description", ""),
            "confidence": float(data.get("confidence", 0.5)),
        }

    def execute(self, parsed: dict) -> bool:
        action = parsed["action"]
        x, y = parsed["x"], parsed["y"]

        if action == "type":
            text = parsed.get("text", "")
            if text:
                pyautogui.write(text, interval=0.05)
            return True

        if action == "wait":
            import time
            time.sleep(2)
            return True

        if action in (self.CLICK, self.DOUBLE_CLICK, self.RIGHT_CLICK):
            return ClickValidator.click_and_verify(x, y, action)

        if action == "move":
            pyautogui.moveTo(x, y, duration=0.3)
            return True

        if action == "scroll":
            pyautogui.scroll(-3)
            return True

        pyautogui.click(x, y)
        return True

    def find_with_template(self, template_path: str, threshold: float = 0.7) -> Optional[Tuple[int, int]]:
        if not os.path.exists(template_path):
            return None
        try:
            template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
            if template is None:
                return None
            screenshot = pyautogui.screenshot()
            screen_np = np.array(screenshot)
            screen_gray = cv2.cvtColor(screen_np, cv2.COLOR_RGB2GRAY)
            result = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            if max_val >= threshold:
                h, w = template.shape
                cx = max_loc[0] + w // 2
                cy = max_loc[1] + h // 2
                return (cx, cy)
        except Exception:
            pass
        return None
