# Codebase Map

**Generated:** 2026-03-29  
**Project:** qwen_desktop (Qwen Code Desktop + Terminal)

---

## Overview

This is a **dual-stack project** containing:
1. **Qwen Code CLI** - TypeScript-based AI terminal agent (main codebase)
2. **Qwen Desktop** - Python PyQt6 desktop GUI application

---

## Stack

### Languages
- **TypeScript 5.3+** (primary - CLI, core logic, web UI)
- **Python 3.9+** (desktop GUI application)
- **JavaScript/JSX** (React components for web UI)

### Frameworks & Libraries

#### TypeScript Stack
| Category | Technology |
|----------|------------|
| Runtime | Node.js 20+ |
| UI Framework (CLI) | Ink 6.x + React 19.x |
| UI Framework (Web) | React 19.x + Vite |
| Build Tool | esbuild, Vite |
| Testing | Vitest 3.x |
| Linting | ESLint 9.x + Prettier 3.x |
| Package Manager | npm (workspaces) |

#### Python Stack
| Category | Technology |
|----------|------------|
| GUI Framework | PyQt6 6.4+ |
| HTTP Client | httpx, requests |
| Markdown | markdown, pygments |
| Testing | pytest, pytest-qt |
| Linting | ruff, black, mypy |

### AI/Model Integration
- **Qwen Models** (primary): qwen3-coder-plus, qwen3.5-plus
- **OpenAI-compatible API** support
- **Anthropic Claude** support
- **Google Gemini** support
- **OAuth authentication** (Qwen free tier: 1000 requests/day)

### Database/Storage
- **File-based storage** (JSON config files)
- **Keyring** for credential storage (Python)
- **Local storage** for session data

---

## Architecture

### Monorepo Structure

```
qwen_desktop/
├── qwen-code/                    # TypeScript CLI (main codebase)
│   ├── packages/
│   │   ├── cli/                  # Main CLI entry point (Ink/React UI)
│   │   ├── core/                 # Core backend logic, tools, agents
│   │   ├── sdk-typescript/       # TypeScript SDK
│   │   ├── sdk-java/             # Java SDK
│   │   ├── webui/                # Web UI components (Storybook)
│   │   ├── vscode-ide-companion/ # VS Code extension
│   │   ├── zed-extension/        # Zed editor extension
│   │   ├── test-utils/           # Shared testing utilities
│   │   └── web-templates/        # HTML export templates
│   ├── scripts/                  # Build & utility scripts
│   ├── integration-tests/        # E2E tests
│   └── docs-site/                # Next.js documentation
│
├── qwen-desktop/                 # Python Desktop App
│   ├── qwen_desktop/
│   │   ├── core/                 # API client, tools, session management
│   │   ├── ui/                   # PyQt6 widgets & components
│   │   ├── auth/                 # OAuth, token management
│   │   ├── config/               # Settings, defaults
│   │   ├── utils/                # Utilities (logging, platform)
│   │   └── resources/            # Static assets
│   ├── tests/                    # pytest tests
│   └── run.py                    # Entry point
│
└── VDA/                          # Legacy/variant desktop app
    └── qwen-desktop/             # Duplicate/similar codebase
```

### Entry Points

| Package | Entry Point | Description |
|---------|-------------|-------------|
| CLI | `packages/cli/src/gemini.tsx` | Interactive terminal UI |
| CLI Headless | `packages/cli/src/nonInteractiveCli.ts` | Non-interactive mode |
| Core | `packages/core/src/index.ts` | Core library exports |
| WebUI | `packages/webui/src/index.ts` | Shared React components |
| Desktop | `qwen-desktop/run.py` | PyQt6 GUI application |
| Desktop Main | `qwen-desktop/qwen_desktop/__main__.py` | Python module entry |

### Module Structure

#### Core Modules (TypeScript)
```
packages/core/src/
├── tools/           # File ops, shell, web fetch, LSP, MCP
├── agents/          # Agent orchestration
├── subagents/       # Task delegation
├── skills/          # Reusable skill system
├── models/          # Model configuration & registry
├── config/          # Configuration management
├── services/        # Git, file discovery, sessions
├── mcp/             # Model Context Protocol
├── lsp/             # Language Server Protocol
├── permissions/     # Permission system
└── telemetry/       # OpenTelemetry integration
```

