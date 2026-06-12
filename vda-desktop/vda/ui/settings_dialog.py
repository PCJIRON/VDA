import asyncio

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QMessageBox, QGroupBox, QFormLayout, QWidget, QFileDialog,
    QStackedWidget, QFrame,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QDesktopServices
from PyQt6.QtCore import QUrl

from vda.auth.provider_config import ProviderConfig
from vda.config.defaults import PROVIDERS
from vda.config.settings import Settings
from vda.core.api_client import APIClient
from vda.core.zen_client import ZenClient


class TestWorker(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, settings: Settings):
        super().__init__()
        self.settings = settings

    def run(self):
        provider_id = self.settings.get("provider", "")
        if provider_id == "opencode":
            client = ZenClient(self.settings)
        else:
            client = APIClient(self.settings)
        try:
            success, msg = asyncio.run(client.test_connection())
            self.finished.emit(success, msg)
        except Exception as e:
            self.finished.emit(False, str(e))


class SettingsDialog(QDialog):
    def __init__(self, provider_config: ProviderConfig, settings: Settings, parent=None):
        super().__init__(parent)
        self._config = provider_config
        self._settings = settings
        self.setWindowTitle("Settings")
        self.setFixedSize(720, 500)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        # Style sheet to match vda-gui charcoal look
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e24;
                color: white;
            }
            QLabel { color: #ffffff; background: transparent; }
            QLineEdit, QComboBox {
                background-color: #141418;
                color: white;
                border: 1px solid #404040;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #2563eb;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #141418;
                color: white;
                selection-background-color: #262626;
                border: 1px solid #404040;
            }
            QPushButton {
                background-color: #262626;
                color: #e5e5e5;
                border: 1px solid #404040;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #404040;
            }
            QPushButton:pressed {
                background-color: #151518;
            }
        """)

        # Main horizontal layout (content on left, sidebar on right)
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left Content Area (Stacked Widget)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(30, 30, 30, 30)
        self.content_layout.setSpacing(20)

        self.content_stack = QStackedWidget()
        self.content_layout.addWidget(self.content_stack)
        main_layout.addWidget(self.content_widget, 1)

        # Right Sidebar Frame
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(220)
        self.sidebar.setStyleSheet("""
            QFrame {
                background-color: #151518;
                border-left: 1px solid #262626;
            }
        """)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(16, 20, 16, 20)
        sidebar_layout.setSpacing(12)

        # Sidebar Title
        sb_title_row = QHBoxLayout()
        sb_title = QLabel("SETTINGS")
        sb_title.setStyleSheet("color: #737373; font-size: 11px; font-weight: bold; letter-spacing: 1px;")
        sb_close_btn = QPushButton("✕")
        sb_close_btn.setFixedSize(24, 24)
        sb_close_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #a3a3a3; border: none; font-size: 14px; font-weight: bold; padding: 0px;
            }
            QPushButton:hover { background: #262626; border-radius: 6px; }
        """)
        sb_close_btn.clicked.connect(self.reject)
        sb_title_row.addWidget(sb_title)
        sb_title_row.addStretch()
        sb_title_row.addWidget(sb_close_btn)
        sidebar_layout.addLayout(sb_title_row)

        # Sidebar Navigation Buttons
        self.btn_ai = QPushButton("  AI Provider")
        self.btn_mcp = QPushButton("  MCP Server")
        self.btn_skills = QPushButton("  Skills")

        for btn in (self.btn_ai, self.btn_mcp, self.btn_skills):
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(40)
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent; color: #a3a3a3; border: none;
                    text-align: left; font-size: 13px; font-weight: 500; border-radius: 10px;
                }
                QPushButton:hover { background: #262626; color: #e5e5e5; }
                QPushButton:checked { background: rgba(37, 99, 235, 0.1); color: #60a5fa; }
            """)

        self.btn_ai.clicked.connect(lambda: self._set_tab('ai'))
        self.btn_mcp.clicked.connect(lambda: self._set_tab('mcp'))
        self.btn_skills.clicked.connect(lambda: self._set_tab('skills'))

        sidebar_layout.addWidget(self.btn_ai)
        sidebar_layout.addWidget(self.btn_mcp)
        sidebar_layout.addWidget(self.btn_skills)
        sidebar_layout.addStretch()

        # Save & Close button at bottom of sidebar
        save_btn = QPushButton("Save & Close")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: white; color: black; border: none;
                border-radius: 12px; padding: 10px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #e5e5e5; }
        """)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._on_save)
        sidebar_layout.addWidget(save_btn)

        main_layout.addWidget(self.sidebar)

        # === PAGE 1: AI PROVIDER ===
        page_ai = QWidget()
        page_ai_layout = QVBoxLayout(page_ai)
        page_ai_layout.setContentsMargins(0, 0, 0, 0)
        page_ai_layout.setSpacing(16)

        ai_header = QLabel("AI Provider")
        ai_header.setStyleSheet("font-size: 20px; font-weight: bold;")
        ai_desc = QLabel("Configure your preferred AI model and API keys.")
        ai_desc.setStyleSheet("color: #a3a3a3; font-size: 13px;")

        page_ai_layout.addWidget(ai_header)
        page_ai_layout.addWidget(ai_desc)

        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        form_layout.setContentsMargins(0, 10, 0, 10)
        form_layout.setSpacing(14)

        provider_lbl = QLabel("Provider")
        provider_lbl.setStyleSheet("font-size: 13px; font-weight: 500; color: #e5e5e5;")
        self.provider_combo = QComboBox()
        provider_ids = []
        for pid, info in PROVIDERS.items():
            self.provider_combo.addItem(info["name"], pid)
            provider_ids.append(pid)
        current_id = self._config.get_provider_id()
        idx = provider_ids.index(current_id) if current_id in provider_ids else 0
        self.provider_combo.setCurrentIndex(idx)
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        form_layout.addRow(provider_lbl, self.provider_combo)

        # API Key Row
        key_lbl = QLabel("API Key")
        key_lbl.setStyleSheet("font-size: 13px; font-weight: 500; color: #e5e5e5;")
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("Enter your API key...")
        current_key = self._config.get_api_key()
        if current_key:
            self.api_key_input.setText(current_key)
            
        form_layout.addRow(key_lbl, self.api_key_input)

        # Helper links and hints for API key
        hint_row = QHBoxLayout()
        self.docs_link = QLabel()
        self.docs_link.setStyleSheet("color: #3b82f6; font-size: 11px; font-weight: 500;")
        self.docs_link.setCursor(Qt.CursorShape.PointingHandCursor)
        self.docs_link.mousePressEvent = lambda e: self._open_docs()
        
        self.api_hint = QLabel()
        self.api_hint.setStyleSheet("color: #737373; font-size: 11px;")
        
        hint_row.addWidget(self.docs_link)
        hint_row.addStretch()
        hint_row.addWidget(self.api_hint)
        form_layout.addRow("", hint_row)

        model_lbl = QLabel("Model")
        model_lbl.setStyleSheet("font-size: 13px; font-weight: 500; color: #e5e5e5;")
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.model_combo.setPlaceholderText("Select or type a model ID...")
        current_model = self._config.get_model()
        if current_model:
            self.model_combo.setCurrentText(current_model)
        form_layout.addRow(model_lbl, self.model_combo)

        # Base URL for Custom provider
        self.base_url_container = QWidget()
        base_url_lay = QHBoxLayout(self.base_url_container)
        base_url_lay.setContentsMargins(0, 0, 0, 0)
        base_url_label = QLabel("Base URL:")
        base_url_label.setStyleSheet("font-size: 11px; color: #737373;")
        self.base_url_input = QLineEdit()
        self.base_url_input.setPlaceholderText("https://api.example.com/v1")
        base_url_lay.addWidget(base_url_label)
        base_url_lay.addWidget(self.base_url_input, 1)
        form_layout.addRow("", self.base_url_container)

        page_ai_layout.addWidget(form_widget)

        # Connection testing row
        test_lay = QHBoxLayout()
        self.test_btn = QPushButton("Test Connection")
        self.test_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.test_btn.clicked.connect(self._on_test)
        self.test_status = QLabel()
        self.test_status.setStyleSheet("font-size: 12px; font-weight: 500;")
        self.test_status.setWordWrap(True)
        test_lay.addWidget(self.test_btn)
        test_lay.addWidget(self.test_status, 1)
        page_ai_layout.addLayout(test_lay)
        page_ai_layout.addStretch()

        self.content_stack.addWidget(page_ai)

        # === PAGE 2: MCP SERVER ===
        page_mcp = QWidget()
        page_mcp_layout = QVBoxLayout(page_mcp)
        page_mcp_layout.setContentsMargins(0, 0, 0, 0)
        page_mcp_layout.setSpacing(16)

        mcp_header = QLabel("MCP Server")
        mcp_header.setStyleSheet("font-size: 20px; font-weight: bold;")
        mcp_desc = QLabel("Connect to an external Model Context Protocol server.")
        mcp_desc.setStyleSheet("color: #a3a3a3; font-size: 13px;")

        page_mcp_layout.addWidget(mcp_header)
        page_mcp_layout.addWidget(mcp_desc)

        mcp_form = QWidget()
        mcp_form_layout = QFormLayout(mcp_form)
        mcp_form_layout.setContentsMargins(0, 10, 0, 10)
        mcp_form_layout.setSpacing(14)

        mcp_url_lbl = QLabel("Server URL")
        mcp_url_lbl.setStyleSheet("font-size: 13px; font-weight: 500; color: #e5e5e5;")
        self.mcp_url_input = QLineEdit()
        self.mcp_url_input.setPlaceholderText("http://localhost:3000/mcp")
        self.mcp_url_input.setText(self._settings.get("mcp_server_url", ""))
        mcp_form_layout.addRow(mcp_url_lbl, self.mcp_url_input)

        page_mcp_layout.addWidget(mcp_form)
        page_mcp_layout.addStretch()

        self.content_stack.addWidget(page_mcp)

        # === PAGE 3: SKILLS ===
        page_skills = QWidget()
        page_skills_layout = QVBoxLayout(page_skills)
        page_skills_layout.setContentsMargins(0, 0, 0, 0)
        page_skills_layout.setSpacing(16)

        skills_header = QLabel("Agent Skills")
        skills_header.setStyleSheet("font-size: 20px; font-weight: bold;")
        skills_desc = QLabel("Upload custom skills for your AI agent to use.")
        skills_desc.setStyleSheet("color: #a3a3a3; font-size: 13px;")

        page_skills_layout.addWidget(skills_header)
        page_skills_layout.addWidget(skills_desc)

        self._skills_path_input = QLineEdit()
        self._skills_path_input.setReadOnly(True)
        self._skills_path_input.setPlaceholderText("No skills file uploaded...")
        self._skills_path_input.setText(self._settings.get("skills_md_path", ""))

        self.upload_area = QPushButton("Upload skills.md\n(Click to browse file)")
        self.upload_area.setCursor(Qt.CursorShape.PointingHandCursor)
        self.upload_area.setStyleSheet("""
            QPushButton {
                border: 2px dashed #404040;
                border-radius: 12px;
                background-color: #141418;
                color: #a3a3a3;
                padding: 40px;
                font-size: 13px;
                text-align: center;
            }
            QPushButton:hover {
                border: 2px dashed #6b7280;
                color: #e5e5e5;
            }
        """)
        self.upload_area.clicked.connect(self._browse_skills_file)

        page_skills_layout.addWidget(self._skills_path_input)
        page_skills_layout.addWidget(self.upload_area)

        skills_clear_row = QHBoxLayout()
        skills_clear_row.addStretch()
        clear_btn = QPushButton("Clear File")
        clear_btn.setFixedWidth(100)
        clear_btn.clicked.connect(self._clear_skills_file)
        skills_clear_row.addWidget(clear_btn)
        page_skills_layout.addLayout(skills_clear_row)
        page_skills_layout.addStretch()

        self.content_stack.addWidget(page_skills)

        # Set default tab
        self._set_tab('ai')
        self._update_fields()

    def _set_tab(self, tab: str):
        # Uncheck all navigation buttons first
        self.btn_ai.setChecked(False)
        self.btn_mcp.setChecked(False)
        self.btn_skills.setChecked(False)

        if tab == 'ai':
            self.btn_ai.setChecked(True)
            self.content_stack.setCurrentIndex(0)
        elif tab == 'mcp':
            self.btn_mcp.setChecked(True)
            self.content_stack.setCurrentIndex(1)
        elif tab == 'skills':
            self.btn_skills.setChecked(True)
            self.content_stack.setCurrentIndex(2)

    def _open_docs(self):
        url = self._config.get_provider_info().get("docs_url", "")
        if url:
            QDesktopServices.openUrl(QUrl(url))

    def _on_test(self):
        provider_id = self.provider_combo.currentData()
        api_key = self.api_key_input.text().strip()
        model = self.model_combo.currentText().strip()
        base_url = self.base_url_input.text().strip()

        provider_info = PROVIDERS.get(provider_id, {})
        allows_anon = provider_info.get("allow_anonymous", False)

        if not api_key and not allows_anon:
            self.test_status.setStyleSheet("font-size: 11px; color: #f87171;")
            self.test_status.setText("Please enter an API key first")
            return
        if not model:
            self.test_status.setStyleSheet("font-size: 11px; color: #f87171;")
            self.test_status.setText("Please select a model")
            return
        if not base_url:
            self.test_status.setStyleSheet("font-size: 11px; color: #f87171;")
            self.test_status.setText("Please enter a Base URL")
            return

        self.test_btn.setEnabled(False)
        self.test_status.setStyleSheet("font-size: 11px; color: #fbbf24;")
        self.test_status.setText("Testing...")

        test_settings = Settings()
        test_settings.set("provider", provider_id)
        test_settings.set("api_key", api_key)
        test_settings.set("api_model", model)
        test_settings.set("api_base_url", base_url)
        test_settings.set("api_timeout", 15)

        self._worker = TestWorker(test_settings)
        self._worker.finished.connect(self._on_test_result)
        self._worker.start()

    def _on_test_result(self, success: bool, msg: str):
        self.test_btn.setEnabled(True)
        if success:
            self.test_status.setStyleSheet("font-size: 11px; color: #34d399;")
            self.test_status.setText(f"Connected: {msg}")
        else:
            self.test_status.setStyleSheet("font-size: 11px; color: #f87171;")
            self.test_status.setText(f"Failed: {msg}")

    def _on_provider_changed(self, idx):
        self.test_status.clear()
        self._update_fields()

    def _update_fields(self):
        provider_id = self.provider_combo.currentData()
        info = PROVIDERS.get(provider_id, PROVIDERS["openrouter"])

        self.model_combo.clear()
        models = info.get("models", [])
        self.model_combo.addItems(models)
        if models:
            self.model_combo.setCurrentIndex(0)

        is_custom = provider_id == "custom"
        self.base_url_container.setVisible(is_custom)

        if is_custom:
            self.base_url_input.setText(self._config.get_base_url())
        else:
            self.base_url_input.setText(info.get("base_url", ""))

        hint = info.get("api_key_hint", "")
        allows_anon = info.get("allow_anonymous", False)
        if allows_anon:
            self.api_hint.setText(f"e.g. {hint} (optional for free models)" if hint else "(optional for free models)")
        else:
            self.api_hint.setText(f"e.g. {hint}" if hint else "")

        docs_url = info.get("docs_url", "")
        if docs_url:
            self.docs_link.setText(f"Get API key \u2192 {docs_url}")
            self.docs_link.show()
        else:
            self.docs_link.hide()

        current_model = self._config.get_model()
        if current_model and provider_id == self._config.get_provider_id():
            idx = self.model_combo.findText(current_model)
            if idx >= 0:
                self.model_combo.setCurrentIndex(idx)
            else:
                self.model_combo.setCurrentText(current_model)

    def _on_save(self):
        provider_id = self.provider_combo.currentData()
        api_key = self.api_key_input.text().strip()
        model = self.model_combo.currentText().strip()
        base_url = self.base_url_input.text().strip()

        provider_info = PROVIDERS.get(provider_id, {})
        allows_anon = provider_info.get("allow_anonymous", False)

        if not api_key and not allows_anon:
            QMessageBox.warning(self, "Missing API Key", "Please enter your API key.")
            return

        if not model:
            QMessageBox.warning(self, "Missing Model", "Please select or type a model ID.")
            return

        if not base_url:
            QMessageBox.warning(self, "Missing Base URL", "Please enter the API base URL.")
            return

        skills_path = self._skills_path_input.text().strip()
        self._settings.set("skills_md_path", skills_path)

        mcp_url = self.mcp_url_input.text().strip()
        self._settings.set("mcp_server_url", mcp_url)

        self._config.save(provider_id, api_key, model, base_url)
        QMessageBox.information(self, "Saved", f"Settings saved for {self._config.get_provider_name()}!")
        self.accept()

    def _browse_skills_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Skills File", "",
            "Markdown Files (*.md);;All Files (*)"
        )
        if path:
            self._skills_path_input.setText(path)

    def _clear_skills_file(self):
        self._skills_path_input.clear()
