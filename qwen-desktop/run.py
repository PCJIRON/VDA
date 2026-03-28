"""
Qwen Desktop Application Runner.

Run with: py run.py
"""

import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from qwen_desktop.app import QwenDesktopApp


def main():
    """Run the application."""
    app = QwenDesktopApp(sys.argv)
    sys.exit(app.run())


if __name__ == "__main__":
    main()
