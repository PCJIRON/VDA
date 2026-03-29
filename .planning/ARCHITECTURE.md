# Architecture Overview

**Project:** qwen_desktop  
**Generated:** 2026-03-29

---

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interfaces                          │
├─────────────────────────┬───────────────────────────────────────┤
│   Terminal CLI (Ink)    │      Desktop GUI (PyQt6)              │
│   packages/cli/         │      qwen-desktop/                    │
└───────────┬─────────────┴────────────────┬──────────────────────┘
            │                              │
            │  ┌───────────────────────────┘
            │  │
            ▼  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Core Agent Engine                            │
│                   packages/core/                                │
│  ┌─────────────┬─────────────┬─────────────┬─────────────────┐ │
│  │   Tools     │   Agents    │  Services   │   Protocols     │ │
│  │  - File     │  - Main     │  - Git      │  - MCP          │ │
│  │  - Shell    │  - Subagent │  - Config   │  - LSP          │ │
│  │  - Web      │  - Skills   │  - Session  │  - ACP          │ │
│  └─────────────┴─────────────┴─────────────┴─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   AI Model Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Qwen API   │  │  OpenAI API  │  │  Anthropic   │          │
│  │  (Dashscope) │  │  Compatible  │  │   Claude     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Architectural Patterns

### 1. Layered Architecture

```
┌─────────────────────────────────────┐
│     Presentation Layer (UI)         │  ← CLI, Desktop GUI, Web UI
├─────────────────────────────────────┤
│     Application Layer (Agent)       │  ← Core logic, orchestration
├─────────────────────────────────────┤
│     Domain Layer (Tools/Services)   │  ← Business logic, tools
├─────────────────────────────────────┤
│     Infrastructure Layer            │  ← API clients, file system
└─────────────────────────────────────┘
```

### 2. Plugin Architecture

The system supports extensibility through:

- **Skills**: Reusable tool combinations
- **Extensions**: VS Code, Zed integrations
- **MCP Servers**: Model Context Protocol providers
- **Custom Tools**: User-defined tool implementations

### 3. Event-Driven Communication

```
User Input → Event Bus → Handler → Tool Execution → Response → UI Update
                ↑
                └──→ Telemetry (OpenTelemetry)
```

---

## Component Architecture

### CLI Application (packages/cli)

```
┌─────────────────────────────────────────────────────────────┐
│                      CLI Entry Point                        │
│                    src/gemini.tsx                           │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │  Interactive    │  │  Non-Interactive│                  │
│  │  Mode (Ink)     │  │  Mode (Headless)│                  │
│  │  src/gemini.tsx │  │  src/nonInter-  │                  │
│  │                 │  │  activeCli.ts   │                  │
│  └─────────────────┘  └─────────────────┘                  │
├─────────────────────────────────────────────────────────────┤
│                    Command System                           │
│  /help  /clear  /compress  /auth  /model  /bug  /exit      │
├─────────────────────────────────────────────────────────────┤
│                    UI Components                            │
│  - MessageList  - InputForm  - ToolCallDisplay             │
│  - Sidebar      - Header      - Footer                     │
└─────────────────────────────────────────────────────────────┘
```

### Core Engine (packages/core)

```
┌─────────────────────────────────────────────────────────────┐
│                    Core Entry Point                         │
│                    src/index.ts                             │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐   │
│  │                 Config System                        │   │
│  │  - settings.json parsing                             │   │
│  │  - Environment variable resolution                   │   │
│  │  - Model provider configuration                      │   │
│  └──────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  Model Layer                         │   │
│  │  - ModelRegistry                                     │   │
│  │  - Provider abstraction (OpenAI, Anthropic, Gemini)  │   │
│  │  - OAuth authentication                              │   │
│  └──────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐   │
│  │                   Tool System                        │   │
│  │  - ReadTool, WriteTool, EditTool                     │   │
│  │  - ShellTool, GlobTool, GrepTool                     │   │
│  │  - WebFetchTool, LSPTool, MCPTool                    │   │
│  │  - Permission system                                 │   │
│  └──────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐   │
│  │                 Agent System                         │   │
│  │  - Main agent loop                                   │   │
│  │  - Subagent delegation                               │   │
│  │  - Skills execution                                  │   │
│  │  - Plan mode                                         │   │
│  └──────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐   │
│  │                Service Layer                         │   │
│  │  - GitService                                        │   │
│  │  - FileDiscoveryService                              │   │
│  │  - SessionService                                    │   │
│  │  - TelemetryService (OpenTelemetry)                  │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Desktop Application (qwen-desktop)

```
┌─────────────────────────────────────────────────────────────┐
│                  Desktop Entry Point                        │
│                    run.py / __main__.py                     │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐   │
│  │               PyQt6 GUI Layer                        │   │
│  │  ┌──────────────┐  ┌──────────────┐                 │   │
│  │  │  MainWindow  │  │  Floating    │                 │   │
│  │  │              │  │  Assistant   │                 │   │
│  │  └──────────────┘  └──────────────┘                 │   │
│  └──────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐   │
│  │              UI Components                           │   │
│  │  - ChatWidget       - MessageBubble                  │   │
│  │  - InputArea        - SendButton                     │   │
│  │  - ToolDisplay      - SettingsDialog                 │   │
│  │  - VisionButton     - AttachButton                   │   │
│  └──────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Core Logic                              │   │
│  │  - APIClient          - ToolExecutor                 │   │
│  │  - ConversationManager - QwenSessionService          │   │
│  │  - CommandRegistry                                   │   │
│  └──────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐   │
│  │            Authentication                            │   │
│  │  - OAuthHandler       - TokenManager                 │   │
│  │  - Credentials        - QwenAuthGUI                  │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Request Flow (Interactive Mode)

