from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

STYLE_INPUT = """
    QLineEdit {
        background: #141418; border: 1px solid #404040; border-radius: 8px;
        padding: 8px 12px; color: white; font-size: 13px; outline: none;
    }
    QLineEdit:focus { border-color: #3b82f6; }
    QLineEdit::placeholder { color: #525252; }
"""

STYLE_COMBO = """
    QComboBox {
        background: #141418; border: 1px solid #404040; border-radius: 8px;
        padding: 8px 12px; color: white; font-size: 13px;
    }
    QComboBox:focus { border-color: #3b82f6; }
    QComboBox::drop-down { border: none; width: 24px; }
    QComboBox::down-arrow { image: none; border-left: 5px solid transparent;
        border-right: 5px solid transparent; border-top: 6px solid #a3a3a3; margin-right: 8px; }
    QComboBox QAbstractItemView {
        background: #1e1e24; border: 1px solid #404040; selection-background-color: #3b82f6;
        color: white; font-size: 13px; outline: none;
    }
"""


class _TabButton(QPushButton):
    def __init__(self, text, icon, parent=None):
        super().__init__(f"  {icon}  {text}", parent)
        self._active = False
        self.setFixedHeight(42)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(self._style())

    def _style(self):
        if self._active:
            return ("QPushButton { background: rgba(59,130,246,0.1); border: none; border-radius: 12px; "
                    "color: #60a5fa; font-size: 13px; font-weight: 500; text-align: left; padding: 8px 12px; }")
        return ("QPushButton { background: transparent; border: none; border-radius: 12px; "
                "color: #a3a3a3; font-size: 13px; font-weight: 500; text-align: left; padding: 8px 12px; } "
                "QPushButton:hover { background: #26262b; color: #e5e5e5; }")

    def set_active(self, active: bool):
        self._active = active
        self.setStyleSheet(self._style())


