import asyncio

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QMessageBox, QGroupBox, QFormLayout, QWidget, QFileDialog,
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
        self.setWindowTitle("Settings - AI Provider")
        self.setFixedSize(540, 540)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self.setStyleSheet("""
            QDialog {
                background-color: #0B0F19;
                color: #F8FAFC;
            }
            QGroupBox {
                color: #F8FAFC;
                border: 1px solid #2A2F42;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
                color: #94A3B8;
            }
            QLabel { color: #F8FAFC; }
            QLineEdit, QComboBox {
                background-color: #151924;
                color: #F8FAFC;
                border: 1px solid #2A2F42;
                border-radius: 6px;
                padding: 6px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #9333ea;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #151924;
                color: #F8FAFC;
                selection-background-color: #1E293B;
                border: 1px solid #2A2F42;
            }
            QPushButton {
                background-color: #151924;
                color: #F8FAFC;
                border: 1px solid #2A2F42;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #1E293B;
            }
            QPushButton:pressed {
                background-color: #334155;
            }
            QPushButton:checked {
                background-color: #1E293B;
                border: 1px solid #9333ea;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel("AI Provider Settings")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        desc = QLabel(
            "Select your AI provider, enter the API key, and pick a model."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #94A3B8; font-size: 12px;")
        layout.addWidget(desc)

        # Provider dropdown
        provider_group = QGroupBox("1. Choose Provider")
        provider_layout = QVBoxLayout(provider_group)
        self.provider_combo = QComboBox()
        provider_ids = []
        for pid, info in PROVIDERS.items():
            self.provider_combo.addItem(info["name"], pid)
            provider_ids.append(pid)
        current_id = self._config.get_provider_id()
        idx = provider_ids.index(current_id) if current_id in provider_ids else 0
        self.provider_combo.setCurrentIndex(idx)
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        provider_layout.addWidget(self.provider_combo)

        self.docs_link = QLabel()
        self.docs_link.setStyleSheet("color: #6366f1; font-size: 11px;")
        self.docs_link.setCursor(Qt.CursorShape.PointingHandCursor)
        self.docs_link.mousePressEvent = lambda e: self._open_docs()
        provider_layout.addWidget(self.docs_link)
        layout.addWidget(provider_group)

        # API Key
        api_group = QGroupBox("2. Enter API Key")
        api_layout = QVBoxLayout(api_group)
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("Paste your API key here...")
        current_key = self._config.get_api_key()
        if current_key:
            self.api_key_input.setText(current_key)
        api_layout.addWidget(self.api_key_input)

        toggle_row = QHBoxLayout()
        toggle_btn = QPushButton("Show")
        toggle_btn.setFixedWidth(60)
        toggle_btn.setCheckable(True)
        toggle_btn.toggled.connect(
            lambda checked: self.api_key_input.setEchoMode(
                QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
            )
        )
        toggle_row.addWidget(toggle_btn)
        toggle_row.addStretch()
        self.api_hint = QLabel()
        self.api_hint.setStyleSheet("color: #9ca3af; font-size: 11px;")
        toggle_row.addWidget(self.api_hint)
        api_layout.addLayout(toggle_row)
        layout.addWidget(api_group)

        # Model selection
        model_group = QGroupBox("3. Choose Model")
        model_layout = QVBoxLayout(model_group)
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.model_combo.setPlaceholderText("Select or type a model ID...")
        current_model = self._config.get_model()
        if current_model:
            self.model_combo.setCurrentText(current_model)
        model_layout.addWidget(self.model_combo)

        # Base URL - shown only for Custom provider
        self.base_url_container = QWidget()
        base_url_layout = QHBoxLayout(self.base_url_container)
        base_url_layout.setContentsMargins(0, 4, 0, 0)
        base_url_label = QLabel("Base URL:")
        base_url_label.setStyleSheet("font-size: 11px; color: #6b7280;")
        self.base_url_input = QLineEdit()
        self.base_url_input.setPlaceholderText("https://api.example.com/v1")
        base_url_layout.addWidget(base_url_label)
        base_url_layout.addWidget(self.base_url_input, 1)
        model_layout.addWidget(self.base_url_container)

        layout.addWidget(model_group)

        # Skills file (optional)
        skills_group = QGroupBox("Skills File (Optional)")
        skills_layout = QHBoxLayout(skills_group)
        self._skills_path_input = QLineEdit()
        self._skills_path_input.setReadOnly(True)
        self._skills_path_input.setPlaceholderText("No file selected...")
        self._skills_path_input.setText(self._settings.get("skills_md_path", ""))
        skills_layout.addWidget(self._skills_path_input, 1)

        browse_btn = QPushButton("Browse...")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self._browse_skills_file)
        skills_layout.addWidget(browse_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.setFixedWidth(60)
        clear_btn.clicked.connect(self._clear_skills_file)
        skills_layout.addWidget(clear_btn)

        layout.addWidget(skills_group)

        # Test & Save buttons
        self.test_btn = QPushButton("Test Connection")
        self.test_btn.setStyleSheet("""
            QPushButton {
                background: #151924; color: #F8FAFC; border: 1px solid #2A2F42;
                border-radius: 6px; padding: 8px 18px; font-weight: bold;
            }
            QPushButton:hover { background: #1E293B; }
            QPushButton:disabled { background: #0B0F19; color: #475569; }
        """)
        self.test_btn.clicked.connect(self._on_test)
        self.test_status = QLabel()
        self.test_status.setStyleSheet("font-size: 11px;")
        self.test_status.setWordWrap(True)

        test_row = QHBoxLayout()
        test_row.addWidget(self.test_btn)
        test_row.addWidget(self.test_status, 1)
        layout.addLayout(test_row)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #9333ea, stop:1 #2563eb); 
                color: white; border: none;
                border-radius: 6px; padding: 8px 24px; font-weight: bold;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #a855f7, stop:1 #3b82f6); }
        """)
        save_btn.clicked.connect(self._on_save)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

        self._update_fields()

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
