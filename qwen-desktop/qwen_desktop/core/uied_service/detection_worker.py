"""Worker thread for UI element detection and LLM labeling.

The original implementation lived in ``core/uied_service.py``.  It has been
extracted into its own module to reduce file size and improve testability.
"""

import base64
import io
import json
import logging
import os
import time
from dataclasses import asdict
from typing import List, Tuple, Optional

import cv2
import numpy as np
from PIL import Image
import pyautogui

from PyQt6.QtCore import QObject, pyqtSignal, QThread

logger = logging.getLogger(__name__)


class UIEDDetectionWorker(QThread):
    """Worker thread for UI element detection and optional LLM labeling.

    Signals:
        detection_complete(list) – list of UIComponent dicts (may be empty for manual mode)
        error_occurred(str) – error message
        progress_update(str) – human‑readable progress messages
    """

    detection_complete = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    progress_update = pyqtSignal(str)

    def __init__(self, screenshot_base64: str, api_client, template_dir: str):
        super().__init__()
        self.screenshot_base64 = screenshot_base64
        self.api_client = api_client
        self.template_dir = template_dir
        self._stop_flag = False

    def run(self) -> None:
        try:
            self.progress_update.emit("Decoding screenshot...")
            img_data = base64.b64decode(self.screenshot_base64)
            nparr = np.frombuffer(img_data, np.uint8)
            screenshot = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if screenshot is None:
                raise ValueError("Failed to decode screenshot")
            self.progress_update.emit("Detecting UI components...")
            # In this project we skip auto‑detection – user creates components manually.
            components = []  # type: List[object]
            self.progress_update.emit("Ready for manual labeling...")
            self.progress_update.emit("Done!")
            self.detection_complete.emit([])
        except Exception as e:
            logger.error(f"UIED detection failed: {e}", exc_info=True)
            self.error_occurred.emit(str(e))
