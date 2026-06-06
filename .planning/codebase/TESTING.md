# Testing Patterns

**Analysis Date:** 2026-06-06

## Test Framework

**Runner:**
- pytest >= 7.4.0
- Config in `pyproject.toml` under `[tool.pytest.ini_options]`:
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_functions = "test_*"
addopts = "-v --tb=short"
```

**Assertion Library:**
- Python built-in `assert` (pytest-native assertions)
- No external assertion library (no `assertpy`, no `hamcrest`)

**Run Commands:**
```bash
pytest                                  # Run all tests
pytest -v                               # Verbose output
pytest --tb=short                        # Shorter traceback
pytest tests/test_attachments.py        # Single test file
pytest -k test_encode                   # Run tests matching keyword
pytest --cov=qwen_desktop                # Coverage report
pytest -x                                # Stop on first failure
```

## Test File Organization

**Location:**
- All tests live in `tests/` directory (separate from source code, not co-located)
- One test file per source module/test area:
  - `tests/test_attachments.py` tests `qwen_desktop/attachments/`
  - `tests/test_auth.py` tests `qwen_desktop/auth/`
  - `tests/test_conversation.py` tests `qwen_desktop/core/conversation.py` and `qwen_desktop/core/models.py`
  - `tests/test_error_handler.py` tests `qwen_desktop/utils/error_handler.py`
  - `tests/test_file_encoder.py` tests `qwen_desktop/utils/file_encoder.py`

**Naming:**
- Test files: `test_<module_name>.py` (snake_case, e.g., `test_error_handler.py`)
- Test classes: `Test` + PascalCase module/class name (e.g., `TestClassifyError`, `TestGetUserMessage`, `TestFileManager`)
- Test methods: `test_` prefix + snake_case description (e.g., `test_auth_error_401`, `test_encode_text_file`)

**Structure:**
```
qwen-desktop/tests/
├── __init__.py              # """Tests package."""
├── test_attachments.py      # Tests for file_manager.py (122 lines)
├── test_auth.py             # Tests for auth/ (109 lines)
├── test_conversation.py     # Tests for core/conversation.py + models.py (185 lines)
├── test_error_handler.py    # Tests for utils/error_handler.py (125 lines)
└── test_file_encoder.py     # Tests for utils/file_encoder.py (174 lines)
```

## Test Structure

**Suite Organization:**
```python
"""Tests for error handling utilities."""

import pytest
import httpx

from qwen_desktop.utils.error_handler import (
    ErrorType,
    classify_error,
    get_user_message,
    get_suggested_action,
)


class TestClassifyError:
    """Test error classification."""

    def test_auth_error_401(self):
        """Test 401 classified as auth error."""
        error_type = classify_error(status_code=401)
        assert error_type == ErrorType.AUTH_ERROR

    def test_network_error(self):
        """Test network error classified correctly."""
        error = httpx.ConnectError("Connection failed")
        error_type = classify_error(error=error)
        assert error_type == ErrorType.NETWORK_ERROR


class TestGetUserMessage:
    """Test user-friendly error messages."""

    def test_auth_error_message(self):
        """Test auth error message."""
        msg = get_user_message(ErrorType.AUTH_ERROR)
        assert "Authentication failed" in msg
        assert "log in again" in msg
```

**Patterns:**
- Class-based grouping: each test class (`Test*`) tests one function or module
- Class docstring describes what's being tested
- Each test method has descriptive one-line docstring
- No `setup_method` / `teardown_method` used (no pytest fixtures either)
- No shared state between tests — each method is self-contained
- Tests do not use pytest fixtures (no `@pytest.fixture` decorator found)

## Mocking

**Framework:** `unittest.mock` (stdlib, no pytest-mock)

**Patterns:**
```python
from unittest.mock import Mock, patch, MagicMock

from qwen_desktop.auth.oauth_handler import OAuthHandler
from qwen_desktop.auth.token_manager import TokenManager
from qwen_desktop.auth.credentials import Credentials


