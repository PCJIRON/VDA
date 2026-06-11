"""
VDA Desktop Application Entry Point.

Run with: py -m vda
Or: py run.py
"""

import sys
from vda.app import DesktopApp


def main():
    """Main entry point for the application."""
    app = DesktopApp(sys.argv)
    sys.exit(app.run())


if __name__ == "__main__":
    main()
