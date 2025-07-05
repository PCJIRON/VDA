import os
import time
import json
import pyautogui
from difflib import get_close_matches
from google import genai
from google.genai import types

# ------------------ CONFIG ------------------

API_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyBogKf9ab6ES5BQQVkKmaSajnqOh0WaNyg"
client = genai.Client(api_key=API_KEY)

# Known image database (all .png files you have for matching)
KNOWN_IMAGES = {
    "chrome": ["chrome.png"],
    "vscode": ["vscode.png"],
    "notepad": ["notepad.png"],
    # Add more groups if needed
}

# ------------------ Gemini Prompt Handler ------------------

def get_image_key_from_command(command: str) -> str:
    """
    Use Gemini to parse the command and extract the image keyword (not filename).
    Example: "Click on chrome" → "chrome"
    """
    prompt = f"""
You are a smart assistant. Given a user's screen control command, extract only the image keyword (like chrome, vscode, notepad).

Respond with this format:
{{ "image": "<keyword or null>" }}

Command: "{command}"
"""

    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=[prompt],
        config=types.GenerateContentConfig(response_mime_type="application/json")
    )

    try:
        parsed = json.loads(response.text.strip())
        return parsed.get("image")
    except Exception as e:
        print("❌ Could not parse Gemini response:", e)
        print("Raw response:", response.text)
        return None

# ------------------ Smart Finder & Clicker ------------------

def find_and_click_best_image(image_keyword, confidence=0.8):
    """
    Try to locate any of the known images matching the keyword.
    Uses fuzzy matching to improve fault tolerance.
    """
    if not image_keyword:
        print("⚠️ No image keyword provided.")
        return False

    # Fuzzy match to known keys
    possible_keys = list(KNOWN_IMAGES.keys())
    matched_key = get_close_matches(image_keyword.lower(), possible_keys, n=1, cutoff=0.6)

    if not matched_key:
        print(f"❌ Unknown or misspelled image name: '{image_keyword}'")
        return False

    matched_key = matched_key[0]
    image_list = KNOWN_IMAGES[matched_key]

    # Try locating each image in the list
    for image_file in image_list:
        try:
            time.sleep(1)
            location = pyautogui.locateOnScreen(image_file, confidence=confidence)
            if location:
                center_point = pyautogui.center(location)
                pyautogui.moveTo(center_point)
                pyautogui.click()
                print(f"✅ Clicked on '{image_file}' at {center_point}")
                return True
        except Exception as e:
            print(f"⚠️ Error locating '{image_file}': {e}")
            continue

    print(f"❌ None of the images for '{matched_key}' were found on screen.")
    return False

# ------------------ Main Program ------------------

if __name__ == "__main__":
    user_command = input("🗣️ Say something to the assistant: ").strip()
    image_key = get_image_key_from_command(user_command)

    if image_key and image_key.lower() != "null":
        if not find_and_click_best_image(image_key):
            print("🔍 Try using more accurate or visible image files on the screen.")
    else:
        print("❌ Gemini could not understand which image to act on.")
