# Coding Conventions

**Analysis Date:** 2026-06-06

## Naming Patterns

**Files:**
- snake_case for all Python files (`file_manager.py`, `error_handler.py`, `api_client.py`)
- One module per file with focused responsibility
- `__init__.py` for barrel exports in each package directory

**Functions:**
- snake_case for all functions and methods (`setup_logger`, `classify_error`, `get_user_message`)
- No special prefix for async functions (Python `async def` is its own marker)
- Private/helper methods use single underscore prefix: `_get_headers`, `_create_client`, `_load`, `_resolve_path`
- Class methods use `@classmethod` decorator: `from_api_response`, `get_default_models`, `get_provider_models`

**Variables:**
- snake_case for module-level, local, and instance variables
- Module-level logger instance: `logger = logging.getLogger(__name__)` (`qwen_desktop/utils/error_handler.py`)
- No special prefix for instance variables (except `self._` for private/protected)

**Constants:**
- UPPER_SNAKE_CASE for module-level constants: `MAX_FILE_SIZE`, `THINKING_PATTERNS`, `MEMORY_DIR`, `DEFAULT_SETTINGS`, `PROVIDERS` (`qwen_desktop/config/defaults.py`, `qwen_desktop/utils/file_encoder.py`)

**Types:**
- PascalCase for class names (`DesktopApp`, `Settings`, `APIClient`, `SessionService`, `ToolExecutor`) — `qwen_desktop/app.py`, `qwen_desktop/config/settings.py`
- PascalCase for dataclasses: `ModelInfo`, `TokenUsage`, `Attachment`, `SlashCommand` — `qwen_desktop/core/models.py`, `qwen_desktop/attachments/file_manager.py`, `qwen_desktop/core/command_registry.py`
- PascalCase for enums: `ErrorType` with UPPER_CASE values: `AUTH_ERROR`, `RATE_LIMIT` — `qwen_desktop/utils/error_handler.py`
- Type aliases use PascalCase: `Platform = Literal["windows", "macos", "linux", "other"]` — `qwen_desktop/utils/platform.py`

## Code Style

**Formatting:**
- Black formatter configured in `pyproject.toml` with `line-length = 100` and `target-version = ["py39", "py310", "py311", "py312"]`
- Ruff linter configured with `line-length = 100`, `target-version = "py39"`
- 100 character line length maximum
- Double quotes not enforced (mixed usage observed — single and double quotes both appear)
- 4-space indentation (Python standard)

**Linting:**
- Ruff: `select = ["E", "F", "W", "I", "N", "D", "UP"]`, `ignore = ["D100", "D104"]` — `pyproject.toml`
- MyPy configured: `python_version = "3.9"`, `warn_return_any = true`, `disallow_untyped_defs = false`, `check_untyped_defs = true` — `pyproject.toml`
- Not enforced in CI (added as dev dependency only)
- Run: `ruff check .`, `mypy qwen_desktop`, `black --check .`

## Import Organization

**Order:**
1. Standard library (os, sys, json, logging, pathlib, re, etc.)
2. Third-party packages (PyQt6, httpx, pytest, etc.)
3. Local package imports (`qwen_desktop.xxx`)

**Grouping:**
- Blank line between standard library and third-party imports, and between third-party and local imports
- Alphabetical within groups
- `from` imports before simple `import` statements within groups

**Path Aliases:**
- No path aliases; all local imports use full package path: `from qwen_desktop.config.settings import Settings`
- Examples: `from qwen_desktop.utils.logger import setup_logger` (`qwen_desktop/app.py`), `from qwen_desktop.auth.provider_config import ProviderConfig` (`qwen_desktop/core/api_client.py`)

## Type Hints

**Requirements:**
- Type hints required for all function parameters and return types
- Module-level: `from typing import Optional, List, Dict, Any, Tuple`
- Modern syntax (`list[str]`, `dict[str, Any]`) used in many files (Python 3.9+ compatible)
- `Optional[X]` used for nullable values
- Return types always annotated, including `-> None` for void functions

**Patterns observed:**
```python
# From qwen_desktop/utils/logger.py
def setup_logger(
    name: str = "qwen_desktop",
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
) -> logging.Logger:

# From qwen_desktop/utils/error_handler.py
def classify_error(
    status_code: Optional[int] = None,
    error: Optional[Exception] = None,
) -> ErrorType:

# From qwen_desktop/core/api_client.py
async def send_message(
    self,
    message: str,
    conversation_history: List[Dict[str, Any]],
    attachments: Optional[List] = None,
    vision_mode: bool = False,
) -> AsyncGenerator[str, None]:
```

## Error Handling

