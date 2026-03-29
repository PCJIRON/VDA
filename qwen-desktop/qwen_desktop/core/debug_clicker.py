"""
Debug Clicker — Coordinate tracing ke liye

Har step pe coordinates print karta hai taaki error trace ho sake
"""

import cv2
import numpy as np
import pyautogui
import json
import time
import base64
import requests
import io
from PIL import Image
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class DebugClicker:
    """Debug version with detailed coordinate tracing"""

    def __init__(self, api_url: str, api_key: str, model: str = "qwen-vl-plus"):
        self.api_url = api_url
        self.api_key = api_key
        self.model = model

        # Calibration
        self.calibration = self._calibrate()

    def _calibrate(self) -> dict:
        """Simple calibration"""
        pag_w, pag_h = pyautogui.size()
        ss = pyautogui.screenshot()
        ss_w, ss_h = ss.size

        ratio_x = pag_w / ss_w if ss_w > 0 else 1.0
        ratio_y = pag_h / ss_h if ss_h > 0 else 1.0

        cal = {
            "pyautogui_w": pag_w,
            "pyautogui_h": pag_h,
            "screenshot_w": ss_w,
            "screenshot_h": ss_h,
            "ratio_x": ratio_x,
            "ratio_y": ratio_y,
        }

        print(f"\n{'='*60}")
        print(f"[CALIBRATION]")
        print(f"  pyautogui.size():   {pag_w}×{pag_h}")
        print(f"  screenshot.size():  {ss_w}×{ss_h}")
        print(f"  ratio_x: {ratio_x:.6f}")
        print(f"  ratio_y: {ratio_y:.6f}")
        print(f"{'='*60}\n")

        return cal

    def _ask_qwen(self, img_bgr: np.ndarray, target: str) -> dict:
        """Single Qwen query with detailed logging"""
        h, w = img_bgr.shape[:2]

        # Convert to base64
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        buf = io.BytesIO()
        Image.fromarray(img_rgb).save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()

        prompt = f"""Find: "{target}"
Image: {w}×{h}px
Return JSON ONLY:
{{"x1": float (0-1), "y1": float (0-1), "x2": float (0-1), "y2": float (0-1), "confidence": float}}
Coordinates normalized 0.0-1.0"""

        resp = requests.post(
            self.api_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": self.model,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                        {"type": "text", "text": prompt}
                    ]
                }],
                "max_tokens": 256,
                "temperature": 0.05
            },
            timeout=45
        )
        resp.raise_for_status()

        raw = resp.json()["choices"][0]["message"]["content"].strip()
        print(f"\n[QWEN RAW RESPONSE]")
        print(f"  {raw[:200]}\n")

        # Parse
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        result = json.loads(raw)

        print(f"[QWEN PARSED]")
        print(f"  x1: {result.get('x1', 'N/A')}")
        print(f"  y1: {result.get('y1', 'N/A')}")
        print(f"  x2: {result.get('x2', 'N/A')}")
        print(f"  y2: {result.get('y2', 'N/A')}")
        print(f"  confidence: {result.get('confidence', 'N/A')}\n")

        return result

    def _visual_centroid(self, img_bgr: np.ndarray, bbox_norm: dict) -> tuple:
        """
        Geometric center of bounding box.
        
        FIX: Removed OpenCV contour detection - it picks up text instead
        of button background, causing centroid to shift.
        """
        h, w = img_bgr.shape[:2]

        # Check if coordinates are in 0-1 or 0-1000 range
        x1_raw = bbox_norm["x1"]
        y1_raw = bbox_norm["y1"]
        x2_raw = bbox_norm["x2"]
        y2_raw = bbox_norm["y2"]

        # Detect range
        if x1_raw > 1.0 or y1_raw > 1.0:
            # 0-1000 range
            scale = 1000.0
            print(f"[COORD RANGE] Detected 0-1000 range")
        else:
            # 0-1 range
            scale = 1.0
            print(f"[COORD RANGE] Detected 0-1 range")

        # Convert to pixel coordinates
        x1 = (x1_raw / scale) * w
        y1 = (y1_raw / scale) * h
        x2 = (x2_raw / scale) * w
        y2 = (y2_raw / scale) * h

        print(f"\n[BBOX PIXELS]")
        print(f"  Image size: {w}×{h}")
        print(f"  Normalized: [{x1_raw:.4f}, {y1_raw:.4f}, {x2_raw:.4f}, {y2_raw:.4f}]")
        print(f"  Pixel bbox: [{x1:.0f}, {y1:.0f}, {x2:.0f}, {y2:.0f}]\n")

        # Simple geometric center (more reliable for UI elements)
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0
        
        print(f"[CENTROID] Geometric center: ({cx:.2f}, {cy:.2f})\n")
        return cx, cy

    def click(self, target: str):
        """Full click with debug tracing"""
        print(f"\n{'='*60}")
        print(f"[CLICK] Target: '{target}'")
        print(f"{'='*60}\n")

        # 1. Capture
        ss = pyautogui.screenshot()
        ss_w, ss_h = ss.size
        img_np = np.array(ss)
        img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

        print(f"[CAPTURE]")
        print(f"  Screenshot size: {ss_w}×{ss_h}")
        print(f"  Image shape: {img_bgr.shape}\n")

        # 2. Qwen
        result = self._ask_qwen(img_bgr, target)

        # 3. Visual centroid
        cx, cy = self._visual_centroid(img_bgr, result)

        # 4. Convert to screen (FIX: scale first, THEN add offset)
        # WRONG: (cx + region_x) * ratio  ← Scales the offset!
        # RIGHT: (cx * ratio) + region_x  ← Scale only screenshot pixels
        screen_x = (cx * self.calibration["ratio_x"])  # No region in simple debug
        screen_y = (cy * self.calibration["ratio_y"])

        print(f"[CONVERSION]")
        print(f"  Centroid: ({cx:.2f}, {cy:.2f})")
        print(f"  ratio_x: {self.calibration['ratio_x']:.6f}")
        print(f"  ratio_y: {self.calibration['ratio_y']:.6f}")
        print(f"  Screen: ({screen_x:.2f}, {screen_y:.2f})")
        print(f"  Rounded: ({round(screen_x)}, {round(screen_y)})\n")

        # 5. Debug visualization
        debug_img = img_bgr.copy()
        cv2.circle(debug_img, (round(cx), round(cy)), 10, (0, 255, 0), -1)
        cv2.imwrite("debug_click.png", debug_img)
        print(f"[DEBUG] Saved debug_click.png\n")

        # 6. Click
        print(f"[MOVING]")
        print(f"  Moving to: ({round(screen_x)}, {round(screen_y)})")
        print(f"  pyautogui.position(): {pyautogui.position()}\n")

        pyautogui.moveTo(round(screen_x), round(screen_y), duration=0.5)

        print(f"[CLICK]")
        print(f"  Final position: {pyautogui.position()}\n")

        pyautogui.click()

        time.sleep(1)

        print(f"[VERIFY]")
        print(f"  Position after click: {pyautogui.position()}\n")

        return round(screen_x), round(screen_y)


if __name__ == "__main__":
    clicker = DebugClicker(
        api_url="https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        api_key="YOUR_API_KEY_HERE",  # Replace with actual key
        model="qwen-vl-plus"
    )

    # Test click
    x, y = clicker.click("Submit button")

    print(f"\n{'='*60}")
    print(f"[RESULT]")
    print(f"  Clicked at: ({x}, {y})")
    print(f"  Expected: (should be on Submit button)")
    print(f"{'='*60}\n")
