# Technology Stack

**Project:** qwen_desktop  
**Generated:** 2026-03-29

---

## Executive Summary

This is a **dual-stack AI agent project** with:
- **TypeScript CLI** - Terminal-based AI coding assistant
- **Python Desktop** - PyQt6 graphical desktop application

Both applications interface with Qwen AI models and share similar authentication/authorization flows.

---

## Core Technologies

### Runtime Environments

| Runtime | Version | Purpose |
|---------|---------|---------|
| **Node.js** | >=20.0.0 (recommended: 20.19.0) | TypeScript CLI execution |
| **Python** | >=3.9 (tested: 3.9-3.12) | Desktop GUI application |

---

## TypeScript Stack (qwen-code)

### Language & Type System

```json
{
  "typescript": "^5.3.3",
  "compilerOptions": {
    "strict": true,
    "module": "NodeNext",
    "moduleResolution": "nodenext",
    "target": "es2022",
    "lib": ["ES2023"],
    "jsx": "react-jsx"
  }
}
```

**Key Features:**
- Strict mode enabled (noImplicitAny, strictNullChecks, etc.)
- ES modules (NodeNext)
- ES2023 target
- React JSX support

### Frontend/UI Libraries

#### CLI Terminal UI
| Package | Version | Purpose |
|---------|---------|---------|
| `ink` | ^6.2.3 | React renderer for terminal |
| `react` | ^19.1.0 | UI component framework |
| `react-dom` | ^19.1.0 | React DOM (for web components) |
| `ink-spinner` | ^5.0.0 | Loading indicators |
| `ink-gradient` | ^3.0.0 | Gradient text effects |
| `ink-link` | ^4.1.0 | Clickable links |

#### Web UI Components
| Package | Version | Purpose |
|---------|---------|---------|
| `vite` | ^5.0.0 | Build tool for web UI |
| `@vitejs/plugin-react` | ^4.2.0 | React plugin for Vite |
| `tailwindcss` | ^3.4.0 | Utility-first CSS |
| `storybook` | ^10.1.11 | Component development environment |
| `markdown-it` | ^14.1.0 | Markdown rendering |

### Backend/Core Libraries

#### AI/Model Integration
| Package | Version | Purpose |
|---------|---------|---------|
| `@google/genai` | 1.30.0 | Google GenAI API client |
| `@anthropic-ai/sdk` | ^0.36.1 | Anthropic Claude API |
| `openai` | 5.11.0 | OpenAI API client |
| `google-auth-library` | ^10.5.0 | Google OAuth authentication |

#### Protocol Support
| Package | Version | Purpose |
|---------|---------|---------|
| `@modelcontextprotocol/sdk` | ^1.25.1 | Model Context Protocol (MCP) |
| `@agentclientprotocol/sdk` | ^0.14.1 | Agent Client Protocol |

#### File & System Operations
| Package | Version | Purpose |
|---------|---------|---------|
| `glob` | ^10.5.0 | File pattern matching |
| `chokidar` | ^4.0.3 | File watching |
| `ignore` | ^7.0.0 | .gitignore parsing |
| `picomatch` | ^4.0.1 | Glob pattern matching |
| `simple-git` | ^3.28.0 | Git operations |
| `tar` | ^7.5.2 | Tar archive handling |
| `extract-zip` | ^2.0.1 | ZIP extraction |

#### Terminal & Process Management
| Package | Version | Purpose |
|---------|---------|---------|
| `@lydell/node-pty` | 1.1.0 | Pseudo-terminal (cross-platform) |
| `ansi-regex` | ^6.2.2 | ANSI escape code parsing |
| `strip-ansi` | ^7.1.0 | Remove ANSI codes |
| `wrap-ansi` | 9.0.2 | Text wrapping with ANSI |
| `string-width` | ^7.1.0 | String width calculation |

#### Configuration & Parsing
| Package | Version | Purpose |
|---------|---------|---------|
| `@iarna/toml` | ^2.2.5 | TOML parsing |
| `comment-json` | ^4.2.5 | JSON with comments |
| `yaml` | (via webui) | YAML parsing |
| `zod` | ^3.23.8 | Schema validation |
| `ajv` | ^8.17.1 | JSON Schema validation |
| `jsonrepair` | ^3.13.0 | Fix malformed JSON |

#### Networking & HTTP
| Package | Version | Purpose |
|---------|---------|---------|
| `undici` | ^6.22.0 | HTTP/1.1 & HTTP/2 client |
| `https-proxy-agent` | ^7.0.6 | Proxy support |
| `ws` | ^8.18.0 | WebSocket support |
| `open` | ^10.1.2 | Open URLs/files in browser |

