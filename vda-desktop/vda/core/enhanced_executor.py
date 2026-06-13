import json
import logging
import os
import re
import time
from typing import Optional, Tuple, Union

import cv2
import numpy as np
import pyautogui

from vda.utils.safety import restore_failsafe

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
                         retries: int = 0) -> bool:
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
        # Return False if no pixel change detected — the LLM needs accurate feedback
        logger.warning(f"[ClickValidator] No pixel change detected at ({x}, {y}) after {retries+1} attempts")
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
            if action in ["type", "wait"]:
                return {
                    "action": action,
                    "x": 0,
                    "y": 0,
                    "text": data.get("text", ""),
                    "target_name": data.get("target_name", ""),
                    "target_text": data.get("target_text", ""),
                    "description": data.get("description", ""),
                    "confidence": float(data.get("confidence", 1.0)),
                }
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
            "text": data.get("text", ""),
            "target_name": data.get("target_name", ""),
            "target_text": data.get("target_text", ""),
            "description": data.get("description", ""),
            "confidence": float(data.get("confidence", 0.5)),
        }

    def execute(self, parsed: dict) -> Union[bool, str, dict]:
        """Execute a vision action (click, type, scroll, etc.).

        Flow for click/double_click/right_click/move:
          1. If target_name given AND matching template exists:
             a) Template match succeeds → use template coords (most accurate)
             b) Template match fails, SIFT succeeds → return sift_verify dict for LLM check
          2. If no template matched → use LLM coordinates directly (still works well)
          3. Execute the click/type/scroll action

        Returns:
            True on success, a dict for sift_verify, or False on failure.
        """
        action = parsed.get("action", "")
        x = parsed.get("x", 0)
        y = parsed.get("y", 0)
        target_name = parsed.get("target_name")
        target_text = parsed.get("target_text")

        template_matched = False
        text_matched = False

        # 1. Try OCR if target_text is provided
        if target_text and action in (self.CLICK, self.DOUBLE_CLICK, self.RIGHT_CLICK, self.MOVE, "type"):
            res = self.find_with_ocr(target_text, llm_x=x, llm_y=y)
            if res:
                x, y = res
                text_matched = True
                logger.info(f"[EnhancedExecutor] Found text '{target_text}' via OCR at ({x}, {y})")
            else:
                return f"Error: OCR could not find the exact text '{target_text}' on the screen. Please try another approach."

        # 2. Try template matching if target_name is provided
        elif target_name and action in (self.CLICK, self.DOUBLE_CLICK, self.RIGHT_CLICK, self.MOVE, "type"):
            template_dir = os.path.join(os.path.expanduser("~"), ".vda", "uied_templates")
            if os.path.exists(template_dir):
                import glob
                normalized_target = target_name.lower().replace(" ", "_").replace(".png", "")

                matched_paths = []
                for ext in ["*.png", "*.jpg", "*.jpeg"]:
                    for tpath in glob.glob(os.path.join(template_dir, ext)):
                        basename = os.path.basename(tpath).lower().replace(ext[1:], "")
                        if normalized_target in basename or basename in normalized_target:
                            matched_paths.append(tpath)

                for tpath in matched_paths:
                    res = self.find_with_template(tpath, threshold=0.65, llm_x=x, llm_y=y)
                    if res:
                        x, y, is_sift = res
                        if is_sift and not parsed.get("sift_verified"):
                            logger.info(f"[EnhancedExecutor] SIFT fallback triggered for '{target_name}'. Requesting LLM verification.")
                            pyautogui.moveTo(x, y, duration=0.2)
                            return {"action": "sift_verify", "x": x, "y": y, "target_name": target_name, "original_parsed": parsed}
                        logger.info(f"[EnhancedExecutor] Found '{target_name}' via template matching at ({x}, {y})")
                        template_matched = True
                        break

            if not template_matched:
                if action in (self.CLICK, self.DOUBLE_CLICK, self.RIGHT_CLICK, self.MOVE):
                    return f"Error: No template match found for '{target_name}'. LLM coordinates are strictly disabled."
                if action == "type":
                    # Don't click LLM coordinates — just type at current cursor position
                    logger.info(f"[EnhancedExecutor] No template for '{target_name}', typing at current cursor position.")
                    x, y = 0, 0  # Reset coords so type action doesn't click anywhere
        elif not target_name and not target_text and action in (self.CLICK, self.DOUBLE_CLICK, self.RIGHT_CLICK, self.MOVE):
            return f"Error: Cannot execute {action} without a target_name or target_text. LLM coordinates are strictly disabled."

        # --- Execute the action ---

        if action == "type":
            text = parsed.get("text", "")
            if text:
                if x != 0 and y != 0:
                    logger.info(f"[EnhancedExecutor] Auto-clicking ({x}, {y}) before typing.")
                    pyautogui.click(x, y)
                    time.sleep(0.3)
                pyautogui.write(text, interval=0.05)
            return True

        if action == "wait":
            time.sleep(2)
            return True

        if action in (self.CLICK, self.DOUBLE_CLICK, self.RIGHT_CLICK):
            res = ClickValidator.click_and_verify(x, y, action)
            if action == self.DOUBLE_CLICK:
                logger.info("[EnhancedExecutor] Waiting 1.5s after double_click for app to open")
                time.sleep(1.5)
            return res

        if action == "move":
            pyautogui.moveTo(x, y, duration=0.3)
            return True

        if action == "scroll":
            direction = parsed.get("direction", "down")
            amount = int(parsed.get("amount", 3))
            scroll_val = -amount if direction == "down" else amount
            pyautogui.scroll(scroll_val)
            return True

        if action == "key":
            key_combo = parsed.get("key", "")
            if key_combo:
                # Support combos like "ctrl+t", "ctrl+l", "alt+f4"
                if "+" in key_combo:
                    keys = [k.strip().lower() for k in key_combo.split("+")]
                    pyautogui.hotkey(*keys)
                else:
                    pyautogui.press(key_combo)
                    if key_combo.lower() == "enter":
                        logger.info("[EnhancedExecutor] Waiting 1.5s after Enter for page to load")
                        time.sleep(1.5)
            return True

        if action == "hotkey":
            keys = parsed.get("keys", [])
            if keys:
                pyautogui.hotkey(*keys)
            return True

        # Fallback: just click
        if x != 0 or y != 0:
            pyautogui.click(x, y)
        return True

    def find_with_template(self, template_path: str, threshold: float = 0.7, llm_x: int = 0, llm_y: int = 0) -> Optional[Tuple[int, int, bool]]:
        if not os.path.exists(template_path):
            return None
        try:
            template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
            if template is None:
                return None
            screenshot = pyautogui.screenshot()
            screen_np = np.array(screenshot)
            screen_gray = cv2.cvtColor(screen_np, cv2.COLOR_RGB2GRAY)

            # Step 1: Standard template matching
            result = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            if max_val >= threshold:
                h, w = template.shape
                cx = max_loc[0] + w // 2
                cy = max_loc[1] + h // 2
                return (cx, cy, False)

            # Step 2: SIFT Fallback
            logger.info(f"[EnhancedExecutor] Standard matching failed (val={max_val:.2f}), attempting SIFT fallback.")
            sift = cv2.SIFT_create()
            kp1, des1 = sift.detectAndCompute(template, None)
            kp2, des2 = sift.detectAndCompute(screen_gray, None)

            if des1 is None or len(des1) < 4:
                return None

            bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck=False)
            matches = bf.knnMatch(des1, des2, k=2)

            good_matches = []
            for m, n in matches:
                if m.distance < 0.75 * n.distance:
                    good_matches.append(m)

            if len(good_matches) >= 4:
                src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
                dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

                M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
                if M is not None:
                    h, w = template.shape
                    pts = np.float32([[0, 0], [0, h-1], [w-1, h-1], [w-1, 0]]).reshape(-1, 1, 2)
                    dst = cv2.perspectiveTransform(pts, M)

                    cx = int(np.mean(dst[:, 0, 0]))
                    cy = int(np.mean(dst[:, 0, 1]))

                    if 0 <= cx <= screen_gray.shape[1] and 0 <= cy <= screen_gray.shape[0]:
                        if llm_x != 0 and llm_y != 0:
                            dist = ((cx - llm_x) ** 2 + (cy - llm_y) ** 2) ** 0.5
                            if dist > 200:
                                logger.warning(f"[EnhancedExecutor] SIFT rejected: ({cx}, {cy}) is {dist:.1f}px from LLM ({llm_x}, {llm_y}).")
                                return None
                        logger.info(f"[EnhancedExecutor] SIFT fallback succeeded at ({cx}, {cy}).")
                        return (cx, cy, True)
        except Exception as e:
            logger.error(f"[EnhancedExecutor] Template matching error: {e}")
        return None

    def find_with_ocr(self, target_text: str, llm_x: int = 0, llm_y: int = 0):
        """Use RapidOCR to find exact screen coordinates of text."""
        try:
            import numpy as np
            import pyautogui
            from rapidocr_onnxruntime import RapidOCR

            ocr = RapidOCR()
            screenshot = pyautogui.screenshot()
            result, _ = ocr(np.array(screenshot))

            if not result:
                return None

            best_match = None
            best_dist = float('inf')
            target_lower = target_text.lower().strip()

            for box, text, score in result:
                # box is [ [x1,y1], [x2,y1], [x2,y2], [x1,y2] ]
                if target_lower in text.lower() or text.lower() in target_lower:
                    pts = np.array(box, np.int32)
                    cx = int(np.mean(pts[:, 0]))
                    cy = int(np.mean(pts[:, 1]))

                    if llm_x and llm_y:
                        dist = ((cx - llm_x)**2 + (cy - llm_y)**2)**0.5
                    else:
                        dist = 0

                    if dist < best_dist:
                        best_dist = dist
                        best_match = (cx, cy)

            return best_match
        except ImportError:
            logger.error("[EnhancedExecutor] rapidocr-onnxruntime not installed.")
            return None
        except Exception as e:
            logger.error(f"[EnhancedExecutor] OCR Error: {e}")
            return None