#### Desktop Modules (Python)
```
qwen_desktop/
├── core/
│   ├── api_client.py         # Qwen API communication
│   ├── tool_executor.py      # Tool execution
│   ├── conversation_manager.py
│   └── qwen_session_service.py
├── ui/
│   ├── main_window.py        # Main application window
│   ├── chat_widget.py        # Chat interface
│   ├── input_area.py         # User input
│   ├── components/           # Reusable PyQt6 widgets
│   └── floating_assistant.py # Floating window mode
├── auth/
│   ├── oauth_handler.py      # OAuth flow
│   ├── token_manager.py      # Token storage/refresh
│   └── credentials.py        # Credential management
└── config/
    ├── settings.py           # User settings
    └── defaults.py           # Default values
```

---

## Conventions

### TypeScript Conventions

| Aspect | Convention |
|--------|------------|
| **Naming** | camelCase (variables), PascalCase (types/classes), UPPER_CASE (constants) |
| **File Organization** | Feature-based directories, index.ts for exports |
| **Imports** | Absolute paths from package src/, ES modules (`import/export`) |
| **Tests** | `*.test.ts` alongside source, Vitest framework |
| **Code Style** | Strict TypeScript, no implicit any, prettier formatting |
| **Comments** | JSDoc for public APIs, minimal inline comments |

### Python Conventions

| Aspect | Convention |
|--------|------------|
| **Naming** | snake_case (variables/functions), PascalCase (classes) |
| **File Organization** | Module-based packages, `__init__.py` exports |
| **Imports** | Relative within package, absolute for external |
| **Tests** | `test_*.py` in tests/ directory, pytest framework |
| **Code Style** | PEP 8, black formatting (100 char line length), ruff linting |
| **Type Hints** | Gradual typing with mypy validation |

### Git Conventions
- **Branch Naming**: feature/*, bugfix/*, release/*
- **Commit Messages**: Conventional Commits format
- **PR Reviews**: Required before merge

---

## Concerns

### ⚠️ Technical Debt

1. **Duplicate Code**: `VDA/` directory contains duplicate/similar code to `qwen-desktop/`
2. **Large Package Count**: 10 packages may be over-engineered for current scope
3. **Build Complexity**: Multiple build systems (esbuild, Vite, setuptools)

### ⚠️ Testing Gaps

1. **Auth Module**: Limited test coverage for OAuth flows
2. **Integration Tests**: Heavy reliance on E2E tests, slower feedback
3. **Desktop Tests**: PyQt6 GUI tests require display (X11/Xvfb)

### ⚠️ Dependency Concerns

1. **Outdated Dependencies**: Check `package.json` for outdated npm packages
2. **Optional Dependencies**: Many platform-specific @lydell/node-pty packages
3. **Python Dependencies**: PyQt6 version lock may cause issues

### ℹ️ Recommendations

1. **Consolidate VDA**: Merge or remove duplicate VDA directory
2. **Update Dependencies**: Run `npm outdated` and `pip list --outdated`
3. **Add Unit Tests**: Increase unit test coverage for core modules
4. **Document APIs**: Add more JSDoc/pydoc for public interfaces
5. **Consider ES Modules**: Python project could use modern packaging (pyproject.toml already in place)

---

## Quick Reference

### Common Commands

#### TypeScript/CLI
```bash
npm install              # Install dependencies
npm run build            # Build all packages
npm run dev              # Development mode
npm run test             # Run tests
npm run lint             # Lint code
npm run format           # Format with prettier
npm run start            # Start CLI (qwen)
```

#### Python/Desktop
```bash
pip install -e .         # Install in dev mode
python run.py            # Run desktop app
pytest                   # Run tests
black .                  # Format code
ruff check .             # Lint code
```

### Configuration Files

| File | Purpose |
|------|---------|
| `~/.qwen/settings.json` | User-wide Qwen settings |
| `.qwen/settings.json` | Project-specific settings |
| `qwen-desktop/pyproject.toml` | Python package config |
| `qwen-code/package.json` | Root npm workspace config |
| `qwen-code/tsconfig.json` | TypeScript compiler options |

---

## Next Steps

After codebase analysis, you can:

1. **Run `/gsd:new-project`** to start a new milestone with this context
2. **Explore specific areas**: auth, api, frontend, tools
3. **Address concerns**: Update dependencies, add tests, refactor duplicates

---

**Analysis Complete** ✅
