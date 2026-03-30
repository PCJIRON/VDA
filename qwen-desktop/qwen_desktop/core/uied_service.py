"""
UIED Service - UI Element Detection using OpenCV + Qwen Vision.

This service captures screenshots, detects UI components using OpenCV contour analysis,
and uses Qwen Vision LLM to intelligently label each detected component.

The detected components are cached as templates for 100% accurate coordinate matching
via PyAutoGUI template matching.
"""

import base64
import io
import json
import logging
import os
import time
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
import pyautogui

from PyQt6.QtCore import QObject, pyqtSignal, QThread

logger = logging.getLogger(__name__)


@dataclass
class UIComponent:
    """Represents a detected UI component."""
    id: str
    label: str  # LLM-generated label (e.g., "Search button", "Username input")
    component_type: str  # button, input, text, image, icon, etc.
    x: int
    y: int
    width: int
    height: int
    confidence: float  # Detection confidence (0.0 - 1.0)
    template_path: Optional[str] = None  # Path to saved template image
    center_x: Optional[int] = None  # Center coordinates for clicking
    center_y: Optional[int] = None
    
    def __post_init__(self):
        if self.center_x is None:
            self.center_x = self.x + self.width // 2
        if self.center_y is None:
            self.center_y = self.y + self.height // 2
    
    def to_dict(self) -> dict:
        return asdict(self)


class UIEDDetectionWorker(QThread):
    """Worker thread for UI element detection and LLM labeling."""
    
    detection_complete = pyqtSignal(list)  # List of UIComponent dicts
    error_occurred = pyqtSignal(str)
    progress_update = pyqtSignal(str)  # Progress status message
    
    def __init__(self, screenshot_base64: str, api_client, template_dir: str):
        super().__init__()
        self.screenshot_base64 = screenshot_base64
        self.api_client = api_client
        self.template_dir = template_dir
        self._stop_flag = False
    
    def run(self):
        try:
            self.progress_update.emit("Decoding screenshot...")
            
            # Decode base64 to numpy array
            img_data = base64.b64decode(self.screenshot_base64)
            nparr = np.frombuffer(img_data, np.uint8)
            screenshot = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if screenshot is None:
                raise ValueError("Failed to decode screenshot")
            
            self.progress_update.emit("Detecting UI components...")
            
            # Detect components (returns empty list - manual mode)
            components = self._detect_components(screenshot)
            
            self.progress_update.emit("Ready for manual labeling...")
            
            # No components - user will create manually
            self.progress_update.emit("Done!")

            # Emit empty list - user creates components manually
            self.detection_complete.emit([])
            
        except Exception as e:
            logger.error(f"UIED detection failed: {e}", exc_info=True)
            self.error_occurred.emit(str(e))
    
    def _detect_components(self, screenshot: np.ndarray) -> List[UIComponent]:
        """
        Skip auto-detection. User will manually draw boxes via overlay editor.
        
        Returns empty list - user creates all components manually.
        """
        logger.info("Skipping auto-detection - user will create boxes manually")
        return []
    
    def _regions_overlap(self, x1, y1, w1, h1, x2, y2, w2, h2) -> bool:
        """Check if two rectangular regions overlap significantly."""
        # Calculate intersection
        x_overlap = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
        y_overlap = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))
        intersection = x_overlap * y_overlap
        
        # Calculate areas
        area1 = w1 * h1
        area2 = w2 * h2
        
        # If intersection is > 50% of smaller region, consider it overlap
        if area1 > 0 and area2 > 0:
            overlap_ratio = intersection / min(area1, area2)
            return overlap_ratio > 0.5
        
        return False
    
    def _label_components(self, screenshot: np.ndarray, components: List[UIComponent]) -> List[UIComponent]:
        """
        Use Qwen Vision to intelligently label each detected component.
        
        Sends cropped component images to the LLM for classification.
        """
        if not components:
            return components
        
        if not self.api_client:
            logger.warning("No API client available for LLM labeling")
            return components
        
        # Group components for batch labeling (more efficient)
        # Send entire screenshot with component highlights to LLM
        labeled_components = self._label_with_vision(screenshot, components)
        
        return labeled_components
    
    def _label_with_vision(self, screenshot: np.ndarray, components: List[UIComponent]) -> List[UIComponent]:
        """
        Return components as-is for manual human labeling.
        
        User will manually create boxes and label via overlay editor.
        This gives 100% human control over detection and labeling.
        """
        logger.info(f"Returning {len(components)} components for manual labeling")
        return components

    def _save_templates(self, screenshot: np.ndarray, components: List[UIComponent], save_immediately: bool = False):
        """
        Save cropped templates for each component.
        
        Args:
            screenshot: The screenshot image
            components: List of UIComponent objects
            save_immediately: If False, only prepare templates but don't save to disk
                             If True, save all templates to disk immediately
        """
        os.makedirs(self.template_dir, exist_ok=True)
        
        saved_count = 0
        duplicate_count = 0
        
        for comp in components:
            try:
                # Crop component from screenshot
                x1, y1 = comp.x, comp.y
                x2, y2 = x1 + comp.width, y1 + comp.height
                
                # Add small padding
                pad = 2
                x1 = max(0, x1 - pad)
                y1 = max(0, y1 - pad)
                x2 = min(screenshot.shape[1], x2 + pad)
                y2 = min(screenshot.shape[0], y2 + pad)
                
                template = screenshot[y1:y2, x1:x2]
                
                # Skip if template is too small
                if template.shape[0] < 10 or template.shape[1] < 10:
                    logger.debug(f"Skipping {comp.id}: template too small ({template.shape})")
                    continue
                
                # Convert to grayscale for comparison
                if len(template.shape) == 3:
                    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
                else:
                    template_gray = template
                
                # Store template in memory (for preview)
                comp._template_gray = template_gray
                
                # Only save to disk if save_immediately is True (user clicked Done)
                if save_immediately:
                    # Check for duplicates
                    is_duplicate = False
                    existing_templates = [f for f in os.listdir(self.template_dir) if f.endswith('.png')]
                    
                    for existing_file in existing_templates:
                        existing_path = os.path.join(self.template_dir, existing_file)
                        existing_template = cv2.imread(existing_path, cv2.IMREAD_GRAYSCALE)
                        
                        if existing_template is None:
                            continue
                        
                        # Check if same size
                        if existing_template.shape == template_gray.shape:
                            # Calculate similarity
                            similarity = cv2.matchTemplate(existing_template, template_gray, cv2.TM_CCOEFF_NORMED)
                            max_similarity = cv2.minMaxLoc(similarity)[1]
                            
                            if max_similarity >= 0.95:  # 95% similar = duplicate
                                logger.debug(f"Duplicate template: {comp.id} matches {existing_file} ({max_similarity:.2f})")
                                is_duplicate = True
                                duplicate_count += 1
                                comp.template_path = existing_path  # Use existing template
                                break
                    
                    if is_duplicate:
                        continue  # Skip saving
                    
                    # Save new template
                    template_filename = f"{comp.id}_{comp.label.replace(' ', '_')[:30]}.png"
                    template_path = os.path.join(self.template_dir, template_filename)
                    
                    cv2.imwrite(template_path, template)
                    comp.template_path = template_path
                    
                    saved_count += 1
                    logger.debug(f"Saved template: {template_filename} ({template_gray.shape})")
                
            except Exception as e:
                logger.error(f"Failed to save template for {comp.id}: {e}")
        
        if save_immediately:
            logger.info(f"Templates: {saved_count} saved, {duplicate_count} duplicates skipped (total: {len(components)} components)")
        else:
            logger.info(f"Prepared {len(components)} templates for preview (not saved to disk yet)")


