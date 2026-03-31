"""
OCR Service for Text Detection and Coordinate Extraction.

Uses EasyOCR to detect text on screen and return coordinates.
Coordinates can be used for precise clicking when labels are not available.
"""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Try to import easyocr
try:
    import easyocr
    OCR_AVAILABLE = True
    logger.info("EasyOCR imported successfully")
except ImportError:
    OCR_AVAILABLE = False
    logger.warning("EasyOCR not installed - OCR features disabled")
    logger.warning("Install with: pip install easyocr")

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("OpenCV not available")


@dataclass
class TextDetection:
    """Represents detected text with coordinates."""
    text: str
    confidence: float
    x: int  # Top-left x coordinate
    y: int  # Top-left y coordinate
    width: int
    height: int
    center_x: int
    center_y: int
    
    def to_dict(self) -> dict:
        return {
            'text': self.text,
            'confidence': self.confidence,
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'center_x': self.center_x,
            'center_y': self.center_y
        }


class OCRService:
    """
    OCR service for detecting text on screen.
    
    Usage:
        ocr = OCRService()
        detections = ocr.detect_text(screenshot_image)
        for detection in detections:
            print(f"Found '{detection.text}' at ({detection.center_x}, {detection.center_y})")
    """
    
    def __init__(self, languages: List[str] = ['en'], gpu: bool = False):
        """
        Initialize OCR service.
        
        Args:
            languages: List of language codes (e.g., ['en'], ['en', 'hi'])
            gpu: Whether to use GPU acceleration (requires CUDA)
        """
        self.reader = None
        self.languages = languages
        self.gpu = gpu
        
        if OCR_AVAILABLE and CV2_AVAILABLE:
            try:
                self.reader = easyocr.Reader(languages, gpu=gpu)
                logger.info(f"OCR reader initialized with languages: {languages}")
            except Exception as e:
                logger.error(f"Failed to initialize OCR reader: {e}")
    
    def detect_text(self, image) -> List[TextDetection]:
        """
        Detect text in image and return with coordinates.
        
        Args:
            image: Can be:
                - numpy array (OpenCV format)
                - PIL Image
                - File path (string)
        
        Returns:
            List of TextDetection objects with text and coordinates
        """
        if not self.reader:
            logger.warning("OCR reader not initialized")
            return []
        
        try:
            # Run OCR
            results = self.reader.readtext(image)
            
            detections = []
            for (bbox, text, confidence) in results:
                # bbox is [[x1,y1], [x2,y1], [x2,y2], [x1,y2]]
                # Convert to x, y, width, height
                x1, y1 = int(bbox[0][0]), int(bbox[0][1])
                x2, y2 = int(bbox[2][0]), int(bbox[2][1])
                
                width = x2 - x1
                height = y2 - y1
                center_x = x1 + width // 2
                center_y = y1 + height // 2
                
                detection = TextDetection(
                    text=text,
                    confidence=confidence,
                    x=x1,
                    y=y1,
                    width=width,
                    height=height,
                    center_x=center_x,
                    center_y=center_y
                )
                detections.append(detection)
            
            logger.info(f"Detected {len(detections)} text elements")
            return detections
            
        except Exception as e:
            logger.error(f"OCR detection failed: {e}")
            return []
    
    def find_text(self, image, search_text: str) -> Optional[TextDetection]:
        """
        Find specific text in image.
        
        Args:
            image: Image to search
            search_text: Text to search for (case-insensitive)
        
        Returns:
            TextDetection if found, None otherwise
        """
        detections = self.detect_text(image)
        search_lower = search_text.lower()
        
        for detection in detections:
            if search_lower in detection.text.lower():
                logger.info(f"Found '{search_text}' at ({detection.center_x}, {detection.center_y})")
                return detection
        
        logger.debug(f"Text '{search_text}' not found")
        return None
    
    def find_text_partial(self, image, search_text: str) -> List[TextDetection]:
        """
        Find all occurrences of partial text in image.
        
        Args:
            image: Image to search
            search_text: Partial text to search for
        
        Returns:
            List of matching TextDetection objects
        """
        detections = self.detect_text(image)
        search_lower = search_text.lower()
        
        matches = []
        for detection in detections:
            if search_lower in detection.text.lower():
                matches.append(detection)
        
        logger.info(f"Found {len(matches)} matches for '{search_text}'")
        return matches


class ScreenOCR:
    """
    Convenience class for screen OCR operations.
    Combines pyautogui screenshot capture with OCR.
    """
    
    def __init__(self, languages: List[str] = ['en'], gpu: bool = False):
        """Initialize screen OCR service."""
        self.ocr = OCRService(languages, gpu)
        
        try:
            import pyautogui
            self.pyautogui = pyautogui
        except ImportError:
            logger.error("pyautogui not installed")
            self.pyautogui = None
    
    def capture_and_detect(self) -> List[TextDetection]:
        """
        Capture screenshot and detect all text.
        
        Returns:
            List of TextDetection objects
        """
        if not self.pyautogui:
            return []
        
        try:
            # Capture screenshot
            screenshot = self.pyautogui.screenshot()
            screenshot_np = np.array(screenshot)
            
            # Detect text
            return self.ocr.detect_text(screenshot_np)
            
        except Exception as e:
            logger.error(f"Screen capture and OCR failed: {e}")
            return []
    
    def find_on_screen(self, search_text: str) -> Optional[TextDetection]:
        """
        Find text on screen and return coordinates.
        
        Args:
            search_text: Text to search for
        
        Returns:
            TextDetection with coordinates if found
        """
        if not self.pyautogui:
            return None
        
        try:
            # Capture screenshot
            screenshot = self.pyautogui.screenshot()
            screenshot_np = np.array(screenshot)
            
            # Find text
            return self.ocr.find_text(screenshot_np, search_text)
            
        except Exception as e:
            logger.error(f"Screen text search failed: {e}")
            return None
    
    def click_text(self, search_text: str, click_type: str = 'click') -> bool:
        """
        Find text on screen and click on it.
        
        Args:
            search_text: Text to find and click
            click_type: 'click', 'double_click', or 'right_click'
        
        Returns:
            True if clicked successfully
        """
        detection = self.find_on_screen(search_text)
        
        if detection:
            try:
                if click_type == 'click':
                    self.pyautogui.click(detection.center_x, detection.center_y)
                elif click_type == 'double_click':
                    self.pyautogui.doubleClick(detection.center_x, detection.center_y)
                elif click_type == 'right_click':
                    self.pyautogui.rightClick(detection.center_x, detection.center_y)
                
                logger.info(f"Clicked on '{search_text}' at ({detection.center_x}, {detection.center_y})")
                return True
                
            except Exception as e:
                logger.error(f"Click failed: {e}")
                return False
        
        logger.warning(f"Text '{search_text}' not found on screen")
        return False
