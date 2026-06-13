"""Multi-scale template matching for UI element detection.

Extracted from the original monolithic ``PyAutoGUIExecutor``.
"""

import logging
import os
from typing import Optional, Tuple

import cv2
import numpy as np
import pyautogui

logger = logging.getLogger(__name__)


def find_with_template(
    template_path: str,
    threshold: float = 0.55,
    screen_resolution: Optional[Tuple[int, int]] = None,
) -> Optional[Tuple[int, int]]:
    """Find element on screen using multi-scale template matching.

    Tries matching at multiple scales (0.7x to 1.3x) to handle DPI
    mismatches between Qt grabWindow (physical pixels) and pyautogui
    screenshot output.

    Args:
        template_path: Path to the template image.
        threshold: Match confidence threshold (0.0-1.0).
        screen_resolution: Optional (width, height) for scaling.

    Returns:
        (center_x, center_y) tuple or None if not found.
    """
    logger.info(f"[TemplateMatch] Looking for: {template_path}")

    if not os.path.exists(template_path):
        logger.warning(f"[TemplateMatch] Template not found: {template_path}")
        return None

    try:
        template_orig = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
        if template_orig is None:
            logger.warning(f"[TemplateMatch] Failed to load template: {template_path}")
            return None

        logger.info(f"[TemplateMatch] Template size: {template_orig.shape}")

        screenshot = pyautogui.screenshot()
        screenshot_np = np.array(screenshot)
        screenshot_gray = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2GRAY)
        logger.info(f"[TemplateMatch] Screen size: {screenshot_gray.shape}")

        dpr = 1.0
        try:
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                screen = app.primaryScreen()
                if screen:
                    dpr = screen.devicePixelRatio()
        except Exception:
            pass

        scales_set = set()
        for base_scale in [1.0, 1.0 / dpr if dpr > 1.0 else 1.0, dpr if dpr > 1.0 else 1.0]:
            for delta in [-0.15, -0.05, 0.0, 0.05, 0.15]:
                s = round(base_scale + delta, 2)
                if 0.4 <= s <= 2.0:
                    scales_set.add(s)
        scales = sorted(scales_set)
        logger.info(f"[TemplateMatch] DPR={dpr}, trying {len(scales)} scales: {scales}")

        best_score = -1.0
        best_location = None
        best_scale = None
        best_template_shape = None

        for scale in scales:
            h_orig, w_orig = template_orig.shape[:2]
            new_w = max(1, int(w_orig * scale))
            new_h = max(1, int(h_orig * scale))
            if new_w >= screenshot_gray.shape[1] or new_h >= screenshot_gray.shape[0]:
                continue
            if new_w < 8 or new_h < 8:
                continue
            if scale == 1.0:
                template_scaled = template_orig
            else:
                template_scaled = cv2.resize(template_orig, (new_w, new_h), interpolation=cv2.INTER_AREA)
            result = cv2.matchTemplate(screenshot_gray, template_scaled, cv2.TM_CCOEFF_NORMED)
            _min_val, max_val, _min_loc, max_loc = cv2.minMaxLoc(result)

            if max_val > best_score:
                best_score = max_val
                best_location = max_loc
                best_scale = scale
                best_template_shape = template_scaled.shape

        logger.info(
            f"[TemplateMatch] Best match: score={best_score:.3f} at {best_location} scale={best_scale}"
        )

        if best_score >= threshold and best_location is not None and best_template_shape is not None:
            h, w = best_template_shape[:2]
            center_x = int(best_location[0] + w / 2)
            center_y = int(best_location[1] + h / 2)
            logger.info(
                f"[TemplateMatch] Match found: ({center_x}, {center_y}) "
                f"with {best_score:.3f} confidence at scale {best_scale}"
            )
            return (center_x, center_y)

        logger.info(
            f"[TemplateMatch] No match above threshold {threshold}. "
            f"Best: {best_score:.3f} at {best_location} scale={best_scale}"
        )
        return None

    except Exception as exc:
        logger.error(f"[TemplateMatch] Error: {exc}", exc_info=True)
        return None
