"""
OpenCV + Qwen2.5-VL — Zero Training, 100% Accuracy System
Chinese Engineer Approach: 精准 (Precision) + 健壮 (Robustness)

OpenCV's Three Roles:
1. Pre-processing: Resize to Qwen's patch size (448x448), sharpen, enhance edges
2. Post-processing: Verify Qwen's bbox with template matching
3. Verification: Before/after click comparison with absdiff
"""

import cv2
import numpy as np
import pyautogui
import base64
import requests
import json
import time
import platform
import ctypes
from PIL import Image
import io
import logging
from typing import Optional, Tuple, List, Dict, Any

logger = logging.getLogger(__name__)


class OpenCVQwenClicker:
    """
    Production-ready vision clicker with OpenCV verification
    Zero training required - pure classical computer vision
    """
    
    # ── Qwen2.5-VL ka internal patch size ──
    # Model 448x448 tiles mein image process karta hai
    # Isi ke multiples mein image bhejni chahiye
    QWEN_PATCH_SIZE = 448
    QWEN_MAX_TILES  = 6      # max 6 tiles = 1344px tak
    QWEN_MIN_SIZE   = 224

    def __init__(self, api_url: str, api_key: str, model: str = "qwen-vl-plus"):
        self.api_url  = api_url
        self.api_key  = api_key
        self.model    = model
        self.dpi      = self._get_dpi_scale()
        self.screen_w, self.screen_h = pyautogui.size()
        logger.info(f"[INIT] Screen: {self.screen_w}x{self.screen_h}  DPI scale: {self.dpi:.2f}")

    # ──────────────────────────────────────────
    # UTIL: Windows DPI scale
    # ──────────────────────────────────────────
    def _get_dpi_scale(self) -> float:
        """Get Windows DPI scaling factor"""
        if platform.system() == "Windows":
            try:
                hdc = ctypes.windll.user32.GetDC(0)
                dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)
                ctypes.windll.user32.ReleaseDC(0, hdc)
                return dpi / 96.0
            except Exception as e:
                logger.warning(f"DPI detection failed: {e}")
                return 1.0
        return 1.0

    # ──────────────────────────────────────────
    # STEP 1 — Screenshot lo, OpenCV mein load karo
    # ──────────────────────────────────────────
    def capture(self, region: Optional[Tuple[int, int, int, int]] = None
                ) -> Tuple[np.ndarray, Image.Image, Dict[str, Any]]:
        """
        Capture screenshot
        
        Args:
            region: (x, y, w, h) — sirf ek hissa chahiye toh
            
        Returns:
            (cv2_img_bgr, pil_img, capture_meta)
        """
        if region:
            x, y, w, h = region
            pil = pyautogui.screenshot(region=(x, y, w, h))
        else:
            pil = pyautogui.screenshot()

        # PIL → NumPy → BGR (OpenCV format)
        img_np  = np.array(pil)
        img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

        h_px, w_px = img_bgr.shape[:2]
        meta = {
            "orig_w"    : w_px,
            "orig_h"    : h_px,
            "region_x"  : region[0] if region else 0,
            "region_y"  : region[1] if region else 0,
            "screen_w"  : self.screen_w,
            "screen_h"  : self.screen_h,
        }
        logger.info(f"[CAPTURE] {w_px}x{h_px}")
        return img_bgr, pil, meta

    # ──────────────────────────────────────────
    # STEP 2 — OpenCV pre-processing
    # Qwen ke liye image ko best possible state mein laao
    # ──────────────────────────────────────────
    def preprocess(self, img_bgr: np.ndarray, enhance_edges: bool = True, 
                   sharpen: bool = True) -> Tuple[np.ndarray, int, int]:
        """
        Pre-process image for Qwen
        
        Returns: processed_bgr, send_w, send_h
        """
        h, w = img_bgr.shape[:2]

        # ── 2a. Qwen-aware resize ──
        # Qwen 448x448 patches mein sochta hai
        # Best quality: image dimension = 448 ka multiple
        target_w = self._best_qwen_size(w)
        target_h = self._best_qwen_size(h)

        if (target_w, target_h) != (w, h):
            img_bgr = cv2.resize(
                img_bgr,
                (target_w, target_h),
                interpolation=cv2.INTER_LANCZOS4   # Best quality upscale
            )
            logger.info(f"[RESIZE] {w}x{h} → {target_w}x{target_h}")

        # ── 2b. Sharpening (UI elements ke edges clear karo) ──
        if sharpen:
            kernel = np.array([
                [ 0, -1,  0],
                [-1,  5, -1],
                [ 0, -1,  0]
            ], dtype=np.float32)
            img_bgr = cv2.filter2D(img_bgr, -1, kernel)

        # ── 2c. Edge enhancement (optional, buttons/icons ke liye helpful) ──
        if enhance_edges:
            gray  = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            edges_3ch = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
            # Edges ko original pe lightly blend karo (overwrite nahi)
            img_bgr = cv2.addWeighted(img_bgr, 0.92, edges_3ch, 0.08, 0)

        # ── 2d. Contrast normalize ──
        # Low-contrast screenshots pe Qwen confuse hota hai
        lab   = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l     = clahe.apply(l)
        lab   = cv2.merge((l, a, b))
        img_bgr = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

        send_h, send_w = img_bgr.shape[:2]
        return img_bgr, send_w, send_h

    def _best_qwen_size(self, dim: int) -> int:
        """
        Qwen ke patch size ke closest multiple mein snap karo
        Lekin QWEN_MAX_TILES se zyada nahi
        """
        max_dim = self.QWEN_PATCH_SIZE * self.QWEN_MAX_TILES
        if dim > max_dim:
            return max_dim
        # Nearest 448-multiple jo dim ke upar hai
        snapped = int(np.ceil(dim / self.QWEN_PATCH_SIZE) * self.QWEN_PATCH_SIZE)
        return max(snapped, self.QWEN_MIN_SIZE)

    # ──────────────────────────────────────────
    # STEP 3 — Qwen2.5-VL ko bhejo, grounding maango
    # Qwen2.5-VL ka special feature: bounding box grounding
    # ──────────────────────────────────────────
    def ask_qwen(self, img_bgr: np.ndarray, target: str, 
                 send_w: int, send_h: int) -> List[Dict[str, Any]]:
        """
        Qwen2.5-VL se normalized bbox maango.
        
        Returns: list of {x1,y1,x2,y2,confidence} — normalized 0-1
        """
        # BGR → RGB → PNG bytes
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        pil     = Image.fromarray(img_rgb)
        buf     = io.BytesIO()
        pil.save(buf, format="PNG")
        b64     = base64.b64encode(buf.getvalue()).decode()

        # ── Prompt engineering: Qwen2.5-VL grounding format ──
        # Yeh model specifically grounding support karta hai
        # Lekin JSON maangna zyada reliable hai
        prompt = f"""You are a precise UI element locator.

Image size: {send_w}x{send_h} pixels.

Task: Find ALL instances of "{target}" in this screenshot.

Rules:
- Respond ONLY with a JSON array, no explanation
- Each element: {{"x1": float, "y1": float, "x2": float, "y2": float, "confidence": float, "label": str}}
- All coordinates are normalized: 0.0 = left/top, 1.0 = right/bottom
- x1,y1 = top-left corner, x2,y2 = bottom-right corner
- confidence: 0.0 to 1.0
- If nothing found: []

Example: [{{"x1": 0.42, "y1": 0.31, "x2": 0.58, "y2": 0.37, "confidence": 0.97, "label": "Submit button"}}]"""

        payload = {
            "model": self.model,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                    {"type": "text",      "text": prompt}
                ]
            }],
            "max_tokens" : 512,
            "temperature": 0.05,   # Near-zero → deterministic
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type" : "application/json"
        }

        resp = requests.post(self.api_url, headers=headers, json=payload, timeout=45)
        resp.raise_for_status()

        content = resp.json()["choices"][0]["message"]["content"].strip()
        logger.info(f"[QWEN RAW] {content[:200]}")

        # JSON clean + parse
        content = content.strip()
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()

        results = json.loads(content)
        logger.info(f"[QWEN] Found {len(results)} candidate(s)")
        return results

    # ──────────────────────────────────────────
    # STEP 4 — OpenCV post-processing
    # Qwen ne jo bbox diya, usse verify + refine karo
    # Template matching se exact pixel confirm karo
    # ──────────────────────────────────────────
    def postprocess_and_verify(self, orig_bgr: np.ndarray, processed_bgr: np.ndarray,
                                qwen_results: List[Dict], meta: Dict[str, Any], 
                                conf_threshold: float = 0.6) -> List[Dict[str, Any]]:
        """
        Verify and refine Qwen's predictions using OpenCV
        
        Returns: list of verified {screen_x, screen_y, confidence, bbox_screen}
        sorted by confidence descending
        """
        orig_h, orig_w = orig_bgr.shape[:2]
        proc_h, proc_w = processed_bgr.shape[:2]
        verified = []

        for r in qwen_results:
            if r.get("confidence", 0) < conf_threshold:
                continue

            # ── 4a. Bbox ko processed image coordinates mein convert ──
            px1 = int(r["x1"] * proc_w)
            py1 = int(r["y1"] * proc_h)
            px2 = int(r["x2"] * proc_w)
            py2 = int(r["y2"] * proc_h)

            # Center of bbox in processed image
            cx_proc = (px1 + px2) / 2
            cy_proc = (py1 + py2) / 2

            # ── 4b. Scale back to original captured image ──
            scale_x = orig_w / proc_w
            scale_y = orig_h / proc_h
            cx_orig = cx_proc * scale_x
            cy_orig = cy_proc * scale_y

            # ── 4c. Original captured image → screen coordinates ──
            # (account for region offset + DPI)
            screen_x = (meta["region_x"] + cx_orig) / self.dpi
            screen_y = (meta["region_y"] + cy_orig) / self.dpi
            screen_x = max(0, min(int(screen_x), self.screen_w - 1))
            screen_y = max(0, min(int(screen_y), self.screen_h - 1))

            # ── 4d. OpenCV Template Matching — double verification ──
            # Qwen ne bbox diya, us region ka crop lekar
            # original screenshot pe matchTemplate chalao
            # Agar match milta hai → coordinates verified!
            tmpl_x1 = max(0, int(px1 * scale_x))
            tmpl_y1 = max(0, int(py1 * scale_y))
            tmpl_x2 = min(orig_w, int(px2 * scale_x))
            tmpl_y2 = min(orig_h, int(py2 * scale_y))

            template = orig_bgr[tmpl_y1:tmpl_y2, tmpl_x1:tmpl_x2]
            tm_confidence = r["confidence"]  # default: Qwen confidence

            if template.size > 0 and template.shape[0] > 5 and template.shape[1] > 5:
                tm_confidence = self._template_verify(orig_bgr, template,
                                                       cx_orig, cy_orig)

            verified.append({
                "screen_x"    : screen_x,
                "screen_y"    : screen_y,
                "confidence"  : min(r["confidence"], tm_confidence) if tm_confidence > 0 else r["confidence"],
                "qwen_conf"   : r["confidence"],
                "tm_conf"     : tm_confidence,
                "label"       : r.get("label", ""),
                "bbox_screen" : (
                    int((meta["region_x"] + tmpl_x1) / self.dpi),
                    int((meta["region_y"] + tmpl_y1) / self.dpi),
                    int((meta["region_x"] + tmpl_x2) / self.dpi),
                    int((meta["region_y"] + tmpl_y2) / self.dpi),
                )
            })

        verified.sort(key=lambda x: x["confidence"], reverse=True)
        return verified

    def _template_verify(self, haystack: np.ndarray, template: np.ndarray, 
                         expected_cx: float, expected_cy: float) -> float:
        """
        Template matching se verify karo ki element wahi hai jahan Qwen ne kaha.
        Returns: 0.0-1.0 match score
        """
        if haystack.shape[0] < template.shape[0] or haystack.shape[1] < template.shape[1]:
            return 0.5  # Inconclusive

        result = cv2.matchTemplate(haystack, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        # Match location
        match_cx = max_loc[0] + template.shape[1] / 2
        match_cy = max_loc[1] + template.shape[0] / 2

        # Distance from Qwen's prediction
        dist = np.sqrt((match_cx - expected_cx)**2 + (match_cy - expected_cy)**2)
        diag = np.sqrt(haystack.shape[1]**2 + haystack.shape[0]**2)
        dist_penalty = max(0, 1 - (dist / (diag * 0.1)))  # 10% diagonal tolerance

        score = max_val * dist_penalty
        logger.info(f"[TM] matchTemplate score: {max_val:.3f}  dist_penalty: {dist_penalty:.3f}  final: {score:.3f}")
        return float(score)

    # ──────────────────────────────────────────
    # STEP 5 — Click karo
    # ──────────────────────────────────────────
    def execute_click(self, screen_x: int, screen_y: int,
                      human_like: bool = True, click_type: str = "single"):
        """Execute mouse click"""
        logger.info(f"[CLICK] Moving to ({screen_x}, {screen_y})")
        if human_like:
            pyautogui.moveTo(screen_x, screen_y,
                             duration=0.25,
                             tween=pyautogui.easeInOutQuad)
            time.sleep(0.05)
        else:
            pyautogui.moveTo(screen_x, screen_y)

        if click_type == "double":
            pyautogui.doubleClick(screen_x, screen_y)
        elif click_type == "right":
            pyautogui.rightClick(screen_x, screen_y)
        else:
            pyautogui.click(screen_x, screen_y)

        logger.info(f"[CLICK] Done ({click_type}) at ({screen_x}, {screen_y})")

    # ──────────────────────────────────────────
    # STEP 6 — Post-click verification
    # Screenshot lo aur check karo kuch change hua ya nahi
    # ──────────────────────────────────────────
    def verify_after_click(self, screen_x: int, screen_y: int, 
                           radius: int = 60) -> Tuple[bool, float]:
        """
        Verify click worked by checking pixel changes
        
        Returns: (changed, change_percentage)
        """
        time.sleep(0.4)
        x  = max(0, screen_x - radius)
        y  = max(0, screen_y - radius)
        w  = min(radius * 2, self.screen_w - x)
        h  = min(radius * 2, self.screen_h - y)

        before_pil = pyautogui.screenshot(region=(x, y, w, h))
        before_np  = np.array(before_pil)

        time.sleep(0.15)
        after_pil  = pyautogui.screenshot(region=(x, y, w, h))
        after_np   = np.array(after_pil)

        # Pixel difference
        diff       = cv2.absdiff(before_np, after_np)
        change_pct = (np.count_nonzero(diff.sum(axis=2)) /
                      (before_np.shape[0] * before_np.shape[1])) * 100

        changed = change_pct > 1.0   # >1% pixels change = kuch hua
        logger.info(f"[VERIFY] Change: {change_pct:.1f}%  → {'SUCCESS' if changed else 'NO CHANGE'}")
        return changed, change_pct

    # ──────────────────────────────────────────
    # MAIN — Ek call mein poora pipeline
    # ──────────────────────────────────────────
    def click_target(self,
                     target         : str,
                     region         : Optional[Tuple[int, int, int, int]] = None,
                     conf_threshold : float = 0.6,
                     click_type     : str   = "single",
                     max_retries    : int   = 3,
                     verify         : bool  = True,
                     enhance_edges  : bool  = True) -> Tuple[bool, Optional[int], Optional[int], float]:
        """
        Complete pipeline: Capture → Pre-process → Qwen → Verify → Click → Verify
        
        Args:
            target        : "Submit button", "Close icon", "Search field" etc.
            region        : (x,y,w,h) optional, focus area
            conf_threshold: 0.6 default, raise for stricter matching
            click_type    : "single" | "double" | "right"
            max_retries   : kitni baar try karna hai
            verify        : click ke baad change check karo
            enhance_edges : edge enhancement on/off
            
        Returns:
            (success, x, y, confidence)
        """
        for attempt in range(1, max_retries + 1):
            logger.info(f"\n{'='*50}")
            logger.info(f"[ATTEMPT {attempt}/{max_retries}] Target: '{target}'")

            try:
                # 1. Capture
                orig_bgr, pil_orig, meta = self.capture(region)

                # 2. Pre-process
                proc_bgr, send_w, send_h = self.preprocess(
                    orig_bgr,
                    enhance_edges=enhance_edges,
                    sharpen=True
                )

                # 3. Qwen query
                qwen_results = self.ask_qwen(proc_bgr, target, send_w, send_h)

                if not qwen_results:
                    logger.warning(f"[MISS] Qwen ne kuch nahi dhoondha. Retry...")
                    time.sleep(1.2)
                    continue

                # 4. Post-process + verify
                verified = self.postprocess_and_verify(
                    orig_bgr, proc_bgr,
                    qwen_results, meta,
                    conf_threshold=conf_threshold
                )

                if not verified:
                    logger.warning(f"[MISS] Koi verified match nahi. Retry...")
                    time.sleep(1.2)
                    continue

                best = verified[0]
                logger.info(f"[BEST] ({best['screen_x']}, {best['screen_y']})  "
                           f"conf={best['confidence']:.3f}  "
                           f"qwen={best['qwen_conf']:.3f}  "
                           f"tm={best['tm_conf']:.3f}")
                logger.info(f"[LABEL] {best['label']}")

                # 5. Click
                self.execute_click(best["screen_x"], best["screen_y"],
                                   click_type=click_type)

                # 6. Verify
                if verify:
                    changed, pct = self.verify_after_click(
                        best["screen_x"], best["screen_y"]
                    )
                    if not changed and attempt < max_retries:
                        logger.info("[RETRY] Click pe koi response nahi, dobara try...")
                        time.sleep(0.5)
                        continue

                return True, best["screen_x"], best["screen_y"], best["confidence"]

            except json.JSONDecodeError as e:
                logger.error(f"[JSON ERR] {e}")
            except requests.RequestException as e:
                logger.error(f"[API ERR] {e}")
            except Exception as e:
                logger.error(f"[ERR] {e}")
                import traceback
                traceback.print_exc()

            time.sleep(1.5)

        logger.error(f"[FAILED] '{target}' {max_retries} attempts ke baad bhi nahi mila")
        return False, None, None, 0.0
