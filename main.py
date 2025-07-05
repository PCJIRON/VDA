from google import genai
import pyautogui as auto
from PIL import Image
import io
import re

# ✅ Use your valid Gemini API key
client = genai.Client(api_key="AIzaSyBogKf9ab6ES5BQQVkKmaSajnqOh0WaNyg")

def capture_screen():
    """Capture full screen and return image bytes + size."""
    screenshot = auto.screenshot()
    img_byte_arr = io.BytesIO()
    screenshot.save(img_byte_arr, format="PNG")
    img_byte_arr.seek(0)
    return img_byte_arr.read(), screenshot.size  # (width, height)

def extract_bbox(text):
    """Extract bounding box from Gemini response: [y_min, x_min, y_max, x_max]"""
    match = re.search(r"\[\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\]", text)
    if match:
        return list(map(int, match.groups()))
    return None

while True:
    user_input = input("\nEnter your command (or 'exit'): ")
    if user_input.strip().lower() == "exit":
        break

    # 1. Capture screen
    image_bytes, (W, H) = capture_screen()

    # 2. Gemini Prompt
    prompt = f"""
Instruction: "{user_input}"

You are given a screenshot. Return the bounding box of the requested UI object as:
[y_min, x_min, y_max, x_max]

Use **normalized coordinates** between 0 and 1000.
Do not explain.
"""

    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=[{
            "role": "user",
            "parts": [
                {
                    "inline_data": {
                        "mime_type": "image/png",
                        "data": image_bytes
                    }
                },
                {"text": prompt}
            ]
        }]
    )

    print("\n🔵 Gemini raw response:\n", response.text.strip())

    # 3. Parse bounding box
    bbox = extract_bbox(response.text)
    if not bbox:
        print("❌ Could not extract bounding box.")
        continue

    y_min, x_min, y_max, x_max = bbox

    # 4. Convert normalized (0–1000) bbox to pixel coordinates
    top = (y_min / 1000) * H
    left = (x_min / 1000) * W
    bottom = (y_max / 1000) * H
    right = (x_max / 1000) * W

    # 5. Calculate center of bounding box
    center_x = int((left + right) / 2)
    center_y = int((top + bottom) / 2)

    print(f"✅ Moving to bounding box center at ({center_x}, {center_y})")
    auto.moveTo(center_x, center_y, duration=0.4)
    auto.click()
