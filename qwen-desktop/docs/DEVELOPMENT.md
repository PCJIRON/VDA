# Qwen Desktop - Developer Guide

**Version:** 0.4.0  
**Last Updated:** 2026-03-28

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Building from Source](#building-from-source)
3. [Running Tests](#running-tests)
4. [Code Style Guide](#code-style-guide)
5. [Adding New Features](#adding-new-features)
6. [Debugging Tips](#debugging-tips)

---

## Project Structure

```
qwen-desktop/
├── qwen_desktop/           # Main package
│   ├── __init__.py         # Package init, version
│   ├── __main__.py         # Entry point (py -m qwen_desktop)
│   ├── app.py              # Application class
│   ├── ui/                 # UI components
│   │   ├── __init__.py
│   │   ├── main_window.py  # Main application window
│   │   ├── chat_widget.py  # Chat interface
│   │   ├── input_area.py   # Input field with attachments
│   │   ├── message_bubble.py  # Message display
│   │   ├── auth_dialog.py  # OAuth login dialog
│   │   ├── settings_dialog.py  # Settings UI
│   │   └── components/     # Reusable components
│   │       ├── __init__.py
│   │       ├── typing_indicator.py
│   │       └── conversation_sidebar.py
│   ├── core/               # Core logic
│   │   ├── __init__.py
│   │   ├── api_client.py   # Qwen API client
│   │   ├── conversation.py # Conversation management
│   │   └── conversation_manager.py  # Persistence
│   ├── auth/               # Authentication
│   │   ├── __init__.py
│   │   ├── oauth_handler.py  # OAuth flow
│   │   ├── token_manager.py  # Token storage/refresh
│   │   └── credentials.py    # Credential management
│   ├── attachments/        # File handling
│   │   ├── __init__.py
│   │   └── file_manager.py   # File operations
│   ├── config/             # Configuration
│   │   ├── __init__.py
│   │   ├── settings.py     # Settings management
│   │   └── defaults.py     # Default values
│   ├── utils/              # Utilities
│   │   ├── __init__.py
│   │   ├── logger.py       # Logging setup
│   │   ├── platform.py     # Platform detection
│   │   ├── file_encoder.py  # Base64 encoding
│   │   ├── rate_limiter.py  # Rate limiting
│   │   └── error_handler.py # Error classification
│   └── resources/          # Assets
│       ├── __init__.py
│       ├── icons/          # Icon files
│       └── styles/         # QSS stylesheets
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── test_auth.py
│   ├── test_attachments.py
│   ├── test_conversation.py
│   ├── test_error_handler.py
│   └── test_file_encoder.py
├── docs/                   # Documentation
│   ├── USER_GUIDE.md
│   ├── DEVELOPMENT.md
│   └── PLATFORM_TESTING.md
├── .planning/              # Project planning
│   ├── PROJECT.md
│   ├── REQUIREMENTS.md
│   ├── ROADMAP.md
│   └── STATE.md
├── pyproject.toml          # Python project config
├── requirements.txt        # Dependencies
├── requirements-dev.txt    # Dev dependencies
├── README.md               # Project readme
└── run.py                  # Development runner
```

---

## Building from Source

### Prerequisites

- Python 3.9+
- pip
- Git (optional)

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/qwen-desktop.git
cd qwen-desktop

# Create virtual environment (recommended)
py -m venv venv
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # macOS/Linux

# Install dependencies
py -m pip install -r requirements.txt

# Install dev dependencies
py -m pip install -r requirements-dev.txt
```

### Run Application

```bash
# Method 1: Using run.py
py run.py

# Method 2: As module
py -m qwen_desktop

# Method 3: Direct import
py -c "from qwen_desktop.app import QwenDesktopApp; import sys; app = QwenDesktopApp(sys.argv); app.run()"
```

### Build Distribution (Optional)

```bash
# Build wheel
py -m pip install build
py -m build

# Install locally
py -m pip install .
```

---

## Running Tests

### Run All Tests

```bash
py -m pytest tests/ -v
```

### Run Specific Test File

```bash
py -m pytest tests/test_auth.py -v
```

### Run Specific Test

```bash
py -m pytest tests/test_auth.py::TestCredentials::test_save_and_get_access_token -v
```

### Run with Coverage

```bash
py -m pytest tests/ --cov=qwen_desktop --cov-report=html
# Open htmlcov/index.html in browser
```

### Run Tests on File Change

```bash
# Install watchdog
py -m pip install watchdog

# Run with pytest-watch
py -m ptw
```

---

## Code Style Guide

### Python Version

- Target: Python 3.9+
- Type hints: Required for all public APIs

### Imports

Order:
1. Standard library
2. Third-party
3. Local imports

```python
# Correct
import json
from datetime import datetime
from pathlib import Path

import httpx
from PyQt6.QtWidgets import QWidget

from qwen_desktop.utils import logger
```

### Type Hints

```python
# Use Optional for nullable types
from typing import Optional

def get_token(self) -> Optional[str]:
    ...

# Use Union for multiple types
from typing import Union

def process(value: Union[str, int]) -> str:
    ...

# Use Literal for specific values
from typing import Literal

def set_status(status: Literal["ready", "loading", "error"]) -> None:
    ...
```

### Docstrings

Use Google style:

```python
def encode_file(file_path: str) -> Optional[dict]:
    """Encode file to base64 with metadata.
    
    Args:
        file_path: Path to file.
        
    Returns:
        Dictionary with encoded content and metadata, or None on error.
    """
    ...
```

### Naming Conventions

- **Classes:** PascalCase (`ConversationSidebar`)
- **Functions/Methods:** snake_case (`load_conversations`)
- **Constants:** UPPER_CASE (`MAX_FILE_SIZE`)
- **Private:** Leading underscore (`_internal_method`)

### Line Length

- Maximum: 100 characters
- Use black for auto-formatting: `py -m black .`

---

## Adding New Features

### New UI Component

1. Create file in `qwen_desktop/ui/components/`
2. Inherit from `QWidget` or appropriate Qt class
3. Add to `components/__init__.py`
4. Import and use in main window

**Example:**

```python
# qwen_desktop/ui/components/my_widget.py
from PyQt6.QtWidgets import QWidget

class MyWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        ...
```

### New Utility Function

1. Create file in `qwen_desktop/utils/`
2. Add to `utils/__init__.py`
3. Write tests in `tests/`

### New Test

1. Create `tests/test_<feature>.py`
2. Use pytest style
3. Aim for >80% coverage

**Example:**

```python
# tests/test_my_feature.py
import pytest
from qwen_desktop.utils.my_feature import my_function

def test_my_function_success():
    result = my_function("input")
    assert result == "expected"

def test_my_function_failure():
    result = my_function(None)
    assert result is None
```

---

## Debugging Tips

### Enable Debug Logging

```python
# In app.py or main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Debug PyQt6 Signals

```python
# Connect to signal and print
self.some_signal.connect(lambda x: print(f"Signal emitted: {x}"))
```

### Inspect Qt Objects

```python
# Print object tree
def print_tree(widget, indent=0):
    print(" " * indent + str(widget))
    for child in widget.children():
        print_tree(child, indent + 2)

print_tree(self.main_window)
```

### Debug Async Code

```python
# Add logging to async methods
import asyncio

async def chat(self, messages):
    logger.debug(f"Sending {len(messages)} messages")
    ...
```

### Common Issues

**Issue:** Application crashes on startup

**Debug:**
```bash
# Run with Python debugger
py -m pdb run.py
```

**Issue:** Signals not connecting

**Debug:**
```python
# Check signal/slot signatures match
print(self.signal.signal)
print(self.slot.__func__)
```

**Issue:** Memory leaks

**Debug:**
```python
# Use objgraph to find references
import objgraph
objgraph.show_most_common_types()
```

---

## Architecture Overview

### MVC Pattern

- **Model:** `Conversation`, `Message`, `Attachment`
- **View:** `MainWindow`, `ChatWidget`, `MessageBubble`
- **Controller:** `APIClient`, `ConversationManager`

### Event-Driven UI

- PyQt6 signals and slots
- Event filters for key handling
- QTimer for periodic updates

### Async API Calls

- `httpx.AsyncClient` for non-blocking I/O
- `async/await` for streaming responses
- QThread for background tasks

---

## Performance Tips

### Avoid UI Blocking

```python
# Bad: Blocks UI
def load_conversations(self):
    convs = self.manager.get_all()  # Slow!
    self.update_ui(convs)

# Good: Async
def load_conversations(self):
    self.loader = ConversationLoader(self.manager)
    self.loader.loaded.connect(self.update_ui)
    self.loader.start()
```

### Efficient Signal Connections

```python
# Bad: Creates many objects
for item in items:
    item.clicked.connect(lambda i=item: self.on_click(i))

# Good: Reuse handler
self.list_widget.itemClicked.connect(self.on_item_clicked)
```

### Memory Management

```python
# Clean up timers
def closeEvent(self, event):
    self.timer.stop()
    self.timer.deleteLater()
```

---

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Run tests
5. Submit PR

See [CONTRIBUTING.md](../CONTRIBUTING.md) for details.

---

## Resources

- [PyQt6 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [Python Documentation](https://docs.python.org/3/)
- [pytest Documentation](https://docs.pytest.org/)

---

**Happy Coding! 🚀**
