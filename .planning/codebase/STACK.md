# Technology Stack

**Analysis Date:** 2026-06-06

## Languages

**Primary:**
- Python 3.9+ - Core application logic, all source code in `qwen-desktop/qwen_desktop/`

**Secondary:**
- Not detected

## Runtime

**Environment:**
- CPython (standard Python runtime), requires >= 3.9

**Package Manager:**
- pip (via `requirements.txt` and `requirements-dev.txt`)
- Build system: setuptools (configured in `qwen-desktop/pyproject.toml`)
- Lockfile: Not detected (no `poetry.lock`, `Pipfile.lock`, or `pdm.lock` present)

## Frameworks

**Core:**
- PyQt6 >= 6.4.0 - Desktop GUI framework used for the entire UI layer (`qwen-desktop/qwen_desktop/ui/`, `qwen_desktop/app.py`)
- httpx >= 0.25.0 - Async HTTP client for AI API communication (`qwen-desktop/qwen_desktop/core/api_client.py`, `core/zen_client.py`)

**GUI Subcomponents (PyQt6):**
- `QApplication`, `QWidget`, `QLineEdit`, `QPushButton`, `QLabel`, `QVBoxLayout`, `QHBoxLayout`, `QScrollArea`, `QFrame` - Primary UI widget set
- `QPropertyAnimation`, `QVariantAnimation`, `QEasingCurve` - Animation framework for expand/collapse transitions
- `QThread`, `pyqtSignal` - Background threading for API streaming
- `QComboBox`, `QGroupBox`, `QFormLayout`, `QDialog` - Settings dialog components
- `QFileDialog`, `QGraphicsDropShadowEffect`, `QMenu`, `QTimer` - Utility components

**Testing:**
- pytest >= 7.4.0 - Test runner (configured in `pyproject.toml` `[tool.pytest.ini_options]`)
- pytest-cov >= 4.1.0 - Coverage reporting
- pytest-qt >= 4.2.0 - Qt test helpers
- pytest-asyncio >= 0.21.0 - Async test support

**Build/Dev:**
- black >= 23.0.0 - Code formatter (line-length: 100, target-version: py39-py312)
- ruff >= 0.1.0 - Linter (select: E, F, W, I, N, D, UP; pydocstyle convention: google)
- mypy >= 1.5.0 - Static type checker (python_version: 3.9, warn_return_any: true)

## Key Dependencies

**Critical:**
- `PyQt6>=6.4.0` - Entire GUI depends on it; no alternative
- `httpx>=0.25.0` - All AI API communication (streaming, async); cannot function without it
- `openai>=1.0.0` - OpenAI-compatible API client (listed in `requirements.txt` but `api_client.py` uses raw httpx, not the openai SDK)
- `pyautogui>=0.9.54` - Screen capture, mouse control, keyboard automation for vision mode
- `opencv-python>=4.8.0` - Template matching for UI element detection; pixel verification

**Infrastructure:**
- `Pillow>=10.0.0` - Image processing (screenshot resize, format conversion)
- `pynput>=1.7.6` - Global mouse/keyboard event listeners (vision trigger)
- `keyring>=24.0.0` - Secure credential storage for API keys
- `requests>=2.31.0` / `requests-oauthlib>=1.3.1` - OAuth flow support
- `flask>=3.0.0` - Local OAuth callback server (port 8080)
- `python-dotenv>=1.0.0` - Environment variable loading
- `pyyaml>=6.0.0` - YAML configuration parsing
- `markdown>=3.5.0` - Markdown rendering for AI responses
- `pygments>=2.17.0` - Syntax highlighting for code blocks
- `nest-asyncio>=1.6.0` - Async event loop integration with Qt event loop
- `aiofiles>=23.0.0` - Async file I/O
- `uiautomation>=2.0.18` - Windows UI Automation for 100% accurate element detection (Windows only)

## Configuration

**Environment:**
- Settings stored as JSON at platform-specific paths:
  - Windows: `%LOCALAPPDATA%/QwenDesktop/config.json`
  - macOS: `~/Library/Preferences/QwenDesktop/config.json`
  - Linux: `~/.config/qwen-desktop/config.json`
  - Fallback: `~/.qwen-desktop/config.json`
- `python-dotenv` supports `.env` file loading (optional)
- API keys stored via `keyring` (OS-level credential manager) or in config file
- Logs written to `~/.qwen-desktop/app.log`
- Conversation history stored at `~/.qwen-desktop/sessions/{project_hash}/chats/`
- Memory/behavior data at `~/.qwen-desktop/memory/` and `~/.qwen-desktop/behavior/`
- UIED template images at `~/.qwen_desktop/uied_templates/`

**Default Settings** (`qwen-desktop/qwen_desktop/config/defaults.py`):
```python
DEFAULT_SETTINGS = {
    "provider": "openrouter",
    "api_base_url": "https://openrouter.ai/api/v1",
    "api_model": "deepseek/deepseek-v4-flash",
    "api_key": "",
    "api_timeout": 120,
    "theme": "dark",
    "font_size": 12,
    "window_width": 1200,
    "window_height": 800,
    "max_file_size_mb": 10,
    "max_attachments": 10,
    "allowed_extensions": [".py", ".js", ".ts", ...],
    "check_for_updates": False,
    "send_analytics": False,
    "auto_save_conversations": True,
}
```

**Build:**
- `pyproject.toml` at `qwen-desktop/pyproject.toml` - Project metadata, dependencies, tool configs
- `requirements.txt` at `qwen-desktop/requirements.txt` - Runtime dependencies (24 lines)
- `requirements-dev.txt` at `qwen-desktop/requirements-dev.txt` - Dev dependencies (14 lines)

## Platform Requirements

**Development:**
- Python 3.9+ installed
- pip install -r requirements.txt and requirements-dev.txt
- Windows recommended for full feature set (UI Automation, DPI scaling support)
- macOS/Linux supported but `uiautomation` is Windows-only

**Production:**
- Windows desktop (primary target, given `uiautomation`, `ctypes.windll`, DPI detection)
- No server deployment — this is a local desktop application
- Entry points: `py run.py` or `python -m qwen_desktop`

---

*Stack analysis: 2026-06-06*
