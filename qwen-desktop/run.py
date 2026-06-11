"""
AI Desktop Assistant Runner.

Run with: py run.py
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from qwen_desktop.app import DesktopApp


def main():
    app = DesktopApp(sys.argv)
    sys.exit(app.run())


if __name__ == "__main__":
    main()
