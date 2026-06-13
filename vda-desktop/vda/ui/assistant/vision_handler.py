"""Vision operations mixin — screenshot capture, VLM coordinate handling, template refinement."""

import logging
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


class VisionHandlerMixin:
    def toggle_vision(self):
        self.is_vision_enabled = not self.is_vision_enabled
        self.vision_btn.is_green = self.is_vision_enabled

        if self.is_vision_enabled:
            self.input_field.setPlaceholderText("Vision ON - Describe what to click...")
            self.history_popup.add_message(
                "Vision mode ON\nDescribe what to interact with on screen.",
                "ai",
            )
            self._update_vision_status_bar()
        else:
            self.input_field.setPlaceholderText("Ask AI...")
            self.history_popup.add_message("Vision mode OFF", "ai")
            self._update_vision_status_bar()

        self.update()

    def _delayed_vision_start(self):
        if not self.is_vision_enabled:
            return
        ok = self._vision_service.start()
        if not ok:
            self.is_vision_enabled = False
            self.vision_btn.is_green = False
            self.history_popup.add_message(
                "Vision requires pyautogui + pynput.\n"
                "Run: pip install pyautogui pynput Pillow",
                "ai",
            )
            self._update_vision_status_bar()
            self.update()

    def _update_vision_status_bar(self):
        try:
            import pyautogui
            sw, sh = pyautogui.size()
            mx, my = pyautogui.position()
            status = f"VISION ON  |  {sw}x{sh}  |  ({mx},{my})" if self.is_vision_enabled else ""
        except Exception:
            status = "VISION ON" if self.is_vision_enabled else ""
        self.history_popup.set_vision_status(status)

    def _on_vision_screenshot(self, b64: str, meta: dict):
        if not self.is_vision_enabled:
            return
        if not getattr(self, 'api_client', None) or not self._config.is_configured():
            return

        if hasattr(self, '_rate_limited') and self._rate_limited:
            logger.debug("Vision: rate-limited, skipping API request")
            self.history_popup.add_message(
                f"Screenshot captured (rate-limited) | ({meta['mouse_x']},{meta['mouse_y']})",
                "ai"
            )
            return

        sw = meta["screen_width"]
        sh = meta["screen_height"]
        mx = meta["mouse_x"]
        my = meta["mouse_y"]

        self._last_screen_resolution = (sw, sh)

        import base64
        import io

        from PIL import Image
        screenshot_img = Image.open(io.BytesIO(base64.b64decode(b64)))
        self._last_screenshot_size = (screenshot_img.width, screenshot_img.height)
        logger.info(f"Screenshot size: {screenshot_img.width}x{screenshot_img.height}, Screen resolution: {sw}x{sh}")

        vision_text = (
            f"[VISION METADATA]\n"
            f"Screen Resolution: {sw}x{sh}\n"
            f"Current Mouse Position: ({mx}, {my})\n\n"
            f"[TASK]\n"
            f"Analyze the attached screenshot. The user wants to interact with a UI element.\n"
            f"Use the current mouse position as context for what they're looking at.\n\n"
            f"[OUTPUT FORMAT]\n"
            f"Respond in this EXACT JSON format:\n"
            f"{{\n"
            f'  "action": "click",\n'
            f'  "target": [x, y],  // Pixel-perfect coordinates for {sw}x{sh} screen\n'
            f'  "confidence": 0.95,\n'
            f'  "description": "What element you found and why these coordinates"\n'
            f"}}\n\n"
            f"[IMPORTANT]\n"
            f"- Calculate coordinates for the FULL screen resolution ({sw}x{sh})\n"
            f"- If element is near current mouse, use those coordinates\n"
            f"- Be PRECISE - user will click exactly where you specify\n"
            f"- Center of buttons/icons is the best target\n"
        )

        payload = [
            {"type": "text", "text": vision_text},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
        ]

        self.history_popup.add_message(
            f"Vision: {sw}x{sh} | ({mx},{my})", "user"
        )
        self.history_popup.add_message("Analyzing...", "ai")

        if not self.is_expanded:
            self.toggle_expand()

        self._update_vision_status_bar()

        self.last_msg_uuid = self.session_service.save_message(
            self.session_id, "user", vision_text,
            attachments=[{"type": "image", "base64": b64, "mime": "image/png", "name": "screenshot.png"}],
            parent_uuid=self.last_msg_uuid,
        )

        prompted_history = self._build_history_with_prompt(self._chat_history)
        self.worker = self._create_worker(
            self.api_client, payload, prompted_history, vision_mode=True
        )

        self._chat_history.append({"role": "user", "content": payload})

    def _execute_vision_action(self, action: str, target: List[int], confidence: float, target_name: str = None):
        model_x, model_y = target[0], target[1]

        if target_name and self._use_ui_automation:
            logger.info(f"[UIA] Priority 1: Trying UI Automation for '{target_name}'...")
            ui_result = self._find_with_ui_automation(target_name)
            if ui_result:
                center_x, center_y, element_name = ui_result
                logger.info(f"[UIA] Found via UI Automation: ({center_x}, {center_y})")
                import pyautogui
                pyautogui.moveTo(center_x, center_y, duration=0.2)
                pyautogui.click()
                self.history_popup.add_message(f"Clicked '{element_name}' (UI Automation)", "ai")
                return

        if target_name and target_name in self._template_cache:
            logger.info(f"[OPENCV] Priority 2: Template found for '{target_name}'. Fast matching...")
            try:
                import cv2
                import numpy as np
                import pyautogui
                screen = np.array(pyautogui.screenshot())
                screen_bgr = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)
                screen_gray = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2GRAY)

                template_gray = self._template_cache[target_name]
                res = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

                if max_val >= self._template_threshold:
                    h, w = template_gray.shape
                    center_x = max_loc[0] + (w // 2)
                    center_y = max_loc[1] + (h // 2)
                    logger.info(f"[OPENCV] Exact match! Confidence: {max_val:.2f} at ({center_x}, {center_y})")
                    pyautogui.moveTo(center_x, center_y, duration=0.2)
                    pyautogui.click()
                    self.history_popup.add_message(f"Clicked '{target_name}' (OpenCV)", "ai")
                    return
                else:
                    logger.info(f"[OPENCV] Match failed ({max_val:.2f} < {self._template_threshold}). Re-learning...")
                    del self._template_cache[target_name]
            except Exception as e:
                logger.debug(f"[OPENCV] Error: {e}. Falling back to VLM...")
                if target_name in self._template_cache:
                    del self._template_cache[target_name]

        logger.info(f"[VLM] Priority 3: No UIA/Template. Using VLM for '{target_name or 'target'}'...")

        is_normalized = (0.0 <= model_x <= 1.0) and (0.0 <= model_y <= 1.0)

        if is_normalized:
            if hasattr(self, '_last_screenshot_size') and hasattr(self, '_last_screen_resolution'):
                screenshot_w, screenshot_h = self._last_screenshot_size
                screen_w, screen_h = self._last_screen_resolution

                ss_x = model_x * screenshot_w
                ss_y = model_y * screenshot_h

                ratio_x = screen_w / screenshot_w
                ratio_y = screen_h / screenshot_h

                real_x = int(ss_x * ratio_x)
                real_y = int(ss_y * ratio_y)

                logger.info(f"Normalized: [{model_x:.4f}, {model_y:.4f}]")
                logger.info(f"Screenshot: {screenshot_w}x{screenshot_h}")
                logger.info(f"Screenshot pixels: ({ss_x:.1f}, {ss_y:.1f})")
                logger.info(f"Ratio: {ratio_x:.6f} x {ratio_y:.6f}")
                logger.info(f"Screen (before refine): [{real_x}, {real_y}] ({screen_w}x{screen_h})")

                try:
                    import os

                    import cv2
                    import numpy as np
                    import pyautogui
                    fresh_ss = np.array(pyautogui.screenshot())
                    fresh_bgr = cv2.cvtColor(fresh_ss, cv2.COLOR_RGB2BGR)
                    fresh_gray = cv2.cvtColor(fresh_bgr, cv2.COLOR_BGR2GRAY)

                    crop_size = 80
                    bbox_w = crop_size
                    bbox_h = crop_size

                    x1 = max(0, int(ss_x) - bbox_w // 2)
                    y1 = max(0, int(ss_y) - bbox_h // 2)
                    x2 = min(screenshot_w, int(ss_x) + bbox_w // 2)
                    y2 = min(screenshot_h, int(ss_y) + bbox_h // 2)

                    crop_gray = fresh_gray[y1:y2, x1:x2]
                    crop_bgr = fresh_bgr[y1:y2, x1:x2]

                    if crop_gray.size > 0 and target_name:
                        self._template_cache[target_name] = crop_gray

                        debug_dir = os.path.join(os.path.expanduser("~"), ".vda-desktop", "templates")
                        os.makedirs(debug_dir, exist_ok=True)
                        template_path = os.path.join(debug_dir, f"{target_name}.png")
                        cv2.imwrite(template_path, crop_bgr)

                        logger.info(f"[LEARNED] Saved template for '{target_name}' (Size: {crop_gray.shape})")
                        logger.info(f"[LEARNED] Template saved to: {template_path}")
                except Exception as e:
                    logger.debug(f"Template extraction failed: {e}")

                target = [real_x, real_y]
            else:
                if hasattr(self, '_last_screen_resolution'):
                    screen_w, screen_h = self._last_screen_resolution
                    real_x = int(model_x * screen_w)
                    real_y = int(model_y * screen_h)
                    logger.warning(f"No screenshot size! Using screen: [{real_x}, {real_y}]")
                    target = [real_x, real_y]
                else:
                    logger.error("No screen resolution stored! Using normalized coords as-is")
        else:
            import pyautogui
            screen_w, screen_h = pyautogui.size()

            real_x = max(0, min(int(model_x), screen_w - 1))
            real_y = max(0, min(int(model_y), screen_h - 1))

            logger.info(f"Absolute pixel coords: [{model_x}, {model_y}] -> [{real_x}, {real_y}] (screen {screen_w}x{screen_h})")
            target = [real_x, real_y]

        if confidence < 0.7:
            self.history_popup.add_message(
                f"Low confidence ({confidence:.0%}). Should I proceed?",
                "ai",
            )
            return

        success = self._pyautogui_executor.execute(action, target, confidence)

        if success:
            if target_name:
                self.history_popup.add_message(f"Clicked '{target_name}' (VLM)", "ai")
            else:
                self.history_popup.add_message("Action completed!", "ai")
        else:
            self.history_popup.add_message("Action failed!", "ai")

    def _refine_with_template(self, screen_x: int, screen_y: int,
                               ss_x: int, ss_y: int,
                               screenshot_w: int, screenshot_h: int) -> Tuple[Optional[int], Optional[int]]:
        try:
            import cv2
            import numpy as np
            import pyautogui

            fresh_ss = pyautogui.screenshot()
            fresh_np = np.array(fresh_ss)
            fresh_bgr = cv2.cvtColor(fresh_np, cv2.COLOR_RGB2BGR)

            template_size = 40
            search_size = 80

            x1 = max(0, ss_x - template_size // 2)
            y1 = max(0, ss_y - template_size // 2)
            x2 = min(screenshot_w, ss_x + template_size // 2)
            y2 = min(screenshot_h, ss_y + template_size // 2)

            template = fresh_bgr[y1:y2, x1:x2].copy()

            if template.shape[0] < 10 or template.shape[1] < 10:
                return None, None

            sx1 = max(0, screen_x - search_size // 2)
            sy1 = max(0, screen_y - search_size // 2)
            sx2 = min(fresh_bgr.shape[1], screen_x + search_size // 2)
            sy2 = min(fresh_bgr.shape[0], screen_y + search_size // 2)

            search_area = fresh_bgr[sy1:sy2, sx1:sx2]

            if search_area.shape[0] < template.shape[0] or search_area.shape[1] < template.shape[1]:
                return None, None

            result = cv2.matchTemplate(search_area, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)

            if max_val < 0.6:
                logger.debug(f"Template match low: {max_val:.3f}")
                return None, None

            template_h, template_w = template.shape[:2]
            best_x_in_search = max_loc[0] + template_w // 2
            best_y_in_search = max_loc[1] + template_h // 2

            refined_screen_x = sx1 + best_x_in_search
            refined_screen_y = sy1 + best_y_in_search

            logger.debug(f"Template match: {max_val:.3f} at ({refined_screen_x}, {refined_screen_y})")

            return refined_screen_x, refined_screen_y

        except Exception as e:
            logger.debug(f"Template refinement error: {e}")
            return None, None
