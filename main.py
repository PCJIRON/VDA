import pyautogui
import time

def find_and_click_image(image_path, confidence=0.8, offset_x=0, offset_y=0):
    """
    Locate an image on the screen and click at an offset position relative to its center.
    
    Args:
        image_path (str): Path to the image file to locate.
        confidence (float): Matching confidence between 0 and 1 (requires OpenCV).
        offset_x (int): Horizontal offset from the center of the found image.
        offset_y (int): Vertical offset from the center of the found image.
        
    Returns:
        bool: True if image was found and clicked, False otherwise.
    """
    try:
        # Pause briefly to allow user to prepare screen if needed
        time.sleep(1)
        
        # Locate the image on the screen with confidence threshold
        location = pyautogui.locateOnScreen(image_path, confidence=confidence)
        
        if location is not None:
            # Get the center coordinates of the located image
            center_point = pyautogui.center(location)
            
            # Calculate the target coordinates with offset
            target_x = center_point.x + offset_x
            target_y = center_point.y + offset_y
            
            # Move the mouse to the target coordinates and click
            pyautogui.moveTo(target_x, target_y)
            pyautogui.click()
            
            print(f"Clicked on image at ({target_x}, {target_y})")
            return True
        else:
            print("Image not found on the screen.")
            return False
            
    except pyautogui.ImageNotFoundException:
        print("ImageNotFoundException: Could not locate the image on the screen.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

if __name__ == "__main__":
    # Replace 'chrome.png' with your image filename or full path
    image_file = "33.png"
    
    # Example: move 10 pixels right and 5 pixels down from the center of the found image
    success = find_and_click_image(image_file, confidence=0.8, offset_x=10, offset_y=5)
    
    if not success:
        print("Please check if the image exists, matches the screen exactly, and your screen scaling is 100%.")