#### Text Processing & Syntax Highlighting
| Package | Version | Purpose |
|---------|---------|---------|
| `marked` | ^15.0.12 | Markdown parsing |
| `highlight.js` | ^11.11.1 | Syntax highlighting |
| `lowlight` | ^3.3.0 | Lowlight syntax highlighting |
| `chardet` | ^2.1.0 | Character encoding detection |
| `iconv-lite` | ^0.6.3 | Character encoding conversion |
| `html-to-text` | ^9.0.5 | HTML to text conversion |

#### Utilities
| Package | Version | Purpose |
|---------|---------|---------|
| `diff` | ^7.0.0 | Diff/patch generation |
| `fast-levenshtein` | ^2.0.6 | String similarity |
| `mnemonist` | ^0.40.3 | Data structures |
| `fdir` | ^6.4.6 | Fast directory traversal |
| `fzf` | ^0.5.2 | Fuzzy search |
| `async-mutex` | ^0.5.0 | Async locking |
| `uuid` | ^9.0.1 | UUID generation |

#### CLI & User Interaction
| Package | Version | Purpose |
|---------|---------|---------|
| `yargs` | ^17.7.2 | Command-line argument parsing |
| `prompts` | ^2.4.2 | Interactive prompts |
| `command-exists` | ^1.2.9 | Check command availability |
| `shell-quote` | ^1.8.3 | Shell command parsing |
| `update-notifier` | ^7.3.1 | npm update notifications |

#### Telemetry & Observability
| Package | Version | Purpose |
|---------|---------|---------|
| `@opentelemetry/api` | ^1.9.0 | OpenTelemetry API |
| `@opentelemetry/sdk-node` | ^0.203.0 | OTel SDK |
| `@opentelemetry/instrumentation-http` | ^0.203.0 | HTTP instrumentation |
| `@opentelemetry/exporter-trace-otlp-http` | ^0.203.0 | Trace export |
| `@opentelemetry/exporter-metrics-otlp-http` | ^0.203.0 | Metrics export |

### Development Dependencies

#### Testing
| Package | Version | Purpose |
|---------|---------|---------|
| `vitest` | ^3.1.1 | Unit testing framework |
| `@vitest/coverage-v8` | ^3.1.1 | Code coverage |
| `@vitest/eslint-plugin` | ^1.3.4 | ESLint plugin for tests |
| `memfs` | ^4.42.0 | In-memory file system (mocking) |
| `mock-fs` | ^5.5.0 | File system mocking |
| `msw` | ^2.10.4 | API mocking |
| `jsdom` | ^26.1.0 | DOM simulation |
| `ink-testing-library` | ^4.0.0 | Ink component testing |
| `@testing-library/react` | ^16.3.0 | React testing utilities |

#### Linting & Formatting
| Package | Version | Purpose |
|---------|---------|---------|
| `eslint` | ^9.24.0 | Linting |
| `typescript-eslint` | ^8.30.1 | TypeScript ESLint |
| `eslint-config-prettier` | ^10.1.2 | Prettier compatibility |
| `eslint-plugin-react` | ^7.37.5 | React linting |
| `eslint-plugin-react-hooks` | ^5.2.0 | React Hooks linting |
| `eslint-plugin-import` | ^2.31.0 | Import statement linting |
| `prettier` | ^3.5.3 | Code formatting |
| `husky` | ^9.1.7 | Git hooks |
| `lint-staged` | ^16.1.6 | Staged file linting |

#### Build Tools
| Package | Version | Purpose |
|---------|---------|---------|
| `esbuild` | ^0.25.0 | Fast bundler |
| `tsx` | ^4.20.3 | TypeScript execution |
| `cross-env` | ^7.0.3 | Cross-platform env vars |
| `npm-run-all` | ^4.1.5 | Parallel script running |

---

## Python Stack (qwen-desktop)

### Language & Type System

```toml
[tool.black]
line-length = 100
target-version = ["py39", "py310", "py311", "py312"]

[tool.mypy]
python_version = "3.9"
warn_return_any = true
check_untyped_defs = true
```

**Key Features:**
- Gradual typing with mypy
- PEP 8 compliant
- Black formatting (100 char lines)

### GUI Framework

| Package | Version | Purpose |
|---------|---------|---------|
| `PyQt6` | >=6.4.0 | Desktop GUI framework |
| `pytest-qt` | >=4.2.0 | Qt testing utilities |

### HTTP & Networking

| Package | Version | Purpose |
|---------|---------|---------|
| `httpx` | >=0.25.0 | Async HTTP client |
| `requests` | >=2.31.0 | Sync HTTP client |
| `requests-oauthlib` | >=1.3.1 | OAuth authentication |

### Authentication & Security

| Package | Version | Purpose |
|---------|---------|---------|
| `keyring` | >=24.0.0 | Secure credential storage |
| `python-dotenv` | >=1.0.0 | Environment variable management |

