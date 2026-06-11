"""
Quick Test - Perfect Clicker with Fixes

Test karo aur dekho ki click accurate jagah pe ho raha hai ya nahi
"""

from vda.core.perfect_clicker import PerfectClicker
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG, format='%(message)s')

# Initialize
clicker = PerfectClicker(
    api_url="https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
    api_key="YOUR_API_KEY_HERE",  # ← APNA API KEY DAALO
    model="vda-vl-plus"
)

print("\n" + "="*60)
print("PERFECT CLICKER - TEST")
print("="*60)
print("\nCalibration:")
print(f"  ratio_x: {clicker.calibrator.calibration['ratio_x']:.6f}")
print(f"  ratio_y: {clicker.calibrator.calibration['ratio_y']:.6f}")
print(f"  pyautogui: {clicker.calibrator.calibration['pyautogui_w']}×{clicker.calibrator.calibration['pyautogui_h']}")
print(f"  screenshot: {clicker.calibrator.calibration['screenshot_w']}×{clicker.calibrator.calibration['screenshot_h']}")

print("\n" + "="*60)
print("TEST 1: Click 'Submit button' (or any visible button)")
print("="*60)

ok, x, y = clicker.click("Submit button", retries=1, verify=False)

print(f"\nResult: {'✅ SUCCESS' if ok else '❌ FAILED'}")
print(f"Clicked at: ({x}, {y})")
print(f"Current mouse position: {clicker.calibrator.calibration['pyautogui_w']}×{clicker.calibrator.calibration['pyautogui_h']} screen pe")

print("\n" + "="*60)
print("CHECK:")
print("  1. Kya click sahi jagah hua?")
print("  2. Agar nahi, toh debug_click.png check karo")
print("  3. Logs mein coordinates dekho")
print("="*60 + "\n")