**Patterns:**
- Custom exception classes defined when needed: `class AuthenticationError(Exception):` (`qwen_desktop/core/api_client.py:15`)
- Try/except with specific exception types; broad `except Exception` only at top-level boundaries
- Centralized error classification via `classify_error()` — `qwen_desktop/utils/error_handler.py`
- Service methods often return error message strings rather than raising exceptions (e.g., `ToolExecutor.execute_tool` returns `f"Error: ..."` — `qwen_desktop/core/tool_executor.py:149`)
- Async generators yield error messages as strings: `yield f"Error: API returned {response.status_code}."` (`qwen_desktop/core/api_client.py:142`)
- Use `exc_info=True` with `logger.error()` to capture stack traces (`qwen_desktop/app.py:46`, `qwen_desktop/core/session_service.py:36`)
- Bare `except:` or `except Exception` used in some session deserialization as short-circuit (`qwen_desktop/core/session_service.py:62`)
- `try/finally` pattern for cleanup (e.g., `client.aclose()` in finally blocks — `qwen_desktop/core/api_client.py:71`)

## Logging

**Framework:** Python `logging` module

**Setup:** Centralized `setup_logger()` function — `qwen_desktop/utils/logger.py`

**Levels:** `DEBUG`, `INFO`, `ERROR` (warn not observed in practice)

**Patterns:**
- Module-level logger: `logger = logging.getLogger(__name__)` (every module)
- Structured format: `"%(asctime)s - %(name)s - %(levelname)s - %(message)s"`
- Log at service boundaries and external API calls
- Include error context: `logger.error(f"Application error: {e}", exc_info=True)` (`qwen_desktop/app.py:46`)
- Custom prefixes in log messages: `"[STM] Task started: ..."` (`qwen_desktop/core/memory_manager.py:31`), `"[UIA] UI Automation loaded successfully"` (`qwen_desktop/ui/floating_assistant.py:39`)
- No `print()` statements in production code (only `print()` found in `file_encoder.py` line 49 in an error path; should use logger)

## Comments

**When to Comment:**
- Module-level docstring explaining purpose at top of every `.py` file
- Docstrings for all public functions and methods (Google-style)
- Inline comments for non-obvious logic, regular expressions, workarounds
- Class docstrings explaining purpose

**Docstring Style (Google):**
```python
# From qwen_desktop/utils/error_handler.py
def classify_error(
    status_code: Optional[int] = None,
    error: Optional[Exception] = None,
) -> ErrorType:
    """Classify an error based on status code or exception type.
    
    Args:
        status_code: HTTP status code if available.
        error: Exception that was raised.
        
    Returns:
        ErrorType classification.
    """

# From qwen_desktop/attachments/file_manager.py
@property
def size_formatted(self) -> str:
    """Get formatted file size.
    
    Returns:
        Human-readable file size.
    """
```

**TODO Comments:** None found in the codebase.

## Function Design

**Size:**
- Most functions under 50-60 lines
- Complex operations extracted into helper methods
- One level of abstraction per function

**Parameters:**
- Max 4-5 parameters before using an options/settings object
- Default parameter values for optional arguments
- Type hints on all parameters

**Return Values:**
- Explicit return statements with annotated return types
- Return early for guard clauses (`if not path.exists(): return None` in `qwen_desktop/utils/file_encoder.py:28`)
- Return `None` for expected error states (not exceptions) in utility functions
- `Tuple[bool, str]` for validation results (`is_valid, error = manager.validate_file(...)`) — `qwen_desktop/attachments/file_manager.py:104`

## Module Design

**Exports:**
- Each package has an `__init__.py` that imports and re-exports the public API
- `__all__` lists defined in `__init__.py`:
  - `qwen_desktop/utils/__init__.py`: `["setup_logger", "get_platform", "is_windows", "is_macos", "is_linux"]`
  - `qwen_desktop/core/__init__.py`: `["APIClient", "ZenClient", "ModelInfo", "CommandRegistry", "SessionService"]`

**Barrel Files:**
- `__init__.py` used as barrel files for package re-exports
- Internal helpers kept private (not exported from `__init__.py`)

**Package Structure:**
```
qwen_desktop/
├── __init__.py          # Package metadata: version, author
├── __main__.py          # Entry point: py -m qwen_desktop
├── app.py               # DesktopApp class
├── attachments/         # File attachment handling
│   ├── __init__.py
│   └── file_manager.py
├── auth/                # Authentication
│   ├── __init__.py
│   └── provider_config.py
├── config/              # Configuration
│   ├── __init__.py
│   ├── defaults.py      # DEFAULT_SETTINGS, PROVIDERS
│   └── settings.py      # Settings class
├── core/                # Core business logic
│   ├── __init__.py
│   ├── api_client.py
│   ├── ... (25+ modules)
├── resources/           # Application resources (icons)
│   ├── __init__.py
│   └── icons/
├── ui/                  # UI components
│   ├── components/      # Button widgets
│   ├── floating_assistant.py (~1988 lines)
│   ├── settings_dialog.py
│   └── uied_overlay.py
└── utils/               # Utilities
    ├── __init__.py
    ├── error_handler.py
    ├── file_encoder.py
    ├── logger.py
    └── platform.py
```

---

*Convention analysis: 2026-06-06*
*Update when patterns change*
