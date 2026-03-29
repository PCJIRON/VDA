"""
Local Vision Clicker - No External API Required
Uses existing Qwen OAuth integration (1000 free requests/day)

Chinese Engineer Approach:
- 实事求是 (Seek truth from facts): Use what's available
- 精准 (Precision): Normalized coordinates
- 系统思维 (Systems Thinking): Closed-loop verification
"""

import pyautogui
from PIL import Image
import io
import base64
import time
import logging
from typing import Tuple, Optional, Dict, Any

logger = logging.getLogger(__name__)


class LocalVisionClicker:
    """
    Local Vision Clicker - No External API
    Uses existing Qwen OAuth integration from floating_assistant.py
    """
    
    def __init__(self, floating_assistant):
        """
        Initialize with reference to existing FloatingAssistant
        No new API keys needed - uses existing OAuth
        """
        self.assistant = floating_assistant
        self.dpi_scale = self._get_dpi_scale()
        logger.info(f"[INIT] DPI scale: {self.dpi_scale}")
    
    def _get_dpi_scale(self) -> float:
        """Detect Windows DPI scaling"""
        import platform
        import ctypes
        
        if platform.system() == "Windows":
            try:
                awareness = ctypes.c_int()
                ctypes.windll.shcore.GetProcessDpiAwareness(0, ctypes.byref(awareness))
                hdc = ctypes.windll.user32.GetDC(0)
                dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)
                ctypes.windll.user32.ReleaseDC(0, hdc)
                return dpi / 96.0
            except:
                return 1.0
        return 1.0
    
    def take_screenshot(self) -> Tuple[bytes, int, int]:
        """
        STEP 1: Screenshot lo aur EXACT size track karo
        PNG lossless format use karo
        """
        screenshot = pyautogui.screenshot()
        
        buffer = io.BytesIO()
        screenshot.save(buffer, format='PNG', optimize=True, compress_level=1)
        buffer.seek(0)
        img_bytes = buffer.getvalue()
        
        img_width, img_height = screenshot.size
        screen_width, screen_height = pyautogui.size()
        
        logger.info(f"[SCREENSHOT] Image: {img_width}x{img_height}, Screen: {screen_width}x{screen_height}")
        
        return img_bytes, img_width, img_height
    
    def build_vision_prompt(self, target_description: str, img_width: int, img_height: int) -> str:
        """
        STEP 2: Enhanced prompt for Qwen
        Normalized coordinates (0.0-1.0) maango
        """
        return f"""Look at this screenshot carefully.

Find the element: "{target_description}"

Respond ONLY in this exact JSON format, nothing else:
{{
    "found": true or false,
    "x_normalized": <float between 0.0 and 1.0, left=0, right=1>,
    "y_normalized": <float between 0.0 and 1.0, top=0, bottom=1>,
    "confidence": <float between 0.0 and 1.0>,
    "element_description": "<what you found>"
}}

Image resolution is {img_width}x{img_height} pixels.
x_normalized = element_center_x / {img_width}
y_normalized = element_center_y / {img_height}

Be precise - user will click exactly where you specify.
Center of buttons/icons is the best target."""
    
    def normalized_to_screen(self, x_norm: float, y_norm: float) -> Tuple[int, int]:
        """
        STEP 3: Normalized coordinates ko screen coordinates mein convert karo
        DPI compensation zaroori hai Windows pe
        """
        screen_w, screen_h = pyautogui.size()
        
        screen_x = int(x_norm * screen_w)
        screen_y = int(y_norm * screen_h)
        
        # DPI compensation
        screen_x = int(screen_x / self.dpi_scale)
        screen_y = int(screen_y / self.dpi_scale)
        
        # Boundary check
        screen_x = max(0, min(screen_x, screen_w - 1))
        screen_y = max(0, min(screen_y, screen_h - 1))
        
        return screen_x, screen_y
    
    def click_target(self, target_description: str, max_retries: int = 3) -> Tuple[bool, Optional[int], Optional[int]]:
        """
        MAIN FUNCTION: Click using existing Qwen integration
        No external API needed - uses OAuth from floating_assistant
        """
        for attempt in range(max_retries):
            logger.info(f"\n[ATTEMPT {attempt + 1}/{max_retries}] Target: '{target_description}'")
            
            try:
                # 1. Screenshot lo
                img_bytes, img_w, img_h = self.take_screenshot()
                
                # 2. Base64 encode
                img_b64 = base64.b64encode(img_bytes).decode()
                
                # 3. Build prompt
                prompt = self.build_vision_prompt(target_description, img_w, img_h)
                
                # 4. Use existing Qwen integration from floating_assistant
                # This uses the SAME OAuth token (1000 free requests/day)
                # No new API key needed!
                
                # Build payload for existing API client
                payload = [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
                ]
                
                # Use existing _handle_api method from assistant
                # This sends to Qwen via existing OAuth
                result_text = self._send_to_qwen(payload)
                
                # 5. Parse JSON response
                import json
                import re
                
                # Extract JSON from response
                json_match = re.search(r'\{[^}]*"x_normalized"[^}]*\}', result_text, re.DOTALL)
                if not json_match:
                    logger.error(f"[PARSE ERROR] No JSON found in: {result_text[:200]}")
                    time.sleep(1)
                    continue
                
                result = json.loads(json_match.group(0))
                
                if not result.get('found', False):
                    logger.warning(f"[MISS] Element not found. Retrying...")
                    time.sleep(1)
                    continue
                
                confidence = result.get('confidence', 0)
                logger.info(f"[CONFIDENCE] {confidence:.2f}")
                
                if confidence < 0.5:
                    logger.warning(f"[LOW CONF] Confidence too low ({confidence}). Retrying...")
                    time.sleep(1)
                    continue
                
                # 6. Convert to screen coordinates
                x_norm = result['x_normalized']
                y_norm = result['y_normalized']
                screen_x, screen_y = self.normalized_to_screen(x_norm, y_norm)
                
                logger.info(f"[COORDS] Normalized: ({x_norm:.4f}, {y_norm:.4f}) → Screen: ({screen_x}, {screen_y})")
                logger.info(f"[FOUND] {result.get('element_description', '')}")
                
                # 7. Human-like movement
                pyautogui.moveTo(screen_x, screen_y, duration=0.3, tween=pyautogui.easeInOutQuad)
                time.sleep(0.1)
                
                # 8. Click!
                pyautogui.click(screen_x, screen_y)
                logger.info(f"[CLICKED] Successfully clicked at ({screen_x}, {screen_y})")
                
                return True, screen_x, screen_y
                
            except Exception as e:
                logger.error(f"[ERROR] {e}")
                time.sleep(1.5)
        
        logger.error(f"[FAILED] Could not click '{target_description}' after {max_retries} attempts")
        return False, None, None
    
    def _send_to_qwen(self, payload: list) -> str:
        """
        Send to Qwen using existing OAuth integration
        No external API - uses floating_assistant's existing setup
        """
        # This uses the SAME OAuth token already configured
        # 1000 free requests/day - NO new API key needed!
        
        if not hasattr(self.assistant, 'api_client') or not self.assistant.api_client:
            logger.error("[ERROR] API client not available")
            return '{"found": false, "error": "API client not available"}'
        
        try:
            # Use existing API client from assistant
            # This is the SAME one used for regular chat
            import asyncio
            
            async def send_request():
                stream = self.assistant.api_client.client.chat.completions.create(
                    model="coder-model",  # Uses existing OAuth model
                    messages=[{"role": "user", "content": payload}],
                    max_tokens=200,
                    temperature=0.1,
                )
                
                full_response = ""
                async for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_response += chunk.choices[0].delta.content
                
                return full_response
            
            # Run async
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(send_request())
            loop.close()
            
            return result
            
        except Exception as e:
            logger.error(f"[API ERROR] {e}")
            return '{"found": false, "error": "' + str(e) + '"}'


# ============================================================
# USAGE EXAMPLE (Integrate with floating_assistant.py)
# ============================================================
if __name__ == "__main__":
    # Example of how to integrate:
    # 1. In floating_assistant.py, add this method:
    #
    # def click_with_vision(self, target_description: str):
    #     clicker = LocalVisionClicker(self)
    #     success, x, y = clicker.click_target(target_description)
    #     return success
    #
    # 2. Call from anywhere in your app:
    #    self.click_with_vision("Submit button")
    
    print("LocalVisionClicker - No API key needed!")
    print("Uses existing Qwen OAuth (1000 free requests/day)")
    print("\nIntegrate with floating_assistant.py to use.")
