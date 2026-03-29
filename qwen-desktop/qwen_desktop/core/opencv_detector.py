"""
Zero-Shot OpenCV Detector.

Finds UI elements using edge detection, contours, and color - NO templates!
"""

import cv2
import numpy as np
from typing import Optional, Tuple, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class OpenCVDetector:
    """Zero-shot element detection using OpenCV."""
    
    def __init__(self):
        """Initialize detector."""
        pass
    
    def detect(
        self,
        screenshot: np.ndarray,
        element_type: str,
        description: str,
        search_area: Optional[Tuple[int, int, int, int]] = None,
    ) -> Optional[Tuple[int, int]]:
        """Detect element using appropriate technique.
        
        Args:
            screenshot: Screenshot as numpy array (BGR format).
            element_type: Type of element ("button", "icon", "color", "text").
            description: Text description (e.g., "red", "submit", "brush").
            search_area: Optional (x1, y1, x2, y2) to narrow search.
        
        Returns:
            (x, y) coordinates or None if not found.
        """
        # Crop to search area if provided
        if search_area:
            x1, y1, x2, y2 = search_area
            roi = screenshot[y1:y2, x1:x2]
        else:
            roi = screenshot
            x1, y1 = 0, 0
        
        # Choose detection technique based on description
        coords = None
        
        # Try color detection first (most accurate)
        if self._is_color_name(description):
            coords = self._detect_by_color(roi, description)
        
        # Try button/rectangular shape detection
        if coords is None and element_type in ["button", "text_field"]:
            coords = self._detect_by_contour(roi)
        
        # Try icon detection
        if coords is None and element_type in ["icon", "tool"]:
            coords = self._detect_icon(roi)
        
        # Adjust coordinates if we cropped
        if coords and search_area:
            coords = (coords[0] + x1, coords[1] + y1)
        
        return coords
    
    def _is_color_name(self, text: str) -> bool:
        """Check if text describes a color."""
        colors = ["red", "green", "blue", "yellow", "orange", "purple", 
                  "pink", "cyan", "magenta", "lime", "violet", "gold", "silver"]
        return any(color in text.lower() for color in colors)
    
    def _detect_by_color(
        self,
        image: np.ndarray,
        color_name: str,
    ) -> Optional[Tuple[int, int]]:
        """Detect element by color - ZERO templates!
        
        Args:
            image: Image as numpy array (BGR).
            color_name: Color name (e.g., "red", "blue").
        
        Returns:
            (x, y) center coordinates or None.
        """
        # Convert to HSV
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Define color ranges (HSV format: [Hue, Saturation, Value])
        # Note: Red wraps around 180°, so it needs two ranges
        color_ranges = {
            'red': ([0, 70, 50], [10, 255, 255]),  # Lower red range
            'green': ([40, 70, 50], [80, 255, 255]),
            'blue': ([100, 70, 50], [130, 255, 255]),
            'yellow': ([20, 70, 50], [35, 255, 255]),
            'orange': ([10, 70, 50], [25, 255, 255]),
            'purple': ([130, 70, 50], [160, 255, 255]),
            'cyan': ([80, 70, 50], [100, 255, 255]),
            'pink': ([140, 50, 50], [170, 255, 255]),
            'magenta': ([140, 70, 50], [160, 255, 255]),
            'lime': ([35, 70, 50], [45, 255, 255]),
            'violet': ([130, 50, 50], [140, 255, 255]),
            'gold': ([25, 50, 50], [35, 255, 255]),
            'silver': ([0, 0, 200], [180, 20, 255]),  # Gray-ish
        }
        
        if color_name.lower() not in color_ranges:
            return None
        
        lower, upper = color_ranges[color_name.lower()]
        lower = np.array(lower, dtype=np.uint8)
        upper = np.array(upper, dtype=np.uint8)
        
        # Create mask
        mask = cv2.inRange(hsv, lower, upper)
        
        # Red wraps around 180°, so create second mask for upper range
        if color_name.lower() == 'red':
            lower_red2 = np.array([170, 70, 50], dtype=np.uint8)
            upper_red2 = np.array([180, 255, 255], dtype=np.uint8)
            mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
            mask = cv2.bitwise_or(mask, mask2)
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            # Get largest contour
            largest = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest)
            return (x + w // 2, y + h // 2)
        
        return None
    
    def _detect_by_contour(
        self,
        image: np.ndarray,
    ) -> Optional[Tuple[int, int]]:
        """Detect button by rectangular contour - ZERO templates!
        
        Args:
            image: Image as numpy array (BGR).
        
        Returns:
            (x, y) center coordinates or None.
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        buttons = []
        for contour in contours:
            # Approximate to polygon
            approx = cv2.approxPolyDP(contour, 0.01 * cv2.arcLength(contour, True), True)
            
            # If 4 corners = rectangle
            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filter by size (typical button dimensions)
                if 50 < w < 300 and 20 < h < 100:
                    buttons.append((x + w // 2, y + h // 2, w * h))
        
        if buttons:
            # Return largest button (by area)
            buttons.sort(key=lambda b: b[2], reverse=True)
            return (buttons[0][0], buttons[0][1])
        
        return None
    
    def _detect_icon(
        self,
        image: np.ndarray,
    ) -> Optional[Tuple[int, int]]:
        """Detect toolbar icon by shape - ZERO templates!
        
        Args:
            image: Image as numpy array (BGR).
        
        Returns:
            (x, y) center coordinates or None.
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Threshold
        _, thresh = cv2.threshold(gray, 80, 255, cv2.THRESH_BINARY_INV)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        icons = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Tool icons are typically small (20-50px)
            if 20 < w < 50 and 20 < h < 50:
                # Calculate solidity
                area = cv2.contourArea(contour)
                hull_area = cv2.contourArea(cv2.convexHull(contour))
                solidity = area / hull_area if hull_area > 0 else 0
                
                if 0.3 < solidity < 0.9:
                    icons.append((x + w // 2, y + h // 2))
        
        if icons:
            return icons[0]  # Return first match
        
        return None