```
1. User Input
   │
   ▼
2. CLI InputForm (Ink component)
   │
   ▼
3. Core Agent Loop (packages/core)
   │
   ├──→ Parse input
   ├──→ Check context (@file references)
   └──→ Build conversation history
   │
   ▼
4. Model API Call
   │
   ├──→ Select model (from config)
   ├──→ Apply authentication (OAuth/API key)
   └──→ Send request
   │
   ▼
5. Stream Response
   │
   ├──→ Parse tool calls
   ├──→ Execute tools (with permission)
   └──→ Format output
   │
   ▼
6. Render to Terminal
   │
   ├──→ Update MessageList
   ├──→ Show tool execution results
   └──→ Return to input
```

### Tool Execution Flow

```
Agent Request
   │
   ▼
┌─────────────────────────────────────┐
│         Permission Check            │
│  - User approval required?          │
│  - YOLO mode bypass?                │
└─────────────────────────────────────┘
   │
   ├──[Denied]──→ Return error
   │
   ▼[Approved]
┌─────────────────────────────────────┐
│         Tool Executor               │
│  - Validate parameters              │
│  - Execute operation                │
│  - Capture output/errors            │
└─────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────┐
│         Result Formatter            │
│  - Format for display               │
│  - Extract relevant info            │
│  - Build context for model          │
└─────────────────────────────────────┘
   │
   ▼
Return to Agent Loop
```

---

## Module Dependencies

### Package Dependency Graph

```
@qwen-code/qwen-code (CLI)
│
├── @qwen-code/qwen-code-core
│   │
│   ├── @anthropic-ai/sdk
│   ├── @google/genai
│   ├── openai
│   ├── @modelcontextprotocol/sdk
│   └── [other dependencies]
│
├── @qwen-code/webui
│   └── [React, Tailwind, etc.]
│
└── [CLI-specific dependencies]


qwen-desktop (Python)
│
├── PyQt6
├── httpx
├── requests
├── markdown
└── [other Python packages]
```

### Internal Module Structure

```
packages/
│
├── cli/                    # Depends on: core, webui
│   ├── src/
│   │   ├── ui/            # Ink/React components
│   │   ├── commands/      # Slash commands
│   │   ├── config/        # CLI config
│   │   └── i18n/          # Internationalization
│   └── package.json
│
├── core/                   # Depends on: none (base package)
│   ├── src/
│   │   ├── tools/         # Tool implementations
│   │   ├── agents/        # Agent logic
│   │   ├── models/        # Model abstraction
│   │   ├── services/      # Utility services
│   │   └── config/        # Core configuration
│   └── package.json
│
├── webui/                  # Depends on: React, Tailwind
│   ├── src/
│   │   ├── components/    # Shared UI components
│   │   ├── hooks/         # React hooks
│   │   └── context/       # React context
│   └── package.json
│
├── sdk-typescript/         # Depends on: core
│   └── src/
│       └── sdk/           # TypeScript SDK
│
├── sdk-java/               # Standalone Java SDK
│   └── client/
│       └── src/
│           └── main/java/
│
├── vscode-ide-companion    # Depends on: VS Code API
│   └── src/
│       └── extension/     # VS Code extension
│
└── zed-extension           # Depends on: Zed API
    └── extension.toml
```

---

## Configuration Architecture

### Settings Hierarchy

```
┌─────────────────────────────────────────┐
│         Configuration Sources           │
│  (Highest Priority → Lowest Priority)   │
├─────────────────────────────────────────┤
│  1. CLI flags (--model, --yolo, etc.)   │
│  2. Environment variables               │
│  3. .env files (project)                │
│  4. .qwen/settings.json (project)       │
│  5. ~/.qwen/settings.json (user)        │
│  6. Default values                      │
└─────────────────────────────────────────┘
```

### Settings Schema

