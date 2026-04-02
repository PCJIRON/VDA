"""
Modern Settings Dialog for Qwen Desktop.

Sidebar navigation with pages:
- Account (Login/Logout)
- MCP Servers
- Extensions/Plugins
- Agents
- Skills
- Terminal
- General Settings
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QPushButton,
    QStackedWidget, QFrame, QScrollArea, QLineEdit, QComboBox,
    QGroupBox, QTextEdit, QFormLayout, QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPainter
import logging
import json
import os
import subprocess
import platform
import shutil

logger = logging.getLogger(__name__)


class SidebarButton(QPushButton):
    def __init__(self, icon: str, label: str, parent=None):
        super().__init__(parent)
        self.icon_text = icon
        self.label_text = label
        self.setFixedSize(220, 48)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._active = False
        self._update_style()

    def set_active(self, active: bool):
        self._active = active
        self._update_style()

    def _update_style(self):
        if self._active:
            self.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #6366f1, stop:1 #8b5cf6);
                    color: white;
                    border: none;
                    border-radius: 10px;
                    padding: 0px 16px;
                    font-size: 14px;
                    font-weight: 600;
                    text-align: left;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #4f46e5, stop:1 #7c3aed);
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #9ca3af;
                    border: none;
                    border-radius: 10px;
                    padding: 0px 16px;
                    font-size: 14px;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: rgba(99, 102, 241, 0.1);
                    color: white;
                }
            """)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        font = QFont("Segoe UI Emoji", 16)
        painter.setFont(font)
        painter.drawText(12, 32, self.icon_text)
        font2 = QFont("Segoe UI", 14, QFont.Weight.Medium if self._active else QFont.Weight.Normal)
        painter.setFont(font2)
        painter.drawText(44, 31, self.label_text)


