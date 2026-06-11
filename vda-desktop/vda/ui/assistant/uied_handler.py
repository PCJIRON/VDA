"""UIED (UI Element Detection) operations mixin — overlay, template management, component actions."""

import json
import logging
import os
import re
from typing import List, Optional

logger = logging.getLogger(__name__)


class UIEDHandlerMixin:
    def trigger_uied_detection(self):
        if self._is_uied_detecting:
            logger.info("Box editor already open")
            return

        logger.info("Opening manual box editor overlay")
        self._is_uied_detecting = True
        self.uied_btn.set_detecting(True)

        self._show_uied_overlay([])

    def _show_uied_overlay(self, components: list):
        if self._uied_overlay is None:
            from vda.ui.uied_overlay import UIEDOverlayWidget
            self._uied_overlay = UIEDOverlayWidget(self)
            self._uied_overlay.component_edited.connect(self._on_uied_component_edited)
            self._uied_overlay.component_added.connect(self._on_uied_component_added)
            self._uied_overlay.component_deleted.connect(self._on_uied_component_deleted)
            self._uied_overlay.close_requested.connect(self._on_uied_overlay_closed)

        self._uied_overlay.set_components(components)
        self._uied_overlay.show()
        self._uied_overlay.activateWindow()

        logger.info("Manual box editor overlay shown")

    def _on_uied_component_edited(self, index: int, new_label: str, new_type: str):
        if 0 <= index < len(self._uied_components):
            comp = self._uied_components[index]
            comp['label'] = new_label
            comp['component_type'] = new_type

            old_path = comp.get('template_path')
            if old_path and os.path.exists(old_path):
                try:
                    template_dir = os.path.dirname(old_path)
                    safe_label = new_label.replace(' ', '_').replace('/', '_')[:40]
                    new_filename = f"{comp['id']}_{safe_label}_{new_type}.png"
                    new_path = os.path.join(template_dir, new_filename)
                    os.rename(old_path, new_path)
                    comp['template_path'] = new_path
                    logger.info(f"Template renamed: {new_filename}")
                except Exception as e:
                    logger.error(f"Failed to rename template: {e}")

            logger.info(f"Component {index} edited: {new_label} [{new_type}]")
            self._uied_overlay.set_components(self._uied_components)

    def _on_uied_component_added(self, x: int, y: int, w: int, h: int, label: str, comp_type: str):
        import uuid
        import cv2
        import numpy as np
        from PyQt6.QtWidgets import QApplication
        import pyautogui as _pag
        import time

        new_component = {
            'id': f"comp_user_{uuid.uuid4().hex[:6]}",
            'label': label,
            'component_type': comp_type,
            'x': x,
            'y': y,
            'width': w,
            'height': h,
            'center_x': x + w // 2,
            'center_y': y + h // 2,
            'confidence': 1.0,
            'template_path': None,
            '_template_gray': None,
            '_template_rgb': None,
        }

        try:
            logger.info(f"Capturing template at widget coordinates: ({x}, {y}) {w}x{h}")

            if self._uied_overlay:
                self._uied_overlay.hide()
                QApplication.processEvents()

            time.sleep(0.3)

            screenshot = _pag.screenshot()
            screenshot_np = np.array(screenshot)

            screen = QApplication.primaryScreen()
            geom = screen.geometry()
            qt_screen_w = geom.width()
            qt_screen_h = geom.height()
            img_h, img_w = screenshot_np.shape[:2]

            scale_x = img_w / qt_screen_w
            scale_y = img_h / qt_screen_h

            crop_x1 = max(0, int(x * scale_x))
            crop_y1 = max(0, int(y * scale_y))
            crop_x2 = min(img_w, int((x + w) * scale_x))
            crop_y2 = min(img_h, int((y + h) * scale_y))

            logger.info(f"Template crop: Qt({x},{y},{w},{h}) -> Pixel({crop_x1},{crop_y1},{crop_x2-crop_x1},{crop_y2-crop_y1}) scale=({scale_x:.2f},{scale_y:.2f})")

            template_rgb = screenshot_np[crop_y1:crop_y2, crop_x1:crop_x2]
            template_bgr = cv2.cvtColor(template_rgb, cv2.COLOR_RGB2BGR)

            if self._uied_overlay:
                self._uied_overlay.show()
                QApplication.processEvents()

            if template_bgr.size == 0:
                logger.error("Template crop is empty!")
                return

            logger.info(f"Template captured: {template_bgr.shape}")

            new_component['_template_rgb'] = template_bgr
            new_component['_template_gray'] = cv2.cvtColor(template_bgr, cv2.COLOR_BGR2GRAY)

            logger.info(f"Template captured successfully using pyautogui screenshot + crop")

        except Exception as e:
            logger.error(f"Failed to capture template: {e}", exc_info=True)

        self._uied_components.append(new_component)
        self._uied_overlay.set_components(self._uied_components)

        logger.info(f"New component added: {label} [{comp_type}] at ({x}, {y}) {w}x{h}")

    def _on_uied_component_deleted(self, index: int):
        if 0 <= index < len(self._uied_components):
            deleted = self._uied_components.pop(index)

            template_path = deleted.get('template_path')
            if template_path and os.path.exists(template_path):
                try:
                    os.remove(template_path)
                    logger.info(f"Template deleted: {template_path}")
                except Exception as e:
                    logger.error(f"Failed to delete template: {e}")

            self._uied_overlay.set_components(self._uied_components)

            logger.info(f"Component {index} deleted: {deleted.get('label')}")

    def _on_uied_overlay_closed(self):
        import cv2
        import numpy as np

        logger.info(f"Manual box editor closed. Final component count: {len(self._uied_components)}")

        saved_count = 0

        template_dir = os.path.join(
            os.path.expanduser("~"),
            ".vda",
            "uied_templates"
        )
        os.makedirs(template_dir, exist_ok=True)

        for comp_dict in self._uied_components:
            try:
                if '_template_rgb' in comp_dict and comp_dict['_template_rgb'] is not None:
                    template = comp_dict['_template_rgb']
                    safe_label = comp_dict.get('label', 'unknown').replace(' ', '_').replace('/', '_')[:40]
                    comp_type = comp_dict.get('component_type', 'other')
                    template_filename = f"{comp_dict.get('id', 'user')}_{safe_label}_{comp_type}.png"
                    template_path = os.path.join(template_dir, template_filename)
                    cv2.imwrite(template_path, template)
                    saved_count += 1
                    logger.info(f"Saved RGB template: {template_filename} {template.shape}")

                elif '_template_gray' in comp_dict and comp_dict['_template_gray'] is not None:
                    template_gray = comp_dict['_template_gray']
                    template = cv2.cvtColor(template_gray, cv2.COLOR_GRAY2BGR)
                    safe_label = comp_dict.get('label', 'unknown').replace(' ', '_').replace('/', '_')[:40]
                    comp_type = comp_dict.get('component_type', 'other')
                    template_filename = f"{comp_dict.get('id', 'user')}_{safe_label}_{comp_type}.png"
                    template_path = os.path.join(template_dir, template_filename)
                    cv2.imwrite(template_path, template)
                    saved_count += 1
                    logger.info(f"Saved grayscale template (fallback): {template_filename}")

            except Exception as e:
                logger.error(f"Failed to save template: {e}")

        self.history_popup.add_message(
            f"Box editor closed. {len(self._uied_components)} components created.\n"
            f"{saved_count} components labeled and saved to disk (RGB color).",
            "ai"
        )

        if self._uied_overlay:
            self._uied_overlay.hide()
            self._uied_overlay.close()
            self._uied_overlay = None

        self._uied_components = []
        self._is_uied_detecting = False
        self.uied_btn.set_has_results(False, 0)

    def _on_uied_component_selected(self, component: dict):
        logger.info(f"Component selected: {component.get('label')}")

        self.history_popup.add_message(
            f"Selected: **{component.get('label')}** "
            f"({component.get('component_type')}) at ({component.get('x')}, {component.get('y')})",
            "user"
        )

        self._last_uied_component = component

        self._handle_uied_component_action(component)

    def _handle_uied_component_action(self, component: dict):
        component_id = component.get('id')
        label = component.get('label', 'Unknown')
        template_path = component.get('template_path')

        logger.info(f"UIED: Handling action for '{label}' (id={component_id})")
        logger.info(f"UIED: Template path: {template_path}")
        logger.info(f"UIED: Component data: x={component.get('x')}, y={component.get('y')}, w={component.get('width')}, h={component.get('height')}")

        if not template_path:
            logger.warning(f"UIED: No template path for '{label}'")
            self.history_popup.add_message(
                f"No template saved for {label}",
                "ai"
            )
            return

        if not os.path.exists(template_path):
            logger.error(f"UIED: Template file not found: {template_path}")
            self.history_popup.add_message(
                f"Template file not found for {label}\nThe UI may have changed. Re-run detection.",
                "ai"
            )
            return

        if self._pyautogui_executor:
            logger.info(f"UIED: Attempting template matching with threshold=0.7")
            coords = self._pyautogui_executor.find_with_template(template_path, threshold=0.7)

            if coords:
                cx, cy = coords
                logger.info(f"UIED: Template match found at ({cx}, {cy})")
                self.history_popup.add_message(
                    f"Template match found at ({cx}, {cy}) - 100% accurate!",
                    "ai"
                )
                self._ask_uied_action(label, cx, cy, component)
                return
            else:
                logger.warning(f"UIED: Template match failed for '{label}'")

        cx = component.get('center_x') or (component.get('x', 0) + component.get('width', 0) // 2)
        cy = component.get('center_y') or (component.get('y', 0) + component.get('height', 0) // 2)

        logger.info(f"UIED: Using stored coordinates: ({cx}, {cy})")
        self.history_popup.add_message(
            f"Using stored coordinates: ({cx}, {cy})\nTemplate match failed - UI may have changed",
            "ai"
        )
        self._ask_uied_action(label, cx, cy, component)

    def _ask_uied_action(self, label: str, x: int, y: int, component: dict):
        from PyQt6.QtGui import QAction
        from PyQt6.QtWidgets import QMenu

        actions_menu = QMenu(self)
        actions_menu.setStyleSheet("""
            QMenu {
                background-color: #1f2937;
                color: white;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 8px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #6366f1;
            }
        """)

        click_act = QAction(f"Click '{label}'", self)
        click_act.triggered.connect(lambda: self._execute_uied_action('click', x, y, component))

        double_act = QAction(f"Double-click '{label}'", self)
        double_act.triggered.connect(lambda: self._execute_uied_action('double_click', x, y, component))

        type_act = QAction(f"Type into '{label}'", self)
        type_act.triggered.connect(lambda: self._execute_uied_action('type', x, y, component))

        actions_menu.addAction(click_act)
        actions_menu.addAction(double_act)
        actions_menu.addAction(type_act)

        actions_menu.exec(self.mapToGlobal(self.uied_btn.pos()))

    def _execute_uied_action(self, action: str, x: int, y: int, component: dict):
        label = component.get('label', 'Unknown')

        logger.info(f"UIED: Executing '{action}' at ({x}, {y}) for '{label}'")

        try:
            import pyautogui
            from vda.utils.safety import restore_failsafe

            screen_w, screen_h = pyautogui.size()

            if x < 0 or x >= screen_w or y < 0 or y >= screen_h:
                error_msg = f"Coordinates ({x}, {y}) out of bounds (screen: {screen_w}x{screen_h})"
                logger.error(f"UIED: {error_msg}")
                self.history_popup.add_message(f"Error: {error_msg}", "ai")
                return

            with restore_failsafe():
                if action == 'click':
                    logger.info(f"UIED: Moving to ({x}, {y}) and clicking")
                    pyautogui.moveTo(x, y, duration=0.3)
                    pyautogui.click()
                    self.history_popup.add_message(f"Clicked '{label}' at ({x}, {y})", "ai")

                elif action == 'double_click':
                    logger.info(f"UIED: Moving to ({x}, {y}) and double-clicking")
                    pyautogui.moveTo(x, y, duration=0.3)
                    pyautogui.doubleClick()
                    self.history_popup.add_message(f"Double-clicked '{label}' at ({x}, {y})", "ai")

                elif action == 'type':
                    logger.info(f"UIED: Moving to ({x}, {y}) and clicking for typing")
                    pyautogui.moveTo(x, y, duration=0.3)
                    pyautogui.click()
                    self.history_popup.add_message(
                        f"Clicked '{label}' - ready for typing.\nType your message in the input field.",
                        "ai"
                    )

            logger.info(f"UIED: Action '{action}' completed successfully")

        except Exception as e:
            error_msg = f"Action '{action}' failed: {str(e)}"
            logger.error(f"UIED: {error_msg}", exc_info=True)
            self.history_popup.add_message(f"Error: {error_msg}", "ai")

    def _execute_uied_from_llm(self, llm_response: str):
        json_match = re.search(r'```json\s*({.*?})\s*```', llm_response, re.DOTALL)
        if not json_match:
            json_match = re.search(r'({.*?"action".*?})', llm_response, re.DOTALL)

        if not json_match:
            logger.warning(f"No JSON found in LLM response: {llm_response[:200]}")
            return

        try:
            action_data = json.loads(json_match.group(1))
            action = action_data.get('action', 'click')
            target_name = action_data.get('target_name', '')
            description = action_data.get('description', '')

            target = action_data.get('target') or action_data.get('target_normalized')
            confidence = action_data.get('confidence', 1.0)

            logger.info(f"UIED-LLM: Parsed JSON: {action_data}")
            logger.info(f"UIED-LLM: Action={action}, Target={target_name}, Desc={description}")

            if action == 'wait':
                logger.info("UIED-LLM: Action is wait. Doing nothing.")
                self.history_popup.add_message(f"Waiting: {description}", "ai")
                return

            if not target_name and description:
                match = re.search(r'Found ([A-Za-z0-9\s\-_]+?)(?:\s+(?:icon|button|logo|text|element|in|at|on|the|a))', description, re.IGNORECASE)
                if match:
                    target_name = match.group(1).strip()
                    logger.info(f"UIED-LLM: Extracted target from description: '{target_name}'")
                else:
                    words = description.split()[:3]
                    target_name = ' '.join(words).replace('"', '').replace("'", '')[:30]
                    logger.info(f"UIED-LLM: Fallback target: '{target_name}'")

            coords = None
            if target_name:
                template_path = self._find_uied_template_for_target(target_name)
                if template_path:
                    logger.info(f"UIED-LLM: Found template: {template_path}")
                    coords = self._pyautogui_executor.find_with_template(template_path, threshold=0.7)
                else:
                    logger.warning(f"UIED-LLM: No manual template found for '{target_name}'")

            if coords:
                cx, cy = coords
                logger.info(f"UIED-LLM: Match found at ({cx}, {cy})")
                self.history_popup.add_message(
                    f"Found '{target_name}' at ({cx}, {cy}) via template matching.\nExecuting: {action}",
                    "ai"
                )
                self._execute_uied_action(action, cx, cy, {'label': target_name})
            else:
                logger.warning(f"UIED-LLM: Template matching failed or template not found for '{target_name}'")
                self.history_popup.add_message(
                    f"Template not found or not visible on screen for '{target_name}'. No action executed.",
                    "ai"
                )

        except json.JSONDecodeError as e:
            logger.error(f"UIED-LLM: Failed to parse JSON: {e}")
            logger.error(f"UIED-LLM: Raw response: {llm_response[:500]}")
            self.history_popup.add_message("Failed to parse LLM response", "ai")
        except Exception as e:
            logger.error(f"UIED-LLM: Error: {e}", exc_info=True)
            self.history_popup.add_message(f"Error: {e}", "ai")

    def _find_uied_template_for_target(self, target_name: str) -> Optional[str]:
        template_dir = os.path.join(
            os.path.expanduser("~"),
            ".vda",
            "uied_templates"
        )

        if not os.path.exists(template_dir):
            logger.warning(f"UIED-LLM: Template directory not found: {template_dir}")
            return None

        target_lower = target_name.lower().replace('_', ' ').strip()

        template_files = [f for f in os.listdir(template_dir) if f.endswith('.png')]

        logger.info(f"UIED-LLM: Searching {len(template_files)} templates for '{target_name}'")

        for template_file in template_files:
            label_part = template_file.replace('.png', '')
            label_lower = label_part.lower().replace('_', ' ')

            if target_lower in label_lower or label_lower in target_lower:
                template_path = os.path.join(template_dir, template_file)
                logger.info(f"UIED-LLM: Found match: {template_file}")
                return template_path

        target_words = target_lower.split()
        for template_file in template_files:
            label_part = template_file.replace('.png', '').lower().replace('_', ' ')

            matches = sum(1 for word in target_words if word in label_part and len(word) > 3)
            if matches >= 1:
                template_path = os.path.join(template_dir, template_file)
                logger.info(f"UIED-LLM: Found fuzzy match: {template_file} ({matches} words)")
                return template_path

        logger.warning(f"UIED-LLM: No matching template found for '{target_name}'")
        return None