```json
{
  "modelProviders": {
    "openai": [
      {
        "id": "qwen3-coder-plus",
        "baseUrl": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "envKey": "DASHSCOPE_API_KEY"
      }
    ]
  },
  "env": {
    "DASHSCOPE_API_KEY": "sk-xxx"
  },
  "security": {
    "auth": {
      "selectedType": "openai"
    }
  },
  "model": {
    "name": "qwen3-coder-plus"
  },
  "tools": {
    "autoApprove": [],
    "permissionMode": "default"
  }
}
```

---

## Security Architecture

### Authentication Flow

```
┌─────────────────────────────────────────────────────────────┐
│                  Authentication Methods                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐         ┌─────────────────┐           │
│  │   Qwen OAuth    │         │    API Key      │           │
│  │  (Device Flow)  │         │   (Multiple)    │           │
│  │                 │         │                 │           │
│  │  1. Open browser│         │  1. Load from   │           │
│  │  2. Get code    │         │     env/config  │           │
│  │  3. Poll token  │         │  2. Validate    │           │
│  │  4. Store token │         │  3. Use in API  │           │
│  └─────────────────┘         └─────────────────┘           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Permission System

```
┌─────────────────────────────────────────────────────────────┐
│                   Permission Modes                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Default Mode:                                              │
│  - Prompt for file writes                                   │
│  - Prompt for shell commands                                │
│  - Auto-approve reads                                       │
│                                                             │
│  YOLO Mode (--yolo):                                        │
│  - Auto-approve all tools                                   │
│  - Use with caution!                                        │
│                                                             │
│  Custom Mode:                                               │
│  - Configure per-tool permissions                           │
│  - Domain-based URL approval                                  │
│  - Path-based file approval                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Credential Storage

| Platform | Storage Method |
|----------|----------------|
| Windows | Windows Credential Manager |
| macOS | Keychain |
| Linux | Secret Service API (GNOME Keyring/KWallet) |

---

## Testing Architecture

### Test Pyramid

```
           ┌───┐
          │ E2E │         Integration Tests
         │ Tests │      (integration-tests/)
        ├─────────┤
       │  Unit   │    Unit Tests
      │   Tests   │  (packages/*/src/*.test.ts)
     ├─────────────┤
    │   Manual    │  Manual Testing
   │   Testing    │
  └───────────────┘
```

### Test Frameworks

| Package | Framework | Config |
|---------|-----------|--------|
| TypeScript | Vitest | vitest.config.ts |
| Python | pytest | pyproject.toml |
| React Components | Testing Library + Vitest | packages/webui/ |
| CLI UI | ink-testing-library | packages/cli/ |
| PyQt6 GUI | pytest-qt | qwen-desktop/tests/ |

### Test Categories

1. **Unit Tests**: Individual functions, classes, modules
2. **Integration Tests**: Multi-component workflows
3. **E2E Tests**: Full user scenarios (Terminal-Bench)
4. **Visual Tests**: Storybook component stories

---

## Deployment Architecture

### Build Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                    CI/CD Pipeline                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Source → Lint → Typecheck → Test → Build → Package        │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  npm packages (TypeScript)                          │   │
│  │  - @qwen-code/qwen-code (CLI)                       │   │
│  │  - @qwen-code/qwen-code-core (Core)                 │   │
│  │  - @qwen-code/webui (Web Components)                │   │
│  │  - @qwen-code/sdk-typescript (SDK)                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  PyPI package (Python)                              │   │
│  │  - qwen-desktop (Desktop GUI)                       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Release Strategy

- **Semantic Versioning**: MAJOR.MINOR.PATCH
- **Monorepo Versioning**: Synchronized across packages
- **Changelog**: Auto-generated from git commits
- **GitHub Releases**: Automated via CI

---

## Scalability Considerations

### Current Limitations

1. **Single-threaded Agent**: One conversation at a time
2. **In-memory State**: No persistent session storage (optional)
3. **Local Execution**: No distributed computing

### Future Extensions

1. **Multi-agent Orchestration**: Parallel task execution
2. **Session Persistence**: Database-backed history
3. **Cloud Deployment**: Containerized agent instances
4. **Plugin Marketplace**: Community-contributed extensions

---

## Architecture Decision Records (ADRs)

### ADR-001: Monorepo Structure

**Decision:** Use npm workspaces for TypeScript packages

**Rationale:**
- Shared types between packages
- Atomic commits across packages
- Simplified dependency management
- Consistent tooling

### ADR-002: Dual-Stack Approach

**Decision:** TypeScript for CLI, Python for Desktop

**Rationale:**
- TypeScript: Best-in-class terminal UI (Ink)
- Python: Rapid GUI development (PyQt6)
- Team expertise alignment
- Ecosystem strengths

### ADR-003: OpenAI-Compatible API

**Decision:** Support OpenAI-compatible API format

**Rationale:**
- Multiple provider support
- Easy model switching
- Future-proof against API changes
- Leverage existing tooling

---

**Architecture Documentation Complete** ✅
