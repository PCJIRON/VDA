# Technology Stack

**Project:** Qwen Desktop  
**Version:** 0.4.0

---

## Runtime & Language

### Python
- **Version:** >=3.9.0
- **Environment:** Standard `venv` recommended

---

## Frontend / UI

### Desktop GUI
- **Framework:** PyQt6
- **Version:** >=6.4.0
- **Features Used:** QMainWindow, QWidget, QThread, signals/slots, custom styling.

---

## Backend / Core

### HTTP & API Client
- **Requests:** Used for all HTTP traffic (API calls, OAuth exchanges)
- **urllib.parse:** For URL manipulation.

### File System
- **Pathlib:** Used heavily for cross-platform path management.
- **base64:** File content encoding for API submission.
- **mimetypes:** Content type discovery for attachments.

### Authentication & Secrets
- **OAuth 2.0:** Integrated device code flow and browser-based OAuth.
- **keyring:** Secure token storage using the host OS credential manager.

---

## Development Tools

### Testing
- **pytest:** Primary test runner
- **pytest-cov:** Code coverage reporting
- **unittest.mock:** Mocking for unit tests

### Code Quality
- **black:** Code formatting and styling
- **ruff:** Linter
- **mypy:** Static type checking

## Packaging
- **setuptools / wheel:** Standard python build tools for distribution.
