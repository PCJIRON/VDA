"""
Main window for Qwen Desktop application.

This is the primary application window containing all UI components.
Matches qwen-code's AppContainer layout: Header → Chat → Composer → Footer.
"""

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QToolBar,
    QStatusBar,
    QMenu,
    QMenuBar,
    QLabel,
    QPushButton,
)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QAction, QFont
from pathlib import Path

from qwen_desktop.config.settings import Settings
from qwen_desktop.ui.chat_widget import ChatWidget
from qwen_desktop.ui.input_area import InputArea
from qwen_desktop.ui.auth_dialog import AuthDialog
from qwen_desktop.ui.settings_dialog import SettingsDialog
from qwen_desktop.ui.theme_manager import ThemeManager
from qwen_desktop.ui.components.header_widget import HeaderWidget
from qwen_desktop.ui.components.footer_widget import FooterWidget
from qwen_desktop.utils.platform import is_macos
from qwen_desktop.core.conversation_manager import ConversationManager
from qwen_desktop.core.command_registry import CommandRegistry
from qwen_desktop.ui.components.conversation_sidebar import ConversationSidebar


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self, settings: Settings, parent: None = None) -> None:
        """Initialize the main window.

        Args:
            settings: Application settings.
            parent: Parent widget.
        """
        super().__init__(parent)

        self.settings = settings

        # Store auth state
        self.is_authenticated = False
        self.user_info: dict | None = None

        # Theme manager
        self.theme_manager = ThemeManager.instance()
        theme_name = self.settings.get("theme", "qwen-dark")
        if theme_name in ("dark", "Dark"):
            theme_name = "qwen-dark"
        self.theme_manager.set_theme(theme_name)

        # Conversation manager
        self.conversation_manager = ConversationManager()
        self.current_conversation = None

        # Command registry
        self.command_registry = CommandRegistry()

        # OAuth handler - initialize once and reuse
        from qwen_desktop.auth.oauth_handler import OAuthHandler
        self.oauth_handler = OAuthHandler()

        # Setup UI
        self._setup_ui()
        self._setup_menu_bar()
        self._setup_sidebar()
        self._apply_theme()

        # Check if already authenticated from previous session
        self._check_existing_authentication()

        # Apply window size from settings
        self.resize(
            self.settings.get("window_width", 1200),
            self.settings.get("window_height", 800),
        )

        self.setWindowTitle("Qwen Desktop")

    def _setup_ui(self) -> None:
        """Set up the main UI components."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header widget (matches qwen-code Header.tsx)
        self.header_widget = HeaderWidget()
        main_layout.addWidget(self.header_widget)

        # Chat widget
        self.chat_widget = ChatWidget()
        main_layout.addWidget(self.chat_widget, 1)

        # Input area
        self.input_area = InputArea(self.settings)
        main_layout.addWidget(self.input_area)

        # Footer widget (matches qwen-code Footer.tsx)
        self.footer_widget = FooterWidget()
        main_layout.addWidget(self.footer_widget)

        # Connect signals
        self.input_area.message_sent.connect(self._on_message_sent)
        self.input_area.attachments_changed.connect(self._on_attachments_changed)

    def _setup_menu_bar(self) -> None:
        """Set up the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        new_chat_action = QAction("&New Chat", self)
        new_chat_action.setShortcut("Ctrl+N")
        new_chat_action.triggered.connect(self._on_new_chat)
        file_menu.addAction(new_chat_action)

        # Open conversation
        open_action = QAction("&Open Conversation...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._on_open_conversation)
        file_menu.addAction(open_action)

        # Save conversation
        save_action = QAction("&Save Conversation", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._on_save_conversation)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")

        clear_action = QAction("&Clear Conversation", self)
        clear_action.setShortcut("Ctrl+Shift+C")
        clear_action.triggered.connect(self._on_clear_conversation)
        edit_menu.addAction(clear_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        # Theme submenu
        theme_menu = view_menu.addMenu("&Theme")
        for theme_id, theme_name in self.theme_manager.get_theme_display_names().items():
            theme_action = QAction(theme_name, self)
            theme_action.setData(theme_id)
            theme_action.triggered.connect(lambda checked, tid=theme_id: self._on_theme_change(tid))
            theme_menu.addAction(theme_action)

        # Account menu
        account_menu = menubar.addMenu("&Account")

        self.login_action = QAction("&Login", self)
        self.login_action.triggered.connect(self._on_login)
        account_menu.addAction(self.login_action)

        self.logout_action = QAction("&Logout", self)
        self.logout_action.triggered.connect(self._on_logout)
        self.logout_action.setEnabled(False)
        account_menu.addAction(self.logout_action)

        account_menu.addSeparator()

        account_info_action = QAction("Account &Info", self)
        account_info_action.triggered.connect(self._show_account_info)
        account_menu.addAction(account_info_action)

        # Settings menu
        settings_menu = menubar.addMenu("&Settings")

        settings_action = QAction("&Preferences", self)
        # Use Cmd+, on macOS, Ctrl+, on other platforms
        shortcut = "Meta+," if is_macos() else "Ctrl+,"
        settings_action.setShortcut(shortcut)
        settings_action.triggered.connect(self._on_preferences)
        settings_menu.addAction(settings_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

    def _setup_sidebar(self) -> None:
        """Set up the conversation sidebar."""
        self.sidebar = ConversationSidebar(self)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.sidebar)

        # Connect sidebar signals
        self.sidebar.conversation_selected.connect(self._on_conversation_selected)
        self.sidebar.new_conversation.connect(self._on_new_chat)
        self.sidebar.delete_conversation.connect(self._on_conversation_deleted)

    def _apply_theme(self) -> None:
        """Apply the current theme to the entire window."""
        stylesheet = self.theme_manager.get_stylesheet()
        self.setStyleSheet(stylesheet)

    def _on_theme_change(self, theme_id: str) -> None:
        """Handle theme change.

        Args:
            theme_id: ID of the theme to switch to.
        """
        if self.theme_manager.set_theme(theme_id):
            self._apply_theme()
            self.settings.set("theme", theme_id)
            self.settings.save()

            # Notify user
            theme_name = self.theme_manager.active_theme.name
            self.chat_widget.add_message(
                f"Theme changed to {theme_name}", is_system=True
            )

    def _check_existing_authentication(self) -> None:
        """Check if user is already authenticated from previous session."""
        import logging
        logger = logging.getLogger(__name__)

        logger.info("Checking for existing OAuth session...")

        if self.oauth_handler.is_authenticated():
            token = self.oauth_handler.token_manager.get_access_token()
            logger.info(f"Existing session found! Token: {token is not None}")
            if token:
                logger.info(f"Token (first 20): {token[:20]}...")
                # Update UI to show logged in state
                self.is_authenticated = True
                self.login_action.setEnabled(False)
                self.logout_action.setEnabled(True)
                self.header_widget.set_auth_type("Qwen OAuth")
                self.footer_widget.set_hint("? for shortcuts")
                logger.info("UI updated for logged in state")
            else:
                logger.warning("OAuth says authenticated but no token found!")
        else:
            logger.info("No existing session found. User needs to login.")
            self.header_widget.set_auth_type("Not logged in")

    def _on_message_sent(self, message: str) -> None:
        """Handle message sent event.

        Args:
            message: The message text.
        """
        import logging
        logger = logging.getLogger(__name__)

        # Check for slash commands
        if message.startswith("/"):
            cmd, args = self.command_registry.parse_command(message)
            if cmd:
                self._handle_slash_command(cmd.name, args)
                return

        logger.info(f"=== MESSAGE SENT ===")
        logger.info(f"Message: {message[:50]}...")

        # Add user message to chat
        self.chat_widget.add_message(message, is_user=True)
        self.chat_widget.set_typing_indicator(True)

        # Send to API - reuse existing OAuth handler
        from qwen_desktop.core.api_client import APIClient

        logger.info("Checking OAuth authentication...")
        is_auth = self.oauth_handler.is_authenticated()
        logger.info(f"OAuth authenticated: {is_auth}")

        if is_auth:
            token = self.oauth_handler.token_manager.get_access_token()
            logger.info(f"Token available: {token is not None}")
            if token:
                logger.info(f"Token (first 20 chars): {token[:20]}...")
        else:
            logger.warning("OAuth not authenticated!")

        # Create API client if not exists
        if not hasattr(self, 'api_client'):
            logger.info("Creating new APIClient...")
            self.api_client = APIClient(self.settings, self.oauth_handler)
            logger.info("APIClient created")

        # Get conversation history
        history = []
        if self.current_conversation:
            history = self.current_conversation.get_messages_for_api()
            logger.info(f"Conversation history: {len(history)} messages")

        # Use QTimer to integrate async with Qt event loop
        logger.info("Scheduling API call via QTimer...")
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, lambda: self._schedule_api_call(message, history))

        self.footer_widget.set_hint("Sending message...")

    def _handle_slash_command(self, name: str, args: str) -> None:
        """Handle a slash command.

        Args:
            name: Command name.
            args: Command arguments.
        """
        if name == "help":
            help_text = self.command_registry.get_help_text()
            self.chat_widget.add_message(help_text, is_system=True)

        elif name == "clear":
            self.chat_widget.clear()
            self.chat_widget.add_message("Conversation cleared.", is_system=True)

        elif name == "new":
            self._on_new_chat()

        elif name == "model":
            if args.strip():
                model = args.strip()
                self.settings.set("api_model", model)
                self.header_widget.set_model(model)
                self.chat_widget.add_message(f"Model changed to {model}", is_system=True)
            else:
                current = self.settings.get("api_model", "qwen-coder-plus")
                models = ["qwen-coder-plus", "qwen-plus", "qwen-max", "qwen-turbo"]
                lines = [f"Current model: {current}", "", "Available models:"]
                for m in models:
                    marker = " ← current" if m == current else ""
                    lines.append(f"  {m}{marker}")
                lines.append("\nUsage: /model <model-name>")
                self.chat_widget.add_message("\n".join(lines), is_system=True)

        elif name == "theme":
            if args.strip():
                tid = args.strip().lower().replace(" ", "-")
                if self.theme_manager.set_theme(tid):
                    self._apply_theme()
                    self.settings.set("theme", tid)
                    self.settings.save()
                    self.chat_widget.add_message(
                        f"Theme changed to {self.theme_manager.active_theme.name}",
                        is_system=True,
                    )
                else:
                    avail = ", ".join(self.theme_manager.available_themes)
                    self.chat_widget.add_message(
                        f"Unknown theme '{args.strip()}'. Available: {avail}",
                        is_system=True,
                    )
            else:
                current = self.theme_manager.active_theme.name
                themes = self.theme_manager.get_theme_display_names()
                lines = [f"Current theme: {current}", "", "Available themes:"]
                for tid, name in themes.items():
                    marker = " ← current" if name == current else ""
                    lines.append(f"  {tid}: {name}{marker}")
                lines.append("\nUsage: /theme <theme-name>")
                self.chat_widget.add_message("\n".join(lines), is_system=True)

        elif name == "stats":
            lines = ["Session Statistics:", ""]
            if hasattr(self, 'api_client') and self.api_client:
                usage = self.api_client.rate_limiter.get_usage()
                lines.append(f"  API requests: {usage['requests_made']}/{usage['max_requests']}")
                lines.append(f"  Remaining: {usage['tokens_remaining']}")
            lines.append(f"  Model: {self.settings.get('api_model', 'qwen-coder-plus')}")
            lines.append(f"  Theme: {self.theme_manager.active_theme.name}")
            lines.append(f"  Auth: {'Logged in' if self.is_authenticated else 'Not logged in'}")
            self.chat_widget.add_message("\n".join(lines), is_system=True)

        elif name == "settings":
            self._on_preferences()

        elif name == "save":
            self._on_save_conversation()

        elif name == "compact":
            self.chat_widget.add_message(
                "Conversation compression not yet implemented.", is_system=True
            )

        elif name == "quit":
            self.close()

    def _schedule_api_call(self, message: str, history: list) -> None:
        """Schedule API call in Qt event loop."""
        import asyncio
        import logging
        import nest_asyncio

        logger = logging.getLogger(__name__)

        # Apply nest_asyncio to allow nested event loops
        try:
            nest_asyncio.apply()
        except Exception:
            pass

        logger.info("Creating new event loop for API call...")

        # Create new event loop and run
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            logger.info("Running API call in event loop...")
            loop.run_until_complete(self._send_message_and_stream(message, history))
        except Exception as e:
            logger.error(f"Event loop error: {e}", exc_info=True)
        finally:
            loop.close()
            logger.info("Event loop closed")

    async def _send_message_and_stream(self, message: str, history: list) -> None:
        """Send message to API and stream response.

        Args:
            message: User message.
            history: Conversation history.
        """
        import logging
        logger = logging.getLogger(__name__)

        try:
            logger.info("=== SENDING TO API ===")
            logger.info(f"History messages: {len(history)}")
            logger.info(f"User message: {message[:50]}...")

            full_response = ""
            chunk_count = 0

            logger.info("Starting API call...")
            async for chunk in self.api_client.send_message(message, history):
                chunk_count += 1
                full_response += chunk
                logger.info(f"Received chunk {chunk_count}: {chunk[:50] if chunk else 'empty'}")

                # Update AI message in real-time
                if chunk_count % 5 == 0:  # Update every 5 chunks
                    from PyQt6.QtCore import QTimer
                    QTimer.singleShot(0, lambda r=full_response: self.chat_widget.add_message(r, is_user=False))

            logger.info(f"=== API CALL COMPLETE ===")
            logger.info(f"Total chunks: {chunk_count}")
            logger.info(f"Full response length: {len(full_response)}")

            # Add final response
            from PyQt6.QtCore import QTimer
            if full_response:
                QTimer.singleShot(0, lambda: self.chat_widget.add_message(full_response, is_user=False))
                logger.info("Response added to chat")
            else:
                logger.warning("No response received from API!")
                QTimer.singleShot(0, lambda: self.chat_widget.add_message("No response from API", is_system=True))

            # Save to conversation
            if self.current_conversation:
                self.current_conversation.add_message(message, role="user")
                self.current_conversation.add_message(full_response, role="assistant")
                logger.info("Conversation saved")

            self.chat_widget.set_typing_indicator(False)
            self.footer_widget.set_hint("? for shortcuts")
            logger.info("=== MESSAGE COMPLETE ===")

        except Exception as e:
            logger.error(f"=== API ERROR ===")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error message: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

            self.chat_widget.set_typing_indicator(False)
            error_message = f"Error: {e}"
            self.footer_widget.set_hint("Error occurred")
            # Show error in chat
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, lambda msg=error_message: self.chat_widget.add_message(msg, is_system=True))

    def _on_attachments_changed(self, attachments: list) -> None:
        """Handle attachments changed event.

        Args:
            attachments: List of attached files.
        """
        count = len(attachments)
        if count > 0:
            self.footer_widget.set_hint(f"{count} file(s) attached")

    def _on_new_chat(self) -> None:
        """Handle new chat action."""
        # Save current conversation before starting new one
        if self.current_conversation and self.current_conversation.messages:
            self._on_save_conversation()

        self.chat_widget.clear()
        self.current_conversation = None
        self.footer_widget.set_hint("New chat started")

    def _on_open_conversation(self) -> None:
        """Handle open conversation action."""
        from PyQt6.QtWidgets import QFileDialog

        # Show file dialog
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Open Conversation",
            str(self.conversation_manager.storage_path),
            "JSON Files (*.json)",
        )

        if filepath:
            conv = self.conversation_manager.load_conversation(Path(filepath))
            if conv:
                self.current_conversation = conv
                self.chat_widget.clear()

                # Load messages with attachments
                for msg in conv.messages:
                    is_user = msg.role == "user"
                    self.chat_widget.add_message(msg.content, is_user=is_user)

                self.footer_widget.set_hint(f"Loaded: {conv.title}")

    def _on_save_conversation(self) -> None:
        """Handle save conversation action."""
        from qwen_desktop.core.conversation import Conversation
        from qwen_desktop.ui.message_bubble import MessageBubble

        # Create or update conversation
        if not self.current_conversation:
            self.current_conversation = Conversation()

        # Extract messages from chat widget
        # Clear existing messages to avoid duplicates
        self.current_conversation.messages.clear()

        for i in range(self.chat_widget.messages_layout.count() - 1):  # Exclude stretch
            item = self.chat_widget.messages_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, MessageBubble):
                    role = "user" if widget.is_user else "assistant"
                    self.current_conversation.add_message(widget.text, role=role)

        # Save conversation
        if self.current_conversation.messages:
            filepath = self.conversation_manager.save_conversation(self.current_conversation)
            self.footer_widget.set_hint(f"Saved: {filepath.name}")
        else:
            self.footer_widget.set_hint("No messages to save")

    def _on_clear_conversation(self) -> None:
        """Handle clear conversation action."""
        self.chat_widget.clear()
        self.footer_widget.set_hint("Conversation cleared")

    def _on_conversation_selected(self, filepath: str) -> None:
        """Handle conversation selection from sidebar.

        Args:
            filepath: Path to conversation file.
        """
        from pathlib import Path

        conv = self.conversation_manager.load_conversation(Path(filepath))
        if conv:
            self.current_conversation = conv
            self.chat_widget.clear()

            # Load messages
            for msg in conv.messages:
                is_user = msg.role == "user"
                self.chat_widget.add_message(msg.content, is_user=is_user)

            self.footer_widget.set_hint(f"Loaded: {conv.title}")

    def _on_conversation_deleted(self, filepath: str) -> None:
        """Handle conversation deletion.

        Args:
            filepath: Path to conversation file.
        """
        from pathlib import Path

        if self.conversation_manager.delete_conversation(Path(filepath)):
            self.sidebar.refresh()
            self.footer_widget.set_hint("Conversation deleted")

    def _on_login(self) -> None:
        """Handle login action - direct device code flow."""
        from qwen_desktop.auth.qwen_auth_gui import QwenAuthDialog

        # Show auth widget directly in main window
        auth_widget = QwenAuthDialog(self)
        auth_widget.auth_success.connect(self._on_login_success)
        auth_widget.auth_failed.connect(self._on_login_failed)

        # Show as modal dialog
        if auth_widget.exec():
            self.is_authenticated = True
            self.login_action.setEnabled(False)
            self.logout_action.setEnabled(True)
            self.header_widget.set_auth_type("Qwen OAuth")
            self.footer_widget.set_hint("Successfully logged in")
            self._update_rate_limit_display()

    def _on_login_success(self, credentials: dict):
        """Handle login success."""
        self.is_authenticated = True
        self.login_action.setEnabled(False)
        self.logout_action.setEnabled(True)
        self.header_widget.set_auth_type("Qwen OAuth")
        self.footer_widget.set_hint("Successfully logged in")
        self._update_rate_limit_display()

    def _on_login_failed(self, error: str):
        """Handle login failure."""
        self.footer_widget.set_hint(f"Login failed: {error}")

    def _update_rate_limit_display(self) -> None:
        """Update rate limit status display."""
        if hasattr(self, 'api_client') and self.api_client:
            usage = self.api_client.rate_limiter.get_usage()
            self.footer_widget.set_rate_limit(
                usage["tokens_remaining"],
                usage["max_requests"],
            )

    def _on_logout(self) -> None:
        """Handle logout action."""
        self.is_authenticated = False
        self.login_action.setEnabled(True)
        self.logout_action.setEnabled(False)
        self.header_widget.set_auth_type("Not logged in")
        self.footer_widget.set_hint("Logged out")

    def _show_account_info(self) -> None:
        """Show account information."""
        self.footer_widget.set_hint("Account info not implemented yet")

    def _on_preferences(self) -> None:
        """Handle preferences action."""
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec():
            self.settings.save()
            self.footer_widget.set_hint("Settings saved")

    def _on_about(self) -> None:
        """Handle about action."""
        from PyQt6.QtWidgets import QMessageBox

        tm = self.theme_manager
        c = tm.colors

        QMessageBox.about(
            self,
            "About Qwen Desktop",
            f"<h2 style='color: {c.AccentYellow}'>Qwen Desktop</h2>"
            "<p>Version 0.5.0</p>"
            "<p>A PyQt GUI application for Qwen AI assistant.</p>"
            "<p>Built with Python and PyQt6.</p>"
            f"<p>Based on <a href='https://github.com/QwenLM/qwen-code' "
            f"style='color: {c.AccentBlue}'>qwen-code</a> CLI.</p>"
        )
