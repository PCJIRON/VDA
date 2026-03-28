"""
Qwen Desktop Application Entry Point.

Run with: py -m qwen_desktop
Or: py run.py
"""

import sys
from qwen_desktop.app import QwenDesktopApp


def main():
    """Main entry point for the application."""
    app = QwenDesktopApp(sys.argv)
    sys.exit(app.run())


if __name__ == "__main__":
    main()
