"""
Qwen Desktop Application.

Main application class that initializes and runs the PyQt application.
"""

import sys
import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QCoreApplication

from qwen_desktop.ui.main_window import MainWindow
from qwen_desktop.config.settings import Settings
from qwen_desktop.utils.logger import setup_logger


class QwenDesktopApp:
    """Main application class for Qwen Desktop."""

    def __init__(self, argv: list[str]) -> None:
        """Initialize the application.
        
        Args:
            argv: Command line arguments.
        """
        # Set application attributes
        QCoreApplication.setApplicationName("Qwen Desktop")
        QCoreApplication.setApplicationVersion("0.4.0")
        QCoreApplication.setOrganizationName("Qwen")
        
        # Create Qt application
        self.app = QApplication(argv)
        
        # Setup logging with file output
        log_path = Path.home() / ".qwen-desktop" / "qwen-desktop.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = setup_logger(log_file=log_path)
        self.logger.info("=" * 60)
        self.logger.info("Qwen Desktop Application Starting...")
        self.logger.info(f"Version: 0.4.0")
        self.logger.info(f"Log file: {log_path}")
        
        # Load settings
        self.settings = Settings()
        
        # Create main window
        self.main_window: Optional[MainWindow] = None
        
        self.logger.info("Application initialized")

    def run(self) -> int:
        """Run the application.
        
        Returns:
            Exit code.
        """
        try:
            # Show main window
            self.main_window = MainWindow(self.settings)
            self.main_window.show()
            
            self.logger.info("Application started - main window visible")
            
            # Run event loop
            return self.app.exec()
            
        except Exception as e:
            self.logger.error(f"Application error: {e}", exc_info=True)
            return 1