### Text Processing

| Package | Version | Purpose |
|---------|---------|---------|
| `markdown` | >=3.5.0 | Markdown rendering |
| `pygments` | >=2.17.0 | Syntax highlighting |
| `pyyaml` | >=6.0.0 | YAML parsing |

### Development Dependencies

#### Testing
| Package | Version | Purpose |
|---------|---------|---------|
| `pytest` | >=7.4.0 | Testing framework |
| `pytest-cov` | >=4.1.0 | Coverage reporting |
| `pytest-qt` | >=4.2.0 | Qt widget testing |

#### Linting & Formatting
| Package | Version | Purpose |
|---------|---------|---------|
| `black` | >=23.0.0 | Code formatter |
| `ruff` | >=0.1.0 | Fast linter |
| `mypy` | >=1.5.0 | Static type checker |

---

## Build & Deployment

### TypeScript Build Chain

```
Source (.ts/.tsx) 
  → esbuild/Vite 
  → dist/ (.js, .d.ts, .css) 
  → npm package
```

**Build Tools:**
- **esbuild**: Primary bundler (CLI, core)
- **Vite**: Web UI bundler
- **TypeScript Compiler**: Type checking, declaration files

### Python Build Chain

```
Source (.py) 
  → setuptools (pyproject.toml) 
  → dist/ (.whl, .tar.gz) 
  → pip installable package
```

**Build Tools:**
- **setuptools**: Package building
- **wheel**: Binary distribution

### Deployment Targets

| Target | Platform | Method |
|--------|----------|--------|
| npm Registry | Global | `npm publish` |
| PyPI | Global | `twine upload` |
| Docker | Container | `docker build/push` |
| GitHub Releases | All | Automated via CI |

---

## Database & Storage

### Configuration Storage

| Type | Location | Format |
|------|----------|--------|
| User Settings | `~/.qwen/settings.json` | JSON |
| Project Settings | `.qwen/settings.json` | JSON |
| Credentials | System keyring | OS-specific |
| Session Data | Local temp files | JSON |

### No Database Required

This is a **stateless agent** that:
- Stores configuration in JSON files
- Uses OS keyring for sensitive data
- Maintains session state in memory
- Persists conversation history locally (optional)

---

## External Services

### AI Model Providers

| Provider | Protocol | Models |
|----------|----------|--------|
| Qwen (Dashscope) | OpenAI-compatible | qwen3-coder-*, qwen3.5-* |
| Alibaba Cloud ModelStudio | OpenAI-compatible | Multiple vendors |
| Anthropic | Native API | claude-* |
| Google | GenAI API | gemini-* |
| OpenAI | Native API | gpt-* |

### Authentication Methods

1. **Qwen OAuth** - Free tier (1000 requests/day)
2. **API Key** - Pay-per-use with any provider

---

## Version Compatibility Matrix

### Node.js Versions

| Node Version | Status | Notes |
|--------------|--------|-------|
| 18.x | ❌ Unsupported | EOL |
| 20.x | ✅ Supported | Recommended: 20.19.0 |
| 21.x | ⚠️ Use with caution | Not tested |
| 22.x | ⚠️ Use with caution | Not tested |

### Python Versions

| Python Version | Status | Notes |
|----------------|--------|-------|
| 3.8 | ❌ Unsupported | EOL |
| 3.9 | ✅ Supported | Minimum version |
| 3.10 | ✅ Supported | |
| 3.11 | ✅ Supported | |
| 3.12 | ✅ Supported | Latest tested |

---

## Dependency Health

### Known Issues

1. **Platform-specific PTY packages**: Multiple @lydell/node-pty variants for different OS
2. **React 19 migration**: Recent upgrade may have compatibility issues
3. **OpenTelemetry versioning**: Large version jump (0.203.0) may need testing

### Recommended Updates

Run these commands to check for outdated dependencies:

```bash
# TypeScript/Node.js
cd qwen-code
npm outdated

# Python
cd qwen-desktop
pip list --outdated
```

---

## Stack Decision Rationale

### Why TypeScript for CLI?
- **Type safety** for complex agent logic
- **Cross-platform** compatibility
- **Rich ecosystem** of AI/ML libraries
- **Terminal UI** via Ink/React

### Why Python for Desktop?
- **PyQt6** for native-looking cross-platform GUI
- **Rapid prototyping** for UI features
- **Easy integration** with system tools
- **Familiar** to ML/AI practitioners

### Why Monorepo?
- **Shared types** between CLI and SDKs
- **Consistent versioning** across packages
- **Easier testing** of cross-package changes
- **Atomic commits** for multi-package changes

---

**Stack Documentation Complete** ✅
