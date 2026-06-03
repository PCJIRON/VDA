import sys
import logging
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QCoreApplication

from qwen_desktop.config.settings import Settings
from qwen_desktop.utils.logger import setup_logger


class DesktopApp:
    def __init__(self, argv: list[str]) -> None:
        QCoreApplication.setApplicationName("AI Desktop Assistant")
        QCoreApplication.setApplicationVersion("0.5.0")
        QCoreApplication.setOrganizationName("AIDesktop")

        self.app = QApplication(argv)

        log_path = Path.home() / ".qwen-desktop" / "app.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = setup_logger(log_file=log_path)
        self.logger.info("=" * 60)
        self.logger.info("AI Desktop Assistant Starting...")
        self.logger.info(f"Version: 0.5.0")
        self.logger.info(f"Log file: {log_path}")

        self.settings = Settings()

        self.floating_assistant = None

        self.logger.info("Application initialized")

    def run(self) -> int:
        try:
            from qwen_desktop.ui.floating_assistant import FloatingAssistant

            self.floating_assistant = FloatingAssistant(self.settings)
            self.floating_assistant.show()

            self.logger.info("Application started - floating assistant visible")

            return self.app.exec()

        except Exception as e:
            self.logger.error(f"Application error: {e}", exc_info=True)
            return 1