class SettingsModal(QDialog):
    saved = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.resize(800, 500)

        self._settings_data = {
            "provider": "OpenAI",
            "model": "gpt-4o",
            "custom_model": "",
            "api_key": "",
            "mcp_server": "",
        }

        self._init_ui()

    def _init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        backdrop = QPushButton(self)
        backdrop.setStyleSheet("background: rgba(0,0,0,0.4);")
        backdrop.setGeometry(0, 0, 16000, 16000)
        backdrop.clicked.connect(self.reject)
        backdrop.lower()

        container = QFrame(self)
        container.setFixedSize(720, 500)
        container.setStyleSheet("QFrame { background: #1e1e24; border: 1px solid #404040; border-radius: 16px; }")
        # Center the container
        container.move(40, 0)

        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Right sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(224)
        sidebar.setStyleSheet("background: #151518; border-left: 1px solid rgba(64,64,64,0.5); border-radius: 0 16px 16px 0;")
        s_layout = QVBoxLayout(sidebar)
        s_layout.setContentsMargins(16, 20, 16, 20)
        s_layout.setSpacing(4)

        header_row = QHBoxLayout()
        h = QLabel("  Settings")
        h.setStyleSheet("color: #737373; font-size: 13px; font-weight: 600; text-transform: uppercase;")
        header_row.addWidget(h)
        header_row.addStretch()
        close_top = QPushButton("\u2715")
        close_top.setFixedSize(28, 28)
        close_top.setCursor(Qt.CursorShape.PointingHandCursor)
        close_top.setStyleSheet(
            "QPushButton { background: transparent; border: none; border-radius: 8px; color: #a3a3a3; font-size: 16px; } "
            "QPushButton:hover { background: #26262b; color: white; }"
        )
        close_top.clicked.connect(self.reject)
        header_row.addWidget(close_top)
        s_layout.addLayout(header_row)
        s_layout.addSpacing(8)

        tabs = [
            ("\u2699", "AI Provider", 0),
            ("\U0001F5A5", "MCP Server", 1),
            ("\U0001F4C4", "Skills", 2),
        ]
        self._tab_btns = []
        self._tab_btn_frame = QVBoxLayout()
        self._tab_btn_frame.setSpacing(4)
        for icon, label, idx in tabs:
            btn = _TabButton(label, icon)
            btn.clicked.connect(lambda checked, i=idx: self._switch_tab(i))
            self._tab_btns.append(btn)
            self._tab_btn_frame.addWidget(btn)
        self._tab_btn_frame.addStretch()
        s_layout.addLayout(self._tab_btn_frame)

        s_layout.addStretch()

        save_btn = QPushButton("Save & Close")
        save_btn.setFixedHeight(42)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet(
            "QPushButton { background: white; border: none; border-radius: 12px; color: black; font-size: 13px; font-weight: 500; } "
            "QPushButton:hover { background: #e5e5e5; }"
        )
        save_btn.clicked.connect(self.accept)
        s_layout.addWidget(save_btn)

        layout.addWidget(sidebar)

        # Left content
        content = QFrame()
        content.setStyleSheet("background: transparent;")
        c_layout = QVBoxLayout(content)
        c_layout.setContentsMargins(32, 40, 32, 40)

        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background: transparent;")

        # Tab 0: AI Provider
        ai_page = QWidget()
        ai_layout = QVBoxLayout(ai_page)
        ai_layout.setSpacing(20)
        ai_layout.setContentsMargins(0, 0, 0, 0)

        self._build_section_header(ai_layout, "AI Provider", "Configure your preferred AI model and API keys.")

        ai_layout.addWidget(self._build_field("Provider", None))
        self._provider_combo = QComboBox()
        self._provider_combo.addItems(["OpenAI", "Anthropic", "Gemini", "Local"])
        self._provider_combo.setStyleSheet(STYLE_COMBO)
        ai_layout.addWidget(self._provider_combo)

        ai_layout.addWidget(self._build_field("Model", None))
        self._model_combo = QComboBox()
        self._model_combo.addItems(["GPT-4o", "GPT-4 Turbo", "Claude 3 Opus", "Claude 3.5 Sonnet", "Custom (Manual)"])
        self._model_combo.setStyleSheet(STYLE_COMBO)
        ai_layout.addWidget(self._model_combo)

        self._custom_model_input = QLineEdit()
        self._custom_model_input.setPlaceholderText("Enter custom model ID (e.g. llama-3-70b)")
        self._custom_model_input.setStyleSheet(STYLE_INPUT)
        self._custom_model_input.setVisible(False)
        self._model_combo.currentTextChanged.connect(self._on_model_changed)
        ai_layout.addWidget(self._custom_model_input)

        ai_layout.addWidget(self._build_field("API Key", None))
        self._api_key_input = QLineEdit()
        self._api_key_input.setPlaceholderText("Enter your API key...")
        self._api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._api_key_input.setStyleSheet(STYLE_INPUT)
        ai_layout.addWidget(self._api_key_input)

        ai_layout.addStretch()
        self._stack.addWidget(ai_page)

        # Tab 1: MCP Server
        mcp_page = QWidget()
        mcp_layout = QVBoxLayout(mcp_page)
        mcp_layout.setSpacing(20)
        mcp_layout.setContentsMargins(0, 0, 0, 0)

        self._build_section_header(mcp_layout, "MCP Server", "Connect to an external Model Context Protocol server.")

        mcp_layout.addWidget(self._build_field("Server URL", None))
        self._mcp_input = QLineEdit()
        self._mcp_input.setPlaceholderText("http://localhost:3000/mcp")
        self._mcp_input.setStyleSheet(STYLE_INPUT)
        mcp_layout.addWidget(self._mcp_input)

        mcp_layout.addStretch()
        self._stack.addWidget(mcp_page)

        # Tab 2: Skills
        skills_page = QWidget()
        skills_layout = QVBoxLayout(skills_page)
        skills_layout.setSpacing(20)
        skills_layout.setContentsMargins(0, 0, 0, 0)

        self._build_section_header(skills_layout, "Agent Skills", "Upload custom skills for your AI agent to use.")

        self._upload_btn = QPushButton()
        self._upload_btn.setFixedHeight(160)
        self._upload_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._upload_btn.setStyleSheet(
            "QPushButton { background: #141418; border: 2px dashed #404040; border-radius: 12px; color: #a3a3a3; font-size: 13px; } "
            "QPushButton:hover { border-color: #737373; }"
        )
        self._upload_btn.setText("\U0001F4C4  Upload skills.md\n\nDrag and drop or click to browse")
        self._upload_btn.clicked.connect(self._browse_file)
        skills_layout.addWidget(self._upload_btn)

        skills_layout.addStretch()
        self._stack.addWidget(skills_page)

        c_layout.addWidget(self._stack)
        layout.addWidget(content)

        self._switch_tab(0)

    def _build_section_header(self, layout, title, desc):
        t = QLabel(title)
        t.setStyleSheet("color: white; font-size: 20px; font-weight: 600;")
        layout.addWidget(t)
        d = QLabel(desc)
        d.setStyleSheet("color: #a3a3a3; font-size: 13px; padding-bottom: 8px;")
        d.setWordWrap(True)
        layout.addWidget(d)

    def _build_field(self, label, _):
        lbl = QLabel(label)
        lbl.setStyleSheet("color: #d4d4d4; font-size: 13px; font-weight: 500; padding-bottom: 4px;")
        return lbl

    def _on_model_changed(self, text):
        self._custom_model_input.setVisible(text == "Custom (Manual)")

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Skills File", "", "Markdown (*.md)")
        if path:
            leaf = path.replace("\\", "/").split("/")[-1]
            self._upload_btn.setText(f"\U0001F4C4  {leaf}")

    def _switch_tab(self, idx):
        for i, btn in enumerate(self._tab_btns):
            btn.set_active(i == idx)
        self._stack.setCurrentIndex(idx)

    def get_data(self) -> dict:
        return {
            "provider": self._provider_combo.currentText(),
            "model": self._model_combo.currentText(),
            "custom_model": self._custom_model_input.text(),
            "api_key": self._api_key_input.text(),
            "mcp_server": self._mcp_input.text(),
        }