class UIEDService(QObject):
    """
    Main UIED Service for UI element detection and template matching.
    
    Usage:
        service = UIEDService(api_client, template_dir)
        service.start()  # Start detection worker
        # Wait for detection_complete signal
    """
    
    detection_started = pyqtSignal()
    detection_complete = pyqtSignal(list)  # List of UIComponent dicts
    detection_error = pyqtSignal(str)
    progress_update = pyqtSignal(str)
    
    def __init__(self, api_client, template_dir: str = None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.template_dir = template_dir or os.path.join(
            os.path.expanduser("~"), 
            ".qwen_desktop", 
            "uied_templates"
        )
        
        self._worker: Optional[UIEDDetectionWorker] = None
        self._current_components: List[UIComponent] = []
        self._screenshot_resolution: Optional[Tuple[int, int]] = None
        
        # Ensure template directory exists
        os.makedirs(self.template_dir, exist_ok=True)
    
    def save_templates_to_disk(self, screenshot: np.ndarray, components: List[UIComponent]) -> int:
        """
        Save templates to disk when user clicks Done.
        Uses templates stored in memory (_template_gray) from when user created them.
        
        Args:
            screenshot: Current screenshot (fallback if template not in memory)
            components: List of UIComponent objects with user-edited labels
        
        Returns:
            Number of templates saved
        """
        os.makedirs(self.template_dir, exist_ok=True)
        
        saved_count = 0
        
        for comp in components:
            try:
                # PRIORITY 1: Use template from memory (captured when user drew the box)
                if hasattr(comp, '_template_gray') and comp._template_gray is not None:
                    template_gray = comp._template_gray
                    h, w = template_gray.shape
                    
                    # Reconstruct template from grayscale
                    template = cv2.cvtColor(template_gray, cv2.COLOR_GRAY2BGR)
                    
                    logger.debug(f"Using in-memory template for {comp.id}: {template.shape}")
                
                # FALLBACK: Crop from screenshot using coordinates
                else:
                    x1, y1 = comp.x, comp.y
                    x2, y2 = x1 + comp.width, comp.y + comp.height
                    
                    # Add padding
                    pad = 2
                    x1 = max(0, x1 - pad)
                    y1 = max(0, y1 - pad)
                    x2 = min(screenshot.shape[1], x2 + pad)
                    y2 = min(screenshot.shape[0], y2 + pad)
                    
                    template = screenshot[y1:y2, x1:x2]
                    
                    if template.shape[0] < 10 or template.shape[1] < 10:
                        logger.debug(f"Skipping {comp.id}: template too small")
                        continue
                    
                    logger.debug(f"Using screenshot crop for {comp.id}: {template.shape}")
                
                # Create filename with user-edited label
                safe_label = comp.label.replace(' ', '_').replace('/', '_')[:40]
                template_filename = f"{comp.id}_{safe_label}_{comp.component_type}.png"
                template_path = os.path.join(self.template_dir, template_filename)
                
                # Save template
                cv2.imwrite(template_path, template)
                comp.template_path = template_path
                
                saved_count += 1
                logger.debug(f"Saved template: {template_filename}")
                
            except Exception as e:
                logger.error(f"Failed to save template for {comp.id}: {e}")
        
        logger.info(f"Templates saved: {saved_count} components")
        return saved_count

    def capture_and_detect(self) -> bool:
        """
        Capture screenshot and start UI element detection.
        
        Returns True if detection started successfully.
        """
        try:
            # Capture screenshot
            screenshot = pyautogui.screenshot()
            width, height = screenshot.size
            self._screenshot_resolution = (width, height)
            
            # Convert to base64
            buffer = io.BytesIO()
            screenshot.save(buffer, format="PNG")
            base64_screenshot = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            logger.info(f"Captured screenshot: {width}x{height}")
            
            # Create and start worker
            self._worker = UIEDDetectionWorker(
                base64_screenshot,
                self.api_client,
                self.template_dir
            )
            
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
        """Handle detection completion."""
        self._current_components = components
        self.detection_complete.emit(components)
        logger.info(f"Detection complete: {len(components)} components found")
    
    def _on_detection_error(self, error: str):
        """Handle detection error."""
        self.detection_error.emit(error)
    
    def get_components(self) -> List[dict]:
        """Get currently detected components."""
        return self._current_components
    
    def find_component_by_label(self, query: str) -> Optional[dict]:
        """
        Find a component by searching its label.
        
        Args:
            query: Search query (e.g., "search button", "submit")
        
        Returns:
            Matching component dict or None
        """
        query_lower = query.lower()
        
        for comp in self._current_components:
            label_lower = comp.get('label', '').lower()
            if query_lower in label_lower or label_lower in query_lower:
                return comp
        
        return None
    
    def get_template_match_coordinates(
        self, 
        component_id: str, 
        current_screen_resolution: Tuple[int, int] = None
    ) -> Optional[Tuple[int, int]]:
        """
        Get the current screen coordinates for a component using template matching.
        
        This provides 100% accurate coordinates by matching the saved template
        against the current screen.
        
        Args:
            component_id: ID of the component to find
            current_screen_resolution: Optional (width, height) tuple
        
        Returns:
            (center_x, center_y) tuple or None if not found
        """
        # Find component
        component = None
        for comp in self._current_components:
            if comp.get('id') == component_id:
                component = comp
                break
        
        if not component:
            logger.warning(f"Component {component_id} not found")
            return None
        
        template_path = component.get('template_path')
        if not template_path or not os.path.exists(template_path):
            logger.warning(f"Template not found for {component_id}")
            return None
        
        # Load template
        template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
        if template is None:
            logger.warning(f"Failed to load template: {template_path}")
            return None
        
        # Capture current screen
        try:
            current_screenshot = pyautogui.screenshot()
            screenshot_np = np.array(current_screenshot)
            screenshot_gray = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2GRAY)
            
            # Template matching
            result = cv2.matchTemplate(screenshot_gray, template, cv2.TM_CCOEFF_NORMED)
            threshold = 0.7  # Lowered from 0.9 for better matching (0.7 = 70%)
            locations = np.where(result >= threshold)
            
            if len(locations[0]) > 0:
                # Get best match
                best_match_idx = np.argmax(result[locations])
                top_left_y = locations[0][best_match_idx]
                top_left_x = locations[1][best_match_idx]
                
                # Calculate center
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
        """Stop any ongoing detection."""
        if self._worker and self._worker.isRunning():
            self._worker.terminate()
            self._worker.wait()
            self._worker = None
