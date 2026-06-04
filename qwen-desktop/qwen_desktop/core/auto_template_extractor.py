import cv2
import numpy as np
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

TEMPLATE_DIR = os.path.join(os.path.expanduser("~"), ".qwen-desktop", "templates")


class AutoTemplateExtractor:
    def __init__(self):
        self._dir = Path(TEMPLATE_DIR)
        self._dir.mkdir(parents=True, exist_ok=True)

    def extract_ui_elements(self, screenshot: np.ndarray) -> list[dict]:
        gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        elements = []

        edges = cv2.Canny(gray, 30, 100)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        h, w = screenshot.shape[:2]
        for cnt in contours:
            x, y, bw, bh = cv2.boundingRect(cnt)
            if bw < 20 or bh < 20 or bw > w * 0.8 or bh > h * 0.8:
                continue
            area = cv2.contourArea(cnt)
            rect_area = bw * bh
            if rect_area == 0:
                continue
            solidity = area / rect_area
            aspect_ratio = bw / bh if bh > 0 else 0

            is_button = 0.4 < aspect_ratio < 2.5 and solidity > 0.7
            is_icon = 0.8 < aspect_ratio < 1.2 and solidity > 0.5 and 20 < bw < 80
            is_input = aspect_ratio > 3.0 and solidity < 0.5

            if not (is_button or is_icon or is_input):
                continue

            roi = screenshot[y:y+bh, x:x+bw]
            template = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            template_name = f"auto_{x}_{y}_{bw}_{bh}"

            elements.append({
                "name": template_name,
                "bbox": (x, y, bw, bh),
                "template": template,
                "type": "button" if is_button else ("icon" if is_icon else "input"),
                "solidity": round(solidity, 2),
                "aspect_ratio": round(aspect_ratio, 2),
                "center": (x + bw // 2, y + bh // 2),
            })

        logger.info(f"[AutoTemplate] Extracted {len(elements)} UI elements from screenshot")
        return elements

    def detect_text_regions(self, screenshot: np.ndarray) -> list[dict]:
        gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 30))
        horizontal_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel)
        vertical_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vertical_kernel)
        combined = cv2.bitwise_or(horizontal_lines, vertical_lines)
        contours, _ = cv2.findContours(combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        regions = []
        for cnt in contours:
            x, y, bw, bh = cv2.boundingRect(cnt)
            if bw < 50 or bh < 15 or bw > 500 or bh > 100:
                continue
            regions.append({
                "bbox": (x, y, bw, bh),
                "center": (x + bw // 2, y + bh // 2),
            })
        return regions

    def find_icons_in_region(self, screenshot: np.ndarray, region: tuple = None) -> list[dict]:
        if region:
            x, y, bw, bh = region
            roi = screenshot[y:y+bh, x:x+bw]
        else:
            roi = screenshot
            x, y = 0, 0
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        icons = []
        for cnt in contours:
            cx, cy, cw, ch = cv2.boundingRect(cnt)
            if cw < 15 or ch < 15 or cw > 60 or ch > 60:
                continue
            aspect = cw / ch if ch > 0 else 0
            if aspect < 0.5 or aspect > 2.0:
                continue
            icon_roi = gray[cy:cy+ch, cx:cx+cw]
            icons.append({
                "name": f"icon_{x+cx}_{y+cy}",
                "bbox": (x+cx, y+cy, cw, ch),
                "template": icon_roi,
                "center": (x+cx + cw//2, y+cy + ch//2),
            })
        return icons

    def save_template(self, template: np.ndarray, name: str) -> str:
        from datetime import datetime
        safe_name = "".join(c if c.isalnum() or c in '-_' else '_' for c in name)
        path = self._dir / f"{safe_name}_{datetime.now().strftime('%H%M%S')}.png"
        cv2.imwrite(str(path), template)
        logger.info(f"[AutoTemplate] Saved: {path.name}")
        return str(path)

    def save_all_templates(self, elements: list[dict]) -> list[str]:
        paths = []
        for el in elements:
            if "template" in el:
                p = self.save_template(el["template"], el["name"])
                paths.append(p)
        return paths
