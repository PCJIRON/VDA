# VDA — Voice-Driven Desktop Agent

VDA is a powerful, local, AI-driven desktop assistant designed to control computers like a human. It sees your screen, clicks, types, and can be instructed via voice or text. Built with Python and PyQt6, VDA features a floating assistant window, advanced vision-based UI element detection (including fallback to OCR and SIFT), and integration with multiple AI providers (OpenCode Zen, OpenRouter, Gemini, DeepSeek).

## Features
- **Vision-Based UI Control**: Uses OpenCV template matching, Windows UI Automation, and RapidOCR for pixel-perfect interactions.
- **Smart Decision Engine**: Uses an LLM agent loop that re-plans every step based on the live screenshot to avoid getting stuck or lost.
- **Customizable Skills**: Upload a `.md` file to teach VDA specific workflows or UI rules.
- **Strict Coordinate Fallback**: Prioritizes robust keyboard shortcuts (e.g., `Ctrl+L`, `Tab`, `Enter`) over fragile mouse coordinates if UI templates fail.
- **Floating UI**: PyQt6 based translucent floating widget that stays out of your way.

## Installation

### Requirements
- **OS**: Windows is highly recommended for full feature set (especially Windows UI Automation).
- **Python**: Version 3.9 or higher.

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/PCJIRON/VDA.git
   cd VDA
   ```

2. Install the required dependencies:
   ```bash
   cd qwen-desktop
   pip install -r requirements.txt
   ```
   > Note: VDA relies on several native modules like `pyautogui`, `opencv-python`, and `rapidocr-onnxruntime`.

3. Start the application:
   ```bash
   python run.py
   ```

## Configuration

Settings are stored in a local `.json` file. You can configure:
- Your preferred AI model and provider.
- API Base URLs.
- Path to your custom `desktop_skill.md` for specific instructions.

## License
This project is licensed under the **GNU General Public License v3.0**. See the [LICENSE](LICENSE) file for details.
