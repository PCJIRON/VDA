"""UIED service – high‑level API for detection, labeling and template handling.

The original monolithic implementation was split into:
- ``models.UIComponent`` – dataclass for a component.
- ``detection_worker.UIEDDetectionWorker`` – background thread that decodes the
  screenshot, runs (currently skipped) detection and emits results.
- This file provides the ``UIEDService`` class that orchestrates the worker,
  saves templates, and offers helper methods for component lookup and
  template‑matching.
"""

import base64
import io
import logging
import os
from typing import List, Optional, Tuple

import cv2
import numpy as np
import pyautogui
from PyQt6.QtCore import QObject, pyqtSignal

from .detection_worker import UIEDDetectionWorker
from .models import UIComponent

logger = logging.getLogger(__name__)


class UIEDService(QObject):
    """Main UIED Service for UI element detection and template matching."""

    detection_started = pyqtSignal()
    detection_complete = pyqtSignal(list)
    detection_error = pyqtSignal(str)
    progress_update = pyqtSignal(str)

    def __init__(self, api_client, template_dir: str = None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.template_dir = template_dir or os.path.join(
            os.path.expanduser("~"),
            ".vda",
            "uied_templates",
        )
        self._worker: Optional[UIEDDetectionWorker] = None
        self._current_components: List[UIComponent] = []
        self._screenshot_resolution: Optional[Tuple[int, int]] = None
        os.makedirs(self.template_dir, exist_ok=True)

    def save_templates_to_disk(self, screenshot: np.ndarray, components: List[UIComponent]) -> int:
        """Save component templates when the user clicks Done."""
        os.makedirs(self.template_dir, exist_ok=True)
        saved_count = 0
        for comp in components:
            try:
                if hasattr(comp, "_template_gray") and comp._template_gray is not None:
                    template_gray = comp._template_gray
                    template = cv2.cvtColor(template_gray, cv2.COLOR_GRAY2BGR)
                else:
                    x1, y1 = comp.x, comp.y
                    x2, y2 = x1 + comp.width, y1 + comp.height
                    pad = 2
                    x1 = max(0, x1 - pad)
                    y1 = max(0, y1 - pad)
                    x2 = min(screenshot.shape[1], x2 + pad)
                    y2 = min(screenshot.shape[0], y2 + pad)
                    template = screenshot[y1:y2, x1:x2]
                safe_label = comp.label.replace(" ", "_").replace("/", "_")[:40]
                filename = f"{comp.id}_{safe_label}_{comp.component_type}.png"
                path = os.path.join(self.template_dir, filename)
                cv2.imwrite(path, template)
                comp.template_path = path
                saved_count += 1
                logger.debug(f"Saved template: {filename}")
            except Exception as e:
                logger.error(f"Failed to save template for {comp.id}: {e}")
        logger.info(f"Templates saved: {saved_count}")
        return saved_count

    def capture_and_detect(self) -> bool:
        """Capture screenshot and start UI element detection."""
        try:
            screenshot = pyautogui.screenshot()
            width, height = screenshot.size
            self._screenshot_resolution = (width, height)
            buffer = io.BytesIO()
            screenshot.save(buffer, format="PNG")
            base64_screenshot = base64.b64encode(buffer.getvalue()).decode("utf-8")
            logger.info(f"Captured screenshot: {width}x{height}")
            self._worker = UIEDDetectionWorker(base64_screenshot, self.api_client, self.template_dir)
            self._worker.detection_complete.connect(self._on_detection_complete)
            self._worker.error_occurred.connect(self._on_detection_error)
            self._worker.progress_update.connect(self.progress_update.emit)
            self._worker.start()
            self.detection_started.emit()
            return True
        except Exception as e:
            logger.error(f"Failed to capture and detect: {e}")
            self.detection_error.emit(str(e))
            return False

    def _on_detection_complete(self, components: list):
        self._current_components = components
        self.detection_complete.emit(components)
        logger.info(f"Detection complete: {len(components)} components found")

    def _on_detection_error(self, error: str):
        self.detection_error.emit(error)

    def get_components(self) -> List[dict]:
        return [comp.to_dict() for comp in self._current_components]

    def find_component_by_label(self, query: str) -> Optional[dict]:
        query_lower = query.lower()
        for comp in self._current_components:
            label_lower = comp.label.lower()
            if query_lower in label_lower or label_lower in query_lower:
                return comp.to_dict()
        return None

    def get_template_match_coordinates(self, component_id: str, current_screen_resolution: Tuple[int, int] = None) -> Optional[Tuple[int, int]]:
        component = None
        for comp in self._current_components:
            if comp.id == component_id:
                component = comp
                break
        if not component:
            logger.warning(f"Component {component_id} not found")
            return None
        template_path = component.template_path
        if not template_path or not os.path.exists(template_path):
            logger.warning(f"Template not found for {component_id}")
            return None
        template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
        if template is None:
            logger.warning(f"Failed to load template: {template_path}")
            return None
        try:
            current_screenshot = pyautogui.screenshot()
            screenshot_np = np.array(current_screenshot)
            screenshot_gray = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2GRAY)
            result = cv2.matchTemplate(screenshot_gray, template, cv2.TM_CCOEFF_NORMED)
            threshold = 0.7
            locations = np.where(result >= threshold)
            if len(locations[0]) > 0:
                best_match_idx = np.argmax(result[locations])
                top_left_y = locations[0][best_match_idx]
                top_left_x = locations[1][best_match_idx]
                h, w = template.shape
                center_x = int(top_left_x + w / 2)
                center_y = int(top_left_y + h / 2)
                logger.info(f"Template match found: ({center_x}, {center_y})")
                return (center_x, center_y)
            else:
                logger.debug(f"No template match found for {component_id}")
                return None
        except Exception as e:
            logger.error(f"Template matching failed: {e}")
            return None

    def stop(self):
        if self._worker and self._worker.isRunning():
            self._worker.terminate()
            self._worker.wait()
            self._worker = None