class SettingsDialog(QDialog):

    login_requested = pyqtSignal()
    logout_requested = pyqtSignal()

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Qwen Desktop Settings")
        self.setMinimumSize(900, 650)
        self.setModal(True)
        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setFixedWidth(240)
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 20, 12, 12)
        sidebar_layout.setSpacing(4)

        title = QLabel("Settings")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: white; padding: 10px 8px 20px 8px;")
        sidebar_layout.addWidget(title)

        self.nav_buttons = []
        nav_items = [
            ("Account",),
            ("MCP Servers",),
            ("Extensions",),
            ("Agents",),
            ("Skills",),
            ("Terminal",),
            ("General",),
        ]
        icons = ["\U0001F464", "\U0001F517", "\U0001F9E9", "\U0001F916", "\U0001F4DA", "\U0001F4BB", "\u26A1"]

        for (label,), icon in zip(nav_items, icons):
            btn = SidebarButton(icon, label)
            btn.clicked.connect(lambda checked, b=btn: self._on_nav_clicked(b))
            sidebar_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        sidebar_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setFixedHeight(40)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(239, 68, 68, 0.2);
                color: #f87171;
                border: 1px solid rgba(239, 68, 68, 0.3);
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: rgba(239, 68, 68, 0.3);
            }
        """)
        sidebar_layout.addWidget(close_btn)

        content_frame = QFrame()
        content_frame.setObjectName("contentFrame")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)

        self.stacked = QStackedWidget()
        content_layout.addWidget(self.stacked)

        self._create_account_page()
        self._create_mcp_page()
        self._create_extensions_page()
        self._create_agents_page()
        self._create_skills_page()
        self._create_terminal_page()
        self._create_general_page()

        main_layout.addWidget(sidebar)
        main_layout.addWidget(content_frame, 1)

        self._on_nav_clicked(self.nav_buttons[0])

    def _apply_styles(self):
        self.setStyleSheet("""
            SettingsDialog {
                background-color: #111827;
            }
            QFrame#sidebar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1f2937, stop:1 #111827);
                border-right: 1px solid #374151;
            }
            QFrame#contentFrame {
                background-color: #111827;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #1f2937;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #4b5563;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #6b7280;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QGroupBox {
                background-color: #1f2937;
                border: 1px solid #374151;
                border-radius: 12px;
                margin-top: 12px;
                padding-top: 16px;
                font-size: 14px;
                font-weight: 600;
                color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
                color: #a78bfa;
            }
            QLineEdit, QComboBox, QTextEdit {
                background-color: #374151;
                color: white;
                border: 1px solid #4b5563;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus {
                border: 1px solid #6366f1;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #374151;
                color: white;
                selection-background-color: #6366f1;
            }
            QPushButton {
                background-color: #374151;
                color: white;
                border: 1px solid #4b5563;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
            QLabel {
                color: #d1d5db;
                font-size: 13px;
            }
        """)

    def _on_nav_clicked(self, btn):
        for b in self.nav_buttons:
            b.set_active(b is btn)
        idx = self.nav_buttons.index(btn)
        self.stacked.setCurrentIndex(idx)

    def _make_page(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        return w, layout

    def _wrap_in_scroll(self, widget):
        sa = QScrollArea()
        sa.setWidgetResizable(True)
        sa.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        sa.setWidget(widget)
        return sa

    # ─── ACCOUNT PAGE ───────────────────────────────────────────────────────

    def _create_account_page(self):
        page, layout = self._make_page()

        auth_card = QGroupBox("Authentication")
        auth_layout = QVBoxLayout(auth_card)

        self.auth_status_label = QLabel("Status: Checking...")
        self.auth_status_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        auth_layout.addWidget(self.auth_status_label)

        self.auth_email_label = QLabel("")
        self.auth_email_label.setStyleSheet("color: #9ca3af; font-size: 13px;")
        auth_layout.addWidget(self.auth_email_label)

        auth_btn_layout = QHBoxLayout()
        self.login_btn = QPushButton("Login with Qwen")
        self.login_btn.setMinimumHeight(44)
        self.login_btn.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.login_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1, stop:1 #8b5cf6);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4f46e5, stop:1 #7c3aed);
            }
        """)
        self.login_btn.clicked.connect(self._on_login_click)
        auth_btn_layout.addWidget(self.login_btn)

        self.logout_btn = QPushButton("Logout")
        self.logout_btn.setMinimumHeight(44)
        self.logout_btn.setVisible(False)
        self.logout_btn.clicked.connect(self._on_logout_click)
        self.logout_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(239, 68, 68, 0.2);
                color: #f87171;
                border: 1px solid rgba(239, 68, 68, 0.3);
                border-radius: 10px;
                padding: 10px 24px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: rgba(239, 68, 68, 0.3);
            }
        """)
        auth_btn_layout.addWidget(self.logout_btn)
        auth_layout.addLayout(auth_btn_layout)

        layout.addWidget(auth_card)

        info_card = QGroupBox("Account Info")
        info_layout = QFormLayout(info_card)
        info_layout.addRow("Daily Limit:", QLabel("1,000 requests/day (Free tier)"))
        info_layout.addRow("Provider:", QLabel("DashScope (Qwen OAuth)"))
        info_layout.addRow("Scopes:", QLabel("openid profile email model.completion"))
        layout.addWidget(info_card)

        layout.addStretch()
        self.stacked.addWidget(self._wrap_in_scroll(page))

    def _on_login_click(self):
        self.login_requested.emit()

    def _on_logout_click(self):
        self.logout_requested.emit()
        self._update_auth_status(False, None)

    def _update_auth_status(self, authenticated: bool, email: str | None = None):
        if authenticated:
            self.auth_status_label.setText("Authenticated")
            self.auth_status_label.setStyleSheet("color: #34d399;")
            self.auth_email_label.setText(f"Logged in as: {email or 'Unknown'}")
            self.login_btn.setVisible(False)
            self.logout_btn.setVisible(True)
        else:
            self.auth_status_label.setText("Not Logged In")
            self.auth_status_label.setStyleSheet("color: #f87171;")
            self.auth_email_label.setText("Click login to authenticate with Qwen")
            self.login_btn.setVisible(True)
            self.logout_btn.setVisible(False)

    # ─── MCP SERVERS PAGE ───────────────────────────────────────────────────

    def _create_mcp_page(self):
        page, layout = self._make_page()

        info = QLabel("MCP (Model Context Protocol) servers extend Qwen with external tools and data sources.")
        info.setWordWrap(True)
        info.setStyleSheet("color: #9ca3af; font-size: 13px; margin-bottom: 8px;")
        layout.addWidget(info)

        add_group = QGroupBox("Add MCP Server")
        add_layout = QFormLayout(add_group)

        self.mcp_name_input = QLineEdit()
        self.mcp_name_input.setPlaceholderText("e.g. filesystem, github, slack")
        add_layout.addRow("Name:", self.mcp_name_input)

        self.mcp_type_combo = QComboBox()
        self.mcp_type_combo.addItems(["stdio", "sse", "http"])
        add_layout.addRow("Transport:", self.mcp_type_combo)

        self.mcp_command_input = QLineEdit()
        self.mcp_command_input.setPlaceholderText("e.g. npx, node, python")
        add_layout.addRow("Command:", self.mcp_command_input)

        self.mcp_args_input = QLineEdit()
        self.mcp_args_input.setPlaceholderText("e.g. -y @modelcontextprotocol/server-filesystem /path")
        add_layout.addRow("Arguments:", self.mcp_args_input)

        self.mcp_url_input = QLineEdit()
        self.mcp_url_input.setPlaceholderText("URL for SSE/HTTP transport")
        add_layout.addRow("URL:", self.mcp_url_input)

        add_btn_layout = QHBoxLayout()
        add_mcp_btn = QPushButton("Add Server")
        add_mcp_btn.clicked.connect(self._add_mcp_server)
        add_btn_layout.addWidget(add_mcp_btn)
        add_btn_layout.addStretch()
        add_layout.addRow("", add_btn_layout)

        layout.addWidget(add_group)

        self.mcp_list_group = QGroupBox("Configured MCP Servers")
        self.mcp_list_layout = QVBoxLayout(self.mcp_list_group)
        self.mcp_list_layout.setSpacing(8)
        self._load_mcp_servers()
        layout.addWidget(self.mcp_list_group)

        layout.addStretch()
        self.stacked.addWidget(self._wrap_in_scroll(page))

    def _mcp_config_path(self) -> str:
        return os.path.join(os.path.expanduser("~"), ".qwen", "settings.json")

    def _load_mcp_servers(self):
        config_path = self._mcp_config_path()
        servers = {}
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    config = json.load(f)
                servers = config.get("mcpServers", {})
            except Exception:
                pass

        for i in reversed(range(self.mcp_list_layout.count())):
            w = self.mcp_list_layout.itemAt(i).widget()
            if w:
                w.deleteLater()

        if not servers:
            no_servers = QLabel("No MCP servers configured. Add one above.")
            no_servers.setStyleSheet("color: #6b7280; padding: 12px;")
            self.mcp_list_layout.addWidget(no_servers)
            return

        for name, cfg in servers.items():
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background-color: #1f2937;
                    border: 1px solid #374151;
                    border-radius: 10px;
                    padding: 12px;
                }
            """)
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(12, 8, 12, 8)

            info_layout = QVBoxLayout()
            transport = "sse" if cfg.get("url") else ("http" if cfg.get("httpUrl") else "stdio")
            cmd = cfg.get("command", "N/A")
            args = " ".join(cfg.get("args", []))
            info_layout.addWidget(QLabel(f"<b style='color:#a78bfa'>{name}</b> <span style='color:#6b7280'>({transport})</span>"))
            if transport == "stdio":
                info_layout.addWidget(QLabel(f"<span style='color:#9ca3af'>{cmd} {args}</span>"))
            else:
                info_layout.addWidget(QLabel(f"<span style='color:#9ca3af'>{cfg.get('url') or cfg.get('httpUrl', 'N/A')}</span>"))

            info_widget = QWidget()
            info_widget.setLayout(info_layout)
            card_layout.addWidget(info_widget, 1)

            remove_btn = QPushButton("Remove")
            remove_btn.setFixedSize(60, 36)
            remove_btn.setToolTip(f"Remove {name}")
            remove_btn.clicked.connect(lambda checked, n=name: self._remove_mcp_server(n))
            card_layout.addWidget(remove_btn)

            self.mcp_list_layout.addWidget(card)

    def _add_mcp_server(self):
        name = self.mcp_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Please enter a server name.")
            return

        transport = self.mcp_type_combo.currentText()
        config_path = self._mcp_config_path()

        servers = {}
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    data = json.load(f)
                servers = data.get("mcpServers", {})
            except Exception:
                pass

        server_cfg = {}
        if transport == "stdio":
            server_cfg["command"] = self.mcp_command_input.text().strip()
            server_cfg["args"] = self.mcp_args_input.text().strip().split() if self.mcp_args_input.text().strip() else []
        else:
            server_cfg["url" if transport == "sse" else "httpUrl"] = self.mcp_url_input.text().strip()

        servers[name] = server_cfg

        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        data = {"mcpServers": servers}
        with open(config_path, "w") as f:
            json.dump(data, f, indent=2)

        self.mcp_name_input.clear()
        self.mcp_command_input.clear()
        self.mcp_args_input.clear()
        self.mcp_url_input.clear()

        self._load_mcp_servers()
        QMessageBox.information(self, "Success", f"MCP server '{name}' added!")

    def _remove_mcp_server(self, name: str):
        config_path = self._mcp_config_path()
        if not os.path.exists(config_path):
            return

        try:
            with open(config_path, "r") as f:
                data = json.load(f)
            servers = data.get("mcpServers", {})
            if name in servers:
                del servers[name]
            with open(config_path, "w") as f:
                json.dump({"mcpServers": servers}, f, indent=2)
            self._load_mcp_servers()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to remove server: {e}")

    # ─── EXTENSIONS PAGE ────────────────────────────────────────────────────

    def _create_extensions_page(self):
        page, layout = self._make_page()

        info = QLabel("Extensions add MCP servers, skills, agents, and hooks to Qwen Desktop.")
        info.setWordWrap(True)
        info.setStyleSheet("color: #9ca3af; font-size: 13px; margin-bottom: 8px;")
        layout.addWidget(info)

        install_group = QGroupBox("Install Extension")
        install_layout = QVBoxLayout(install_group)

        input_row = QHBoxLayout()
        self.ext_source_input = QLineEdit()
        self.ext_source_input.setPlaceholderText("GitHub URL, owner/repo, or local path")
        input_row.addWidget(self.ext_source_input)

        install_btn = QPushButton("Install")
        install_btn.clicked.connect(self._install_extension)
        input_row.addWidget(install_btn)

        install_layout.addLayout(input_row)
        install_layout.addWidget(QLabel("Examples: https://github.com/owner/repo  |  owner/repo  |  /path/to/extension"))

        layout.addWidget(install_group)

        self.ext_list_group = QGroupBox("Installed Extensions")
        self.ext_list_layout = QVBoxLayout(self.ext_list_group)
        self.ext_list_layout.setSpacing(8)
        self._load_extensions()
        layout.addWidget(self.ext_list_group)

        layout.addStretch()
        self.stacked.addWidget(self._wrap_in_scroll(page))

    def _ext_dir(self) -> str:
        return os.path.join(os.path.expanduser("~"), ".qwen", "extensions")

    def _load_extensions(self):
        ext_dir = self._ext_dir()
        for i in reversed(range(self.ext_list_layout.count())):
            w = self.ext_list_layout.itemAt(i).widget()
            if w:
                w.deleteLater()

        if not os.path.exists(ext_dir):
            no_ext = QLabel("No extensions installed. Install one above.")
            no_ext.setStyleSheet("color: #6b7280; padding: 12px;")
            self.ext_list_layout.addWidget(no_ext)
            return

        for entry in os.listdir(ext_dir):
            ext_path = os.path.join(ext_dir, entry)
            if not os.path.isdir(ext_path):
                continue

            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background-color: #1f2937;
                    border: 1px solid #374151;
                    border-radius: 10px;
                    padding: 12px;
                }
            """)
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(12, 8, 12, 8)

            info_layout = QVBoxLayout()
            info_layout.addWidget(QLabel(f"<b style='color:#a78bfa'>{entry}</b>"))

            config_file = os.path.join(ext_path, "qwen-extension.json")
            if os.path.exists(config_file):
                try:
                    with open(config_file, "r") as f:
                        cfg = json.load(f)
                    version = cfg.get("version", "unknown")
                    mcp_count = len(cfg.get("mcpServers", {}))
                    skills = cfg.get("skills", [])
                    agents = cfg.get("agents", [])
                    info_layout.addWidget(QLabel(
                        f"<span style='color:#9ca3af'>v{version} | MCP: {mcp_count} | Skills: {len(skills)} | Agents: {len(agents)}</span>"
                    ))
                except Exception:
                    pass
            else:
                info_layout.addWidget(QLabel("<span style='color:#9ca3af'>Local extension</span>"))

            info_widget = QWidget()
            info_widget.setLayout(info_layout)
            card_layout.addWidget(info_widget, 1)

            remove_btn = QPushButton("Remove")
            remove_btn.setFixedSize(60, 36)
            remove_btn.clicked.connect(lambda checked, p=ext_path: self._remove_extension(p, entry))
            card_layout.addWidget(remove_btn)

            self.ext_list_layout.addWidget(card)

    def _install_extension(self):
        source = self.ext_source_input.text().strip()
        if not source:
            QMessageBox.warning(self, "Error", "Please enter a source URL or path.")
            return

        ext_dir = self._ext_dir()
        os.makedirs(ext_dir, exist_ok=True)

        if source.startswith("http"):
            name = source.rstrip("/").split("/")[-1].replace(".git", "")
            cmd = ["git", "clone", source, os.path.join(ext_dir, name)]
        elif "/" in source and not os.path.exists(source):
            name = source.split("/")[-1]
            cmd = ["git", "clone", f"https://github.com/{source}", os.path.join(ext_dir, name)]
        elif os.path.exists(source):
            name = os.path.basename(source.rstrip("/\\"))
            target = os.path.join(ext_dir, name)
            if os.path.exists(target):
                QMessageBox.warning(self, "Error", f"Extension '{name}' already exists.")
                return
            try:
                shutil.copytree(source, target)
                self.ext_source_input.clear()
                self._load_extensions()
                QMessageBox.information(self, "Success", f"Extension '{name}' installed!")
                return
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to install: {e}")
                return
        else:
            QMessageBox.warning(self, "Error", "Invalid source. Use a GitHub URL, owner/repo, or local path.")
            return

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            self.ext_source_input.clear()
            self._load_extensions()
            QMessageBox.information(self, "Success", f"Extension '{name}' installed!")
        except subprocess.CalledProcessError as e:
            QMessageBox.warning(self, "Error", f"Git clone failed: {e.stderr}")
        except FileNotFoundError:
            QMessageBox.warning(self, "Error", "Git not found. Please install Git first.")

    def _remove_extension(self, path: str, name: str):
        try:
            shutil.rmtree(path)
            self._load_extensions()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to remove: {e}")

    # ─── AGENTS PAGE ────────────────────────────────────────────────────────

    def _create_agents_page(self):
        page, layout = self._make_page()

        info = QLabel("Agents are specialized AI assistants with custom prompts, tools, and models.")
        info.setWordWrap(True)
        info.setStyleSheet("color: #9ca3af; font-size: 13px; margin-bottom: 8px;")
        layout.addWidget(info)

        create_group = QGroupBox("Create Agent")
        create_layout = QFormLayout(create_group)

        self.agent_name_input = QLineEdit()
        self.agent_name_input.setPlaceholderText("e.g. code-reviewer, researcher")
        create_layout.addRow("Name:", self.agent_name_input)

        self.agent_model_combo = QComboBox()
        self.agent_model_combo.addItems(["qwen-coder-plus", "qwen-plus", "qwen-max"])
        create_layout.addRow("Model:", self.agent_model_combo)

        self.agent_tools_input = QLineEdit()
        self.agent_tools_input.setPlaceholderText("e.g. read_file, shell, grep, glob")
        create_layout.addRow("Tools:", self.agent_tools_input)

        self.agent_prompt_input = QTextEdit()
        self.agent_prompt_input.setPlaceholderText("System prompt for the agent...")
        self.agent_prompt_input.setMinimumHeight(120)
        create_layout.addRow("Prompt:", self.agent_prompt_input)

        create_btn_layout = QHBoxLayout()
        create_agent_btn = QPushButton("Create Agent")
        create_agent_btn.clicked.connect(self._create_agent)
        create_btn_layout.addWidget(create_agent_btn)
        create_btn_layout.addStretch()
        create_layout.addRow("", create_btn_layout)

        layout.addWidget(create_group)

        self.agent_list_group = QGroupBox("Available Agents")
        self.agent_list_layout = QVBoxLayout(self.agent_list_group)
        self.agent_list_layout.setSpacing(8)
        self._load_agents()
        layout.addWidget(self.agent_list_group)

        layout.addStretch()
        self.stacked.addWidget(self._wrap_in_scroll(page))

    def _agent_dir(self) -> str:
        return os.path.join(os.path.expanduser("~"), ".qwen", "agents")

    def _load_agents(self):
        agent_dir = self._agent_dir()
        for i in reversed(range(self.agent_list_layout.count())):
            w = self.agent_list_layout.itemAt(i).widget()
            if w:
                w.deleteLater()

        if not os.path.exists(agent_dir):
            no_agents = QLabel("No agents created yet. Create one above.")
            no_agents.setStyleSheet("color: #6b7280; padding: 12px;")
            self.agent_list_layout.addWidget(no_agents)
            return

        for entry in os.listdir(agent_dir):
            if not entry.endswith(".md"):
                continue

            agent_path = os.path.join(agent_dir, entry)
            name = entry[:-3]

            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background-color: #1f2937;
                    border: 1px solid #374151;
                    border-radius: 10px;
                    padding: 12px;
                }
            """)
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(12, 8, 12, 8)

            info_layout = QVBoxLayout()
            info_layout.addWidget(QLabel(f"<b style='color:#a78bfa'>{name}</b>"))

            try:
                with open(agent_path, "r") as f:
                    content = f.read()
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        import yaml
                        frontmatter = yaml.safe_load(parts[1]) or {}
                        model = frontmatter.get("modelConfig", {}).get("model", "default")
                        tools = frontmatter.get("tools", [])
                        desc = frontmatter.get("description", "")
                        info_layout.addWidget(QLabel(f"<span style='color:#9ca3af'>Model: {model} | Tools: {', '.join(tools)}</span>"))
                        if desc:
                            info_layout.addWidget(QLabel(f"<span style='color:#6b7280'>{desc}</span>"))
            except Exception:
                pass

            info_widget = QWidget()
            info_widget.setLayout(info_layout)
            card_layout.addWidget(info_widget, 1)

            remove_btn = QPushButton("Remove")
            remove_btn.setFixedSize(60, 36)
            remove_btn.clicked.connect(lambda checked, p=agent_path: self._remove_agent(p))
            card_layout.addWidget(remove_btn)

            self.agent_list_layout.addWidget(card)

    def _create_agent(self):
        name = self.agent_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Please enter an agent name.")
            return

        agent_dir = self._agent_dir()
        os.makedirs(agent_dir, exist_ok=True)

        model = self.agent_model_combo.currentText()
        tools_str = self.agent_tools_input.text().strip()
        tools = [t.strip() for t in tools_str.split(",") if t.strip()] if tools_str else ["read_file", "shell"]
        prompt = self.agent_prompt_input.toPlainText().strip() or f"You are a {name} assistant."

        agent_file = os.path.join(agent_dir, f"{name}.md")
        if os.path.exists(agent_file):
            QMessageBox.warning(self, "Error", f"Agent '{name}' already exists.")
            return

        import yaml
        frontmatter = {
            "name": name,
            "description": f"{name} agent",
            "tools": tools,
            "modelConfig": {"model": model},
            "runConfig": {"max_time_minutes": 10, "max_turns": 20},
        }

        content = f"---\n{yaml.dump(frontmatter, default_flow_style=False)}---\n\n{prompt}\n"

        with open(agent_file, "w") as f:
            f.write(content)

        self.agent_name_input.clear()
        self.agent_tools_input.clear()
        self.agent_prompt_input.clear()

        self._load_agents()
        QMessageBox.information(self, "Success", f"Agent '{name}' created!")

    def _remove_agent(self, path: str):
        try:
            os.remove(path)
            self._load_agents()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to remove: {e}")

    # ─── SKILLS PAGE ────────────────────────────────────────────────────────

    def _create_skills_page(self):
        page, layout = self._make_page()

        info = QLabel("Skills are reusable instruction bundles that teach Qwen how to perform specific tasks.")
        info.setWordWrap(True)
        info.setStyleSheet("color: #9ca3af; font-size: 13px; margin-bottom: 8px;")
        layout.addWidget(info)

        create_group = QGroupBox("Create Skill")
        create_layout = QFormLayout(create_group)

        self.skill_name_input = QLineEdit()
        self.skill_name_input.setPlaceholderText("e.g. paperclip, para-memory-files")
        create_layout.addRow("Name:", self.skill_name_input)

        self.skill_desc_input = QLineEdit()
        self.skill_desc_input.setPlaceholderText("Brief description of what this skill does")
        create_layout.addRow("Description:", self.skill_desc_input)

        self.skill_tools_input = QLineEdit()
        self.skill_tools_input.setPlaceholderText("e.g. read_file, write_file, shell")
        create_layout.addRow("Allowed Tools:", self.skill_tools_input)

        self.skill_content_input = QTextEdit()
        self.skill_content_input.setPlaceholderText("Detailed instructions for the AI agent...")
        self.skill_content_input.setMinimumHeight(120)
        create_layout.addRow("Instructions:", self.skill_content_input)

        create_btn_layout = QHBoxLayout()
        create_skill_btn = QPushButton("Create Skill")
        create_skill_btn.clicked.connect(self._create_skill)
        create_btn_layout.addWidget(create_skill_btn)
        create_btn_layout.addStretch()
        create_layout.addRow("", create_btn_layout)

        layout.addWidget(create_group)

        self.skill_list_group = QGroupBox("Available Skills")
        self.skill_list_layout = QVBoxLayout(self.skill_list_group)
        self.skill_list_layout.setSpacing(8)
        self._load_skills()
        layout.addWidget(self.skill_list_group)

        layout.addStretch()
        self.stacked.addWidget(self._wrap_in_scroll(page))

    def _skill_dir(self) -> str:
        return os.path.join(os.path.expanduser("~"), ".qwen", "skills")

    def _load_skills(self):
        skill_dir = self._skill_dir()
        for i in reversed(range(self.skill_list_layout.count())):
            w = self.skill_list_layout.itemAt(i).widget()
            if w:
                w.deleteLater()

        if not os.path.exists(skill_dir):
            no_skills = QLabel("No skills created yet. Create one above.")
            no_skills.setStyleSheet("color: #6b7280; padding: 12px;")
            self.skill_list_layout.addWidget(no_skills)
            return

        for entry in os.listdir(skill_dir):
            entry_path = os.path.join(skill_dir, entry)
            if not os.path.isdir(entry_path):
                continue

            skill_file = os.path.join(entry_path, "SKILL.md")
            if not os.path.exists(skill_file):
                continue

            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background-color: #1f2937;
                    border: 1px solid #374151;
                    border-radius: 10px;
                    padding: 12px;
                }
            """)
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(12, 8, 12, 8)

            info_layout = QVBoxLayout()
            info_layout.addWidget(QLabel(f"<b style='color:#a78bfa'>{entry}</b>"))

            try:
                with open(skill_file, "r") as f:
                    content = f.read()
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        import yaml
                        fm = yaml.safe_load(parts[1]) or {}
                        desc = fm.get("description", "")
                        tools = fm.get("allowedTools", [])
                        info_layout.addWidget(QLabel(f"<span style='color:#9ca3af'>{desc}</span>"))
                        info_layout.addWidget(QLabel(f"<span style='color:#6b7280'>Tools: {', '.join(tools)}</span>"))
            except Exception:
                pass

            info_widget = QWidget()
            info_widget.setLayout(info_layout)
            card_layout.addWidget(info_widget, 1)

            remove_btn = QPushButton("Remove")
            remove_btn.setFixedSize(60, 36)
            remove_btn.clicked.connect(lambda checked, p=entry_path: self._remove_skill(p))
            card_layout.addWidget(remove_btn)

            self.skill_list_layout.addWidget(card)

    def _create_skill(self):
        name = self.skill_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Please enter a skill name.")
            return

        skill_dir = self._skill_dir()
        skill_path = os.path.join(skill_dir, name)
        os.makedirs(skill_path, exist_ok=True)

        desc = self.skill_desc_input.text().strip() or f"{name} skill"
        tools_str = self.skill_tools_input.text().strip()
        tools = [t.strip() for t in tools_str.split(",") if t.strip()] if tools_str else ["read_file", "write_file"]
        content = self.skill_content_input.toPlainText().strip() or f"Instructions for {name}..."

        import yaml
        frontmatter = {
            "name": name,
            "description": desc,
            "allowedTools": tools,
        }

        skill_file = os.path.join(skill_path, "SKILL.md")
        skill_content = f"---\n{yaml.dump(frontmatter, default_flow_style=False)}---\n\n{content}\n"

        with open(skill_file, "w") as f:
            f.write(skill_content)

        self.skill_name_input.clear()
        self.skill_desc_input.clear()
        self.skill_tools_input.clear()
        self.skill_content_input.clear()

        self._load_skills()
        QMessageBox.information(self, "Success", f"Skill '{name}' created!")

    def _remove_skill(self, path: str):
        try:
            shutil.rmtree(path)
            self._load_skills()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to remove: {e}")

    # ─── TERMINAL PAGE ──────────────────────────────────────────────────────

    def _create_terminal_page(self):
        page, layout = self._make_page()

        info = QLabel("Execute shell commands directly. Commands run in your system shell.")
        info.setWordWrap(True)
        info.setStyleSheet("color: #9ca3af; font-size: 13px; margin-bottom: 8px;")
        layout.addWidget(info)

        self.terminal_output = QTextEdit()
        self.terminal_output.setReadOnly(True)
        self.terminal_output.setFont(QFont("Consolas", 12))
        self.terminal_output.setStyleSheet("""
            QTextEdit {
                background-color: #0d1117;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 10px;
                padding: 12px;
            }
        """)
        self.terminal_output.setMinimumHeight(300)
        layout.addWidget(self.terminal_output)

        cmd_layout = QHBoxLayout()
        self.terminal_prompt_label = QLabel(">")
        self.terminal_prompt_label.setStyleSheet("color: #6366f1; font-weight: bold; font-size: 16px;")
        cmd_layout.addWidget(self.terminal_prompt_label)

        self.terminal_input = QLineEdit()
        self.terminal_input.setPlaceholderText("Enter command...")
        self.terminal_input.setFont(QFont("Consolas", 12))
        self.terminal_input.returnPressed.connect(self._execute_command)
        cmd_layout.addWidget(self.terminal_input)

        exec_btn = QPushButton("Run")
        exec_btn.clicked.connect(self._execute_command)
        exec_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1, stop:1 #8b5cf6);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 20px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4f46e5, stop:1 #7c3aed);
            }
        """)
        cmd_layout.addWidget(exec_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(lambda: self.terminal_output.clear())
        cmd_layout.addWidget(clear_btn)

        layout.addLayout(cmd_layout)

        shell_info = QGroupBox("Shell Info")
        shell_info_layout = QFormLayout(shell_info)
        shell = os.environ.get("SHELL", "cmd" if platform.system() == "Windows" else "bash")
        shell_info_layout.addRow("Shell:", QLabel(shell))
        shell_info_layout.addRow("OS:", QLabel(platform.system()))
        shell_info_layout.addRow("Working Dir:", QLabel(os.getcwd()))
        layout.addWidget(shell_info)

        self.stacked.addWidget(self._wrap_in_scroll(page))

    def _execute_command(self):
        cmd = self.terminal_input.text().strip()
        if not cmd:
            return

        self.terminal_input.clear()
        self.terminal_output.append(f"<span style='color:#6366f1;font-weight:bold'>> {cmd}</span>")
        self.terminal_output.append("<span style='color:#6b7280'>Running...</span>")

        self.terminal_output.verticalScrollBar().setValue(
            self.terminal_output.verticalScrollBar().maximum()
        )

        import threading
        def _run():
            try:
                if platform.system() == "Windows":
                    proc = subprocess.run(
                        ["cmd", "/c", cmd],
                        capture_output=True, text=True, timeout=30,
                        cwd=os.getcwd()
                    )
                else:
                    proc = subprocess.run(
                        ["bash", "-c", cmd],
                        capture_output=True, text=True, timeout=30,
                        cwd=os.getcwd()
                    )

                output = proc.stdout
                error = proc.stderr

                QTimer.singleShot(0, lambda: self._show_output(output, error, proc.returncode))
            except subprocess.TimeoutExpired:
                QTimer.singleShot(0, lambda: self._show_output("", "Command timed out (30s limit)", -1))
            except Exception as e:
                QTimer.singleShot(0, lambda: self._show_output("", str(e), -1))

        threading.Thread(target=_run, daemon=True).start()

    def _show_output(self, stdout: str, stderr: str, returncode: int):
        if stdout:
            self.terminal_output.append(f"<pre style='color:#e6edf3;margin:0'>{self._escape_html(stdout)}</pre>")
        if stderr:
            self.terminal_output.append(f"<pre style='color:#f87171;margin:0'>{self._escape_html(stderr)}</pre>")
        if returncode != 0:
            self.terminal_output.append(f"<span style='color:#f87171'>Exit code: {returncode}</span>")
        else:
            self.terminal_output.append(f"<span style='color:#34d399'>Exit code: 0</span>")

        self.terminal_output.append("")

        self.terminal_output.verticalScrollBar().setValue(
            self.terminal_output.verticalScrollBar().maximum()
        )

    def _escape_html(self, text: str) -> str:
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # ─── GENERAL PAGE ───────────────────────────────────────────────────────

    def _create_general_page(self):
        page, layout = self._make_page()

        api_group = QGroupBox("API Settings")
        api_layout = QFormLayout(api_group)

        self.api_model_combo = QComboBox()
        self.api_model_combo.addItems(["qwen-coder-plus", "qwen-plus", "qwen-max"])
        current_model = self.settings.get("api_model", "qwen-coder-plus")
        idx = self.api_model_combo.findText(current_model)
        if idx >= 0:
            self.api_model_combo.setCurrentIndex(idx)
        api_layout.addRow("Model:", self.api_model_combo)

        self.api_timeout_input = QLineEdit()
        self.api_timeout_input.setText(str(self.settings.get("api_timeout", 60)))
        api_layout.addRow("Timeout (s):", self.api_timeout_input)

        api_layout.addRow("", QLabel("<span style='color:#6b7280;font-size:12px'>Using Qwen OAuth (DashScope)</span>"))

        layout.addWidget(api_group)

        ui_group = QGroupBox("UI Settings")
        ui_layout = QFormLayout(ui_group)

        self.font_size_input = QLineEdit()
        self.font_size_input.setText(str(self.settings.get("font_size", 14)))
        ui_layout.addRow("Font Size:", self.font_size_input)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        ui_layout.addRow("Theme:", self.theme_combo)

        layout.addWidget(ui_group)

        save_layout = QHBoxLayout()
        save_btn = QPushButton("Save Settings")
        save_btn.setMinimumHeight(44)
        save_btn.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        save_btn.clicked.connect(self._save_general_settings)
        save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1, stop:1 #8b5cf6);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4f46e5, stop:1 #7c3aed);
            }
        """)
        save_layout.addWidget(save_btn)
        save_layout.addStretch()
        layout.addLayout(save_layout)

        layout.addStretch()
        self.stacked.addWidget(self._wrap_in_scroll(page))

    def _save_general_settings(self):
        self.settings.set("api_model", self.api_model_combo.currentText())
        self.settings.set("api_timeout", int(self.api_timeout_input.text() or "60"))
        self.settings.set("font_size", int(self.font_size_input.text() or "14"))
        self.settings.save()
        QMessageBox.information(self, "Success", "Settings saved!")
