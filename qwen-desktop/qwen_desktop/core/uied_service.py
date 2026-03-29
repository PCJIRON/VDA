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
            
            # Detect components using OpenCV
            components = self._detect_components(screenshot)
            
            self.progress_update.emit(f"Found {len(components)} components, labeling with AI...")
            
            # Label components using Qwen Vision
            labeled_components = self._label_components(screenshot, components)
            
            self.progress_update.emit("Saving templates...")
            
            # Save templates for each component
            self._save_templates(screenshot, labeled_components)
            
            self.progress_update.emit("Done!")
            
            # Emit result
            self.detection_complete.emit([comp.to_dict() for comp in labeled_components])
            
        except Exception as e:
            logger.error(f"UIED detection failed: {e}", exc_info=True)
            self.error_occurred.emit(str(e))
    
    def _detect_components(self, screenshot: np.ndarray) -> List[UIComponent]:
        """
        Detect UI components using OpenCV contour analysis.
        
        Uses a MULTI-SCALE approach:
        1. Large containers (panels, sidebars, toolbars)
        2. Medium elements (buttons, inputs, text blocks)
        3. Small elements (icons, checkboxes, small text)
        """
        gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape
        
        components = []
        component_id = 0
        
        # ── SCALE 1: LARGE CONTAINERS (panels, sidebars, toolbars) ────────────
        # Use larger minimum size for containers
        min_size_large = min(width, height) * 0.05  # 5% of screen
        max_size_large = max(width, height) * 0.5   # 50% of screen
        
        # Edge detection for large structures
        edges = cv2.Canny(gray, 30, 100, apertureSize=3)
        kernel = np.ones((5, 5), np.uint8)
        dilated_edges = cv2.dilate(edges, kernel, iterations=3)
        eroded_edges = cv2.erode(dilated_edges, kernel, iterations=2)
        
        contours_large, _ = cv2.findContours(
            eroded_edges,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        for contour in contours_large:
            x, y, w, h = cv2.boundingRect(contour)
            
            if w < min_size_large or h < min_size_large:
                continue
            if w > max_size_large or h > max_size_large:
                continue
            
            # Check if this is likely a container (large, rectangular)
            aspect_ratio = w / h if h > 0 else 0
            if aspect_ratio > 10 or aspect_ratio < 0.1:  # Very wide or tall
                continue
            
            component_id += 1
            components.append(UIComponent(
                id=f"comp_{component_id:03d}",
                label=f"Container {component_id}",
                component_type="container",
                x=x,
                y=y,
                width=w,
                height=h,
                confidence=0.7
            ))
        
        # ── SCALE 2: MEDIUM ELEMENTS (buttons, inputs, text blocks) ───────────
        min_size_medium = min(width, height) * 0.02  # 2% of screen
        max_size_medium = min(width, height) * 0.15  # 15% of screen
        
        # Adaptive threshold for medium elements
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 2
        )
        
        contours_medium, _ = cv2.findContours(
            thresh,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        for contour in contours_medium:
            x, y, w, h = cv2.boundingRect(contour)
            
            if w < min_size_medium or h < min_size_medium:
                continue
            if w > max_size_medium or h > max_size_medium:
                continue
            
            # Check if overlaps with existing component
            overlaps = False
            for comp in components:
                if self._regions_overlap(x, y, w, h, comp.x, comp.y, comp.width, comp.height):
                    # If overlaps with container, still add (it's a child element)
                    if comp.component_type != "container":
                        overlaps = True
                        break
            
            if not overlaps:
                component_id += 1
                components.append(UIComponent(
                    id=f"comp_{component_id:03d}",
                    label=f"Element {component_id}",
                    component_type="other",
                    x=x,
                    y=y,
                    width=w,
                    height=h,
                    confidence=0.6
                ))
        
        # ── SCALE 3: SMALL ELEMENTS (icons, checkboxes, small text) ───────────
        min_size_small = min(width, height) * 0.005  # 0.5% of screen
        max_size_small = min(width, height) * 0.03   # 3% of screen
        
        # Color-based detection for icons (look for color changes)
        color_edges = cv2.Canny(gray, 50, 150)
        kernel_small = np.ones((3, 3), np.uint8)
        dilated_small = cv2.dilate(color_edges, kernel_small, iterations=1)
        eroded_small = cv2.erode(dilated_small, kernel_small, iterations=0)
        
        contours_small, _ = cv2.findContours(
            eroded_small,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        for contour in contours_small:
            x, y, w, h = cv2.boundingRect(contour)
            
            if w < min_size_small or h < min_size_small:
                continue
            if w > max_size_small or h > max_size_small:
                continue
            
            # Check aspect ratio (icons are usually square-ish)
            aspect_ratio = w / h if h > 0 else 0
            if aspect_ratio > 3 or aspect_ratio < 0.33:
                continue  # Skip very thin elements (likely text lines)
            
            # Check if overlaps with existing
            overlaps = False
            for comp in components:
                if self._regions_overlap(x, y, w, h, comp.x, comp.y, comp.width, comp.height):
                    overlaps = True
                    break
            
            if not overlaps:
                component_id += 1
                components.append(UIComponent(
                    id=f"comp_{component_id:03d}",
                    label=f"Icon {component_id}",
                    component_type="icon",
                    x=x,
                    y=y,
                    width=w,
                    height=h,
                    confidence=0.65
                ))
        
        # Sort by position (top-to-bottom, left-to-right)
        components.sort(key=lambda c: (c.y // 50 * 50, c.x))
        
        logger.info(f"Detected {len(components)} UI components: "
                   f"{sum(1 for c in components if c.component_type == 'container')} containers, "
                   f"{sum(1 for c in components if c.component_type == 'icon')} icons, "
                   f"{sum(1 for c in components if c.component_type == 'other')} other")
        
        return components
    
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
        Label components using Qwen Vision on the full screenshot.
        
        This approach:
        1. Creates an annotated image with numbered boxes
        2. Sends to LLM with prompt to identify each numbered element
        3. Parses LLM response to update component labels
        """
        try:
            # Create annotated image with numbered boxes
            annotated = screenshot.copy()
            
            for i, comp in enumerate(components[:50]):  # Limit to 50 components
                # Draw rectangle
                cv2.rectangle(
                    annotated,
                    (comp.x, comp.y),
                    (comp.x + comp.width, comp.y + comp.height),
                    (0, 255, 0),  # Green box
                    2
                )
                
                # Draw number label
                cv2.putText(
                    annotated,
                    str(i + 1),
                    (comp.x + 5, comp.y + 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 0, 255),  # Red text
                    2
                )
            
            # Encode annotated image
            _, buffer = cv2.imencode('.png', annotated)
            base64_annotated = base64.b64encode(buffer).decode('utf-8')
            
            # Create prompt for LLM
            component_list = "\n".join([
                f"{i+1}. ({comp.x}, {comp.y}) - {comp.width}x{comp.height}"
                for i, comp in enumerate(components[:50])
            ])
            
            prompt = f"""You are a **UI/UX Labeling Expert**. Your task is to identify and label UI elements with PRECISE, DESCRIPTIVE names.

**ANALYSIS GUIDELINES:**
1. **Be Specific**: Not "button" → "Submit button", "Search icon", "Close X button"
2. **Include Context**: Mention the application (e.g., "VS Code Explorer icon", "Chrome tab close button")
3. **Identify by Function**: What does it do? (e.g., "Settings gear icon", "Notifications bell")
4. **Note Visual Features**: Color, shape, icon type (e.g., "Green play button", "Hamburger menu icon")
5. **Hierarchy Matters**: Distinguish between containers and elements
   - Large boxes → "VS Code sidebar", "Chrome address bar", "Window title bar"
   - Small elements → "File icon", "Text label", "Checkbox"

**COMPONENT TYPES (choose one):**
- `button` - Clickable buttons
- `icon` - Icons (gear, bell, home, etc.)
- `input` - Text input fields
- `text` - Text labels, titles
- `image` - Images, logos
- `container` - Panels, sidebars, toolbars, tabs
- `menu` - Menu items, dropdowns
- `checkbox` - Checkboxes, toggles
- `link` - Hyperlinks
- `other` - Anything else

**NUMBERED ELEMENTS TO LABEL:**
{component_list}

**RESPONSE FORMAT (JSON array only, no markdown):**
[
  {{"number": 1, "label": "VS Code Explorer sidebar panel", "type": "container"}},
  {{"number": 2, "label": "File tree icon", "type": "icon"}},
  {{"number": 3, "label": "Search input field", "type": "input"}},
  ...
]

**IMPORTANT:**
- Label ALL {min(len(components), 50)} elements
- Be DESCRIPTIVE but CONCISE (3-6 words max)
- Use ENGLISH only
- If unsure, describe what you see (e.g., "Blue circular icon with white arrow")"""

            # Call Qwen Vision API
            import asyncio
            from qwen_desktop.core.api_client import APIClient
            
            async def call_vision():
                messages = [{
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{base64_annotated}"}
                        },
                        {"type": "text", "text": prompt}
                    ]
                }]
                
                response_text = ""
                async for chunk in self.api_client.send_message(
                    prompt, 
                    messages, 
                    vision_mode=True
                ):
                    response_text += chunk
                
                return response_text
            
            # Run async call
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response_json = loop.run_until_complete(call_vision())
            finally:
                loop.close()
            
            # Parse LLM response
            labeled_components = components.copy()
            
            # Extract JSON from response
            json_start = response_json.find('[')
            json_end = response_json.rfind(']') + 1
            
            if json_start >= 0 and json_end > json_start:
                try:
                    labels_data = json.loads(response_json[json_start:json_end])
                    
                    for item in labels_data:
                        num = item.get('number', 0)
                        if 1 <= num <= len(labeled_components):
                            idx = num - 1
                            labeled_components[idx].label = item.get('label', labeled_components[idx].label)
                            labeled_components[idx].component_type = item.get('type', 'other')
                            labeled_components[idx].confidence = 0.95  # High confidence from LLM
                    
                    logger.info(f"Successfully labeled {len(labels_data)} components via LLM")
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse LLM JSON response: {e}")
                    logger.debug(f"Raw response: {response_json}")
            else:
                logger.warning("No valid JSON found in LLM response")
            
            return labeled_components
            
        except Exception as e:
            logger.error(f"Vision labeling failed: {e}")
            return components
    
    def _save_templates(self, screenshot: np.ndarray, components: List[UIComponent]):
        """
        Save cropped templates for each component.
        
        These templates will be used for 100% accurate template matching.
        Avoids saving duplicate templates by checking if similar template exists.
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
                
                # ── DUPLICATE CHECK: Compare with existing templates ──
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
                            comp._template_gray = template_gray
                            break
                
                if is_duplicate:
                    continue  # Skip saving
                
                # Save new template
                template_filename = f"{comp.id}_{comp.label.replace(' ', '_')[:30]}.png"
                template_path = os.path.join(self.template_dir, template_filename)
                
                cv2.imwrite(template_path, template)
                comp.template_path = template_path
                comp._template_gray = template_gray
                
                saved_count += 1
                logger.debug(f"Saved template: {template_filename} ({template_gray.shape})")
                
            except Exception as e:
                logger.error(f"Failed to save template for {comp.id}: {e}")
        
        logger.info(f"Templates: {saved_count} saved, {duplicate_count} duplicates skipped (total: {len(components)} components)")


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