class TestOAuthHandler:
    """Test OAuth handler."""

    def test_init_default_values(self):
        """Test OAuth handler initialization."""
        handler = OAuthHandler()
        assert handler.redirect_uri == "http://localhost:8080/callback"
        assert handler.scopes == "openid profile email model.completion"
```

**What to Mock:**
- External dependencies (OAuth handlers, token managers, credentials storage)
- No `patch` or `mock` usage in current tests for `test_error_handler.py`, `test_attachments.py`, `test_file_encoder.py` (these use real modules)

**What NOT to Mock:**
- Pure functions with deterministic outputs (error classification, file encoding, string processing)
- Dataclasses and simple value objects
- File system operations to real temp files

## Fixtures and Factories

**Test Data:**
- Test data created inline using literals and dictionaries
- No factory functions or fixture files
- No shared test data directory

```python
# Inline dictionary test data (test_conversation.py)
data = {
    "id": "test-id",
    "title": "Test Chat",
    "messages": [
        {"content": "Hello", "role": "user", "timestamp": "2024-01-01T12:00:00"}
    ],
    "created_at": "2024-01-01T12:00:00",
    "updated_at": "2024-01-01T12:00:00",
    "model": "qwen-plus",
}
```

```python
# Direct instantiation (test_attachments.py)
attachment = Attachment(file_path="/path/to/file.py")
assert attachment.name == "file.py"
assert attachment.file_type == ".py"
```

**Temporary File Creation:**
```python
# Using tempfile (test_file_encoder.py)
with tempfile.NamedTemporaryFile(
    mode="w", suffix=".txt", delete=False
) as f:
    f.write("Hello, World!")
    temp_path = f.name

try:
    result = encode_file(temp_path)
    assert result is not None
    assert result["size"] == 13
finally:
    Path(temp_path).unlink()
```

**Location:**
- All test data defined inline within the test method
- No shared fixtures file or factories directory
- Cleanup via `try/finally` block with `Path(temp_path).unlink()`

## Coverage

**Requirements:**
- No enforced coverage target
- `pytest-cov` listed as dev dependency in `pyproject.toml`
- No `.coveragerc` or coverage configuration file found
- No coverage thresholds or CI enforcement detected

**Configuration:**
- Run coverage via: `pytest --cov=qwen_desktop tests/`
- No exclusions configured

**View Coverage:**
```bash
pytest --cov=qwen_desktop tests/         # Terminal report
pytest --cov=qwen_desktop --cov-report=html tests/   # HTML report
```

## Test Types

**Unit Tests:**
- Only unit tests detected in the codebase
- Test single functions/modules in isolation
- Test real module logic without mocking internals
- No external service calls in tests
- Fast execution (each test <100ms)
- Examples: `test_error_handler.py`, `test_file_encoder.py`, `test_attachments.py`

**Integration Tests:**
- Not present. No integration tests detected.

**E2E Tests:**
- Not present. No E2E tests detected.

## Common Patterns

**Async Testing:**
- No async tests currently in the codebase
- `pytest-asyncio` is listed as a dev dependency in `requirements-dev.txt` but not used yet
- Async code (e.g., `APIClient.send_message`, `ZenClient.test_connection`) is not currently tested

**Error Testing:**
```python
def test_auth_error_401(self):
    """Test 401 classified as auth error."""
    error_type = classify_error(status_code=401)
    assert error_type == ErrorType.AUTH_ERROR

def test_validate_file_not_exists(self):
    """Test validation of non-existent file."""
    manager = FileManager()
    is_valid, error = manager.validate_file("/nonexistent/file.py")
    assert not is_valid
    assert "does not exist" in error
```

**File System Testing:**
```python
def test_encode_text_file(self):
    """Test encoding a text file."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False
    ) as f:
        f.write("Hello, World!")
        temp_path = f.name
    try:
        result = encode_file(temp_path)
        assert result is not None
        assert result["name"].endswith(".txt")
        assert result["size"] == 13
        assert "content" in result
    finally:
        Path(temp_path).unlink()
```

**Snapshot Testing:**
- Not used in this codebase

**Property-Based Testing:**
- Not used (`hypothesis` not in dependencies)

---

*Testing analysis: 2026-06-06*
*Update when test patterns change*
