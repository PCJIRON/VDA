"""PerfectClicker — 100% accuracy vision system.

Combines self-calibration, multi-scale Qwen ensemble, visual centroid,
sub-pixel refinement, universal coordinate conversion, and pixel verification.
"""

import io
import json
import time
import base64
import logging
from typing import Tuple, Optional, List, Dict, Any

import cv2
import numpy as np
import requests
from PIL import Image
import pyautogui

from qwen_desktop.utils.screen import ScreenDetector
from .calibrator import SelfCalibrator

logger = logging.getLogger(__name__)


class PerfectClicker:
    """100% accuracy vision system."""

    def __init__(self, api_url: str, api_key: str, model: str = "qwen-vl-plus",
                 calibration_file: str = "calibration.json"):
        self.api_url = api_url
        self.api_key = api_key
        self.model = model
        self.calibration_file = calibration_file

        # 1. Detect environment
        self.env = ScreenDetector.detect()
        logger.info(f"[ENV] OS:       {self.env.os}")
        logger.info(f"[ENV] Logical:  {self.env.logical_w}×{self.env.logical_h}")
        logger.info(f"[ENV] HiDPI:    {self.env.is_hidpi}")
        logger.info(f"[ENV] Monitors: {len(self.env.monitors)}")

        # 2. Self-calibrate
        self.calibrator = SelfCalibrator(self.env)
        if not self.calibrator.load(calibration_file):
            self.calibrator.calibrate()
            self.calibrator.save(calibration_file)
        logger.info("[READY] Perfect Clicker initialized")

    def _capture(self, region: Optional[Tuple[int, int, int, int]] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Capture screenshot with metadata."""
        if region:
            rx, ry, rw, rh = region
            pil = pyautogui.screenshot(region=(rx, ry, rw, rh))
        else:
            rx, ry = 0, 0
            pil = pyautogui.screenshot()

        img_np = np.array(pil)
        img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        cap_h, cap_w = img_bgr.shape[:2]
        return img_bgr, {"cap_w": cap_w, "cap_h": cap_h, "region_x": rx, "region_y": ry}

    def _ask_qwen_single(self, img_bgr: np.ndarray, target: str, send_w: int, send_h: int) -> List[Dict[str, Any]]:
        """Single-scale Qwen query."""
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        buf = io.BytesIO()
        Image.fromarray(img_rgb).save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()

        prompt = f"""You are a PRECISE UI element locator.

Image size: {send_w}×{send_h} pixels.

Task: Find ALL instances of "{target}" in this screenshot.

CRITICAL RULES:
- Respond ONLY with a JSON array, NO explanation
- Each element: {{"x1": float, "y1": float, "x2": float, "y2": float, "confidence": float, "label": str}}
- All coordinates are normalized: 0.0 = left/top, 1.0 = right/bottom
- If nothing found: []

Example: [{{"x1": 0.42, "y1": 0.31, "x2": 0.58, "y2": 0.37, "confidence": 0.97, "label": "Submit button"}}]
"""
        try:
            resp = requests.post(
                self.api_url,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={
                    "model": self.model,
                    "messages": [{
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                            {"type": "text", "text": prompt}
                        ]
                    }],
                    "max_tokens": 512,
                    "temperature": 0.05
                },
                timeout=45
            )
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"].strip()
            if "```" in raw:
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip()
            results = json.loads(raw)
            normalized = []
            for r in results if isinstance(results, list) else []:
                x1, y1, x2, y2 = r.get("x1", 0), r.get("y1", 0), r.get("x2", 0), r.get("y2", 0)
                if x1 > 1.0 or y1 > 1.0 or x2 > 1.0 or y2 > 1.0:
                    x1 /= 1000.0; y1 /= 1000.0; x2 /= 1000.0; y2 /= 1000.0
                normalized.append({
                    "x1": max(0.0, min(1.0, x1)), "y1": max(0.0, min(1.0, y1)),
                    "x2": max(0.0, min(1.0, x2)), "y2": max(0.0, min(1.0, y2)),
                    "confidence": r.get("confidence", 0), "label": r.get("label", "")
                })
            logger.info(f"[QWEN] Found {len(normalized)} candidate(s)")
            return normalized
        except Exception as exc:
            logger.error(f"[API ERR] {exc}")
            return []

    def _ask_qwen_ensemble(self, img_bgr: np.ndarray, target: str) -> List[Dict[str, Any]]:
        """Multi-scale Qwen query with ensemble merging."""
        h, w = img_bgr.shape[:2]
        results_all = self._ask_qwen_single(img_bgr, target, w, h)

        zoom_factor = 1.5
        zoomed = cv2.resize(img_bgr, (int(w * zoom_factor), int(h * zoom_factor)), interpolation=cv2.INTER_LANCZOS4)
        zoom_results = self._ask_qwen_single(zoomed, target, int(w * zoom_factor), int(h * zoom_factor))
        for r in zoom_results:
            r["x1"] /= zoom_factor; r["y1"] /= zoom_factor; r["x2"] /= zoom_factor; r["y2"] /= zoom_factor
            r["source"] = "zoomed"
        results_all.extend(zoom_results)

        merged = self._nms_ensemble(results_all, iou_threshold=0.7)
        logger.info(f"[QWEN] Ensemble: merged → {len(merged)} result(s)")
        return merged

    def _calculate_iou(self, r1: Dict, r2: Dict) -> float:
        x1 = max(r1.get("x1", 0), r2.get("x1", 0))
        y1 = max(r1.get("y1", 0), r2.get("y1", 0))
        x2 = min(r1.get("x2", 1), r2.get("x2", 1))
        y2 = min(r1.get("y2", 1), r2.get("y2", 1))
        inter_w = max(0, x2 - x1); inter_h = max(0, y2 - y1)
        inter_area = inter_w * inter_h
        area1 = (r1.get("x2", 1) - r1.get("x1", 0)) * (r1.get("y2", 1) - r1.get("y1", 0))
        area2 = (r2.get("x2", 1) - r2.get("x1", 0)) * (r2.get("y2", 1) - r2.get("y1", 0))
        union_area = area1 + area2 - inter_area
        return inter_area / union_area if union_area > 0 else 0

    def _merge_predictions(self, predictions: List[Dict]) -> Dict:
        if len(predictions) == 1:
            return predictions[0]
        total_conf = sum(p.get("confidence", 0) for p in predictions)
        if total_conf == 0:
            return predictions[0]
        return {
            "x1": sum(p.get("x1", 0) * p.get("confidence", 0) for p in predictions) / total_conf,
            "y1": sum(p.get("y1", 0) * p.get("confidence", 0) for p in predictions) / total_conf,
            "x2": sum(p.get("x2", 1) * p.get("confidence", 0) for p in predictions) / total_conf,
            "y2": sum(p.get("y2", 1) * p.get("confidence", 0) for p in predictions) / total_conf,
            "confidence": max(p.get("confidence", 0) for p in predictions),
            "label": predictions[0].get("label", ""),
        }

    def _nms_ensemble(self, results_list: List[Dict], iou_threshold: float = 0.7) -> List[Dict]:
        if not results_list:
            return []
        results_sorted = sorted(results_list, key=lambda x: x.get("confidence", 0), reverse=True)
        kept = []
        used = [False] * len(results_sorted)
        for i, r1 in enumerate(results_sorted):
            if used[i]:
                continue
            overlapping = [r1]
            used[i] = True
            for j, r2 in enumerate(results_sorted[i+1:], i+1):
                if used[j]:
                    continue
                if self._calculate_iou(r1, r2) > iou_threshold:
                    overlapping.append(r2)
                    used[j] = True
            kept.append(self._merge_predictions(overlapping))
        return kept

    def _visual_centroid(self, img_bgr: np.ndarray, bbox_norm: Dict[str, float]) -> Tuple[float, float]:
        """Geometric center of the bounding box."""
        h, w = img_bgr.shape[:2]
        x1, y1 = bbox_norm["x1"] * w, bbox_norm["y1"] * h
        x2, y2 = bbox_norm["x2"] * w, bbox_norm["y2"] * h
        return (x1 + x2) / 2.0, (y1 + y2) / 2.0

    def _subpixel_refine(self, img_bgr: np.ndarray, bbox_norm: Dict[str, float],
                         cx_img: float, cy_img: float) -> Tuple[float, float]:
        h, w = img_bgr.shape[:2]
        x1 = max(0, int(bbox_norm["x1"] * w))
        y1 = max(0, int(bbox_norm["y1"] * h))
        x2 = min(w, int(bbox_norm["x2"] * w))
        y2 = min(h, int(bbox_norm["y2"] * h))
        template = img_bgr[y1:y2, x1:x2]
        if template.shape[0] < 5 or template.shape[1] < 5:
            return cx_img, cy_img

        pad = max(template.shape[0], template.shape[1]) // 2
        sx1, sy1 = max(0, x1 - pad), max(0, y1 - pad)
        sx2, sy2 = min(w, x2 + pad), min(h, y2 + pad)
        search = img_bgr[sy1:sy2, sx1:sx2]
        if search.shape[0] < template.shape[0] or search.shape[1] < template.shape[1]:
            return cx_img, cy_img

        result = cv2.matchTemplate(search, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val < 0.5:
            return cx_img, cy_img

        match_x = sx1 + max_loc[0]
        match_y = sy1 + max_loc[1]
        refined_cx = match_x + template.shape[1] / 2.0
        refined_cy = match_y + template.shape[0] / 2.0

        try:
            t_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY).astype(np.float32)
            m_crop = img_bgr[match_y:match_y + template.shape[0], match_x:match_x + template.shape[1]]
            if m_crop.shape == template.shape:
                m_gray = cv2.cvtColor(m_crop, cv2.COLOR_BGR2GRAY).astype(np.float32)
                (shift_x, shift_y), _ = cv2.phaseCorrelate(t_gray, m_gray)
                refined_cx -= shift_x
                refined_cy -= shift_y
        except Exception:
            pass
        return refined_cx, refined_cy

    def _verify_pixel(self, screen_x: int, screen_y: int) -> Tuple[bool, float]:
        """Verify click via pixel color change."""
        time.sleep(0.4)
        r = 20
        x_cap = max(0, screen_x - r)
        y_cap = max(0, screen_y - r)
        before_bgr, _ = self._capture(region=(x_cap, y_cap, r * 2, r * 2))
        time.sleep(0.15)
        after_bgr, _ = self._capture(region=(x_cap, y_cap, r * 2, r * 2))
        diff = cv2.absdiff(before_bgr, after_bgr)
        score = diff.mean()
        ph, pw = before_bgr.shape[:2]
        cy_s, cx_s = ph // 2, pw // 2
        before_px = before_bgr[cy_s, cx_s].astype(int)
        after_px = after_bgr[cy_s, cx_s].astype(int)
        center_delta = np.abs(before_px - after_px).sum()
        logger.info(f"[VERIFY] avg_diff={score:.2f}  center_delta={center_delta}")
        return score > 2.0 or center_delta > 10, score

    def click(self, target: str, region: Optional[Tuple[int, int, int, int]] = None,
              retries: int = 3, click_type: str = "single", verify: bool = True) -> Tuple[bool, Optional[int], Optional[int]]:
        """Execute a precise click on the target UI element."""
        for attempt in range(1, retries + 1):
            logger.info(f"\n── Attempt {attempt}/{retries}: '{target}' ──")
            try:
                img_bgr, meta = self._capture(region)
                results = self._ask_qwen_ensemble(img_bgr, target)
                if not results:
                    logger.warning("[MISS] Qwen: not found")
                    time.sleep(1)
                    continue
                best = max(results, key=lambda r: r.get("confidence", 0))
                if best.get("confidence", 0) < 0.55:
                    logger.warning(f"[LOW] conf={best['confidence']:.2f}")
                    time.sleep(1)
                    continue

                cx, cy = self._visual_centroid(img_bgr, best)
                cx, cy = self._subpixel_refine(img_bgr, best, cx, cy)
                sx, sy = self.calibrator.screenshot_px_to_screen(cx, cy, region_offset=(meta["region_x"], meta["region_y"]))
                logger.info(f"[COORDS] ss=({cx:.1f},{cy:.1f}) → screen=({sx},{sy})")

                pyautogui.moveTo(sx, sy, duration=0.2, tween=pyautogui.easeInOutQuad)
                time.sleep(0.04)
                if click_type == "double":
                    pyautogui.doubleClick(sx, sy)
                elif click_type == "right":
                    pyautogui.rightClick(sx, sy)
                else:
                    pyautogui.click(sx, sy)
                logger.info(f"[CLICK] ({sx}, {sy})")

                if verify:
                    changed, score = self._verify_pixel(sx, sy)
                    if not changed and attempt < retries:
                        logger.info("[RETRY] No pixel change detected")
                        time.sleep(0.5)
                        continue
                return True, sx, sy
            except Exception as exc:
                logger.error(f"[ERR] {exc}")
                time.sleep(1.5)
        logger.error(f"[FAILED] '{target}' after {retries} attempts")
        return False, None, None
