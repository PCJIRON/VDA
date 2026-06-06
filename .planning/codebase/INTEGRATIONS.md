# External Integrations

**Analysis Date:** 2026-06-06

## APIs & External Services

**AI Providers (Multi-Provider Architecture):**
The application supports multiple AI providers through a unified OpenAI-compatible chat completions API (`/chat/completions` endpoint). Provider selection and configuration done via `qwen-desktop/qwen_desktop/auth/provider_config.py` and `qwen-desktop/qwen_desktop/config/defaults.py`.

| Provider | Base URL | Auth | Free Tier |
|----------|----------|------|-----------|
| OpenCode Zen | `https://opencode.ai/zen/v1` | Bearer token (`occ_...`/`sk-...`) | Yes (free models: `deepseek-v4-flash-free`, `mimo-v2.5-free`, etc.) |
| OpenRouter | `https://openrouter.ai/api/v1` | Bearer token (`sk-or-v1-...`) | No |
| DeepSeek | `https://api.deepseek.com` | Bearer token (`sk-...`) | No |
| Google Gemini | `https://generativelanguage.googleapis.com/v1beta/openai/` | `x-goog-api-key` header (`AIza...`) | No |
| NVIDIA NIM | `https://integrate.api.nvidia.com/v1` | Bearer token (`nvapi-...`) | No |
| Custom (OpenAI-compatible) | User-defined | Bearer token (`sk-...`) | No |

**Model Inventory** (defined in `qwen-desktop/qwen_desktop/config/defaults.py`):
- 33 models across OpenCode Zen
- 17 models across OpenRouter
- 2 models across DeepSeek
- 5 models across Google Gemini
- 11 models across NVIDIA NIM
- Models include: deepseek-v4-flash, claude-sonnet-4, gemini-2.5-pro, gpt-5.x, llama-3.3, qwen3.x, minimax-m2.x, etc.

**API Client Implementations:**
- `APIClient` (`qwen-desktop/qwen_desktop/core/api_client.py`): Generic OpenAI-compatible client using `httpx.AsyncClient` for streaming completions. Handles auth headers, vision payloads (base64 images), file attachments, and server-sent events (SSE) parsing.
- `ZenClient` (`qwen-desktop/qwen_desktop/core/zen_client.py`): Specialized client for OpenCode Zen API. Adds custom headers (`x-opencode-client`, `x-opencode-session`, `x-opencode-project`, `x-opencode-request`). Handles free model fallback and specific error messages for 401/500 responses.

## Data Storage

**Databases:**
- None. The application uses filesystem-based storage exclusively.

**File Storage:**
- Local filesystem only

**Conversation Storage:**
- JSONL files at `~/.qwen-desktop/sessions/{project_hash}/chats/{session_id}.jsonl`
- Each message stored as a JSON record with UUID, parentUuid (for threading), sessionId, cwd, timestamp, type, and message parts
- Session management via `SessionService` in `qwen-desktop/qwen_desktop/core/session_service.py`

**Memory Storage:**
- `ShortTermMemory`: In-memory task context tracking (max 4096 tokens) in `qwen-desktop/qwen_desktop/core/memory_manager.py`
- `LongTermMemory`: JSON files at `~/.qwen-desktop/memory/{key}.json`
- `DailyTaskCache`: Wraps LTM with daily task aggregation (`daily_tasks_{YYYYMMDD}.json`)
- `BehaviorTracker`: JSONL action log at `~/.qwen-desktop/behavior/session_{YYYYMMDD}.jsonl`

**Template Storage:**
- UIED component templates stored as PNG images at `~/.qwen_desktop/uied_templates/`

**Caching:**
- None (no Redis, Memcached, or in-memory caching layer)

## Authentication & Identity

**Auth Provider:**
- **OAuth 2.0 via Qwen** — The `requests-oauthlib` library is used for OAuth flow.
- OAuth callback server runs locally via Flask on `http://localhost:8080/callback`
- Auth module files (`oauth_handler.py`, `token_manager.py`, `credentials.py`) are referenced in tests (`qwen-desktop/tests/test_auth.py`) but not yet present in the source tree (`qwen-desktop/qwen_desktop/auth/` only contains `provider_config.py` and `__init__.py`). These are planned/under development.
- Scopes used: `openid profile email model.completion`
- Bearer token authentication for all AI provider APIs (except Gemini which uses `x-goog-api-key`)

**Implementation:**
- API key input via Settings dialog (`qwen-desktop/qwen_desktop/ui/settings_dialog.py`)
- Keys stored in JSON config file (and optionally via `keyring` OS-level credential manager)
- Provider configuration read by `ProviderConfig` class (`qwen-desktop/qwen_desktop/auth/provider_config.py`)

## Monitoring & Observability

**Error Tracking:**
- None (no Sentry, Rollbar, or similar service)

**Logs:**
- Python `logging` module with standard `logging.Logger`
- Log format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- Console handler (stdout) always active
- File handler writes to `~/.qwen-desktop/app.log`
- Logger setup via `setup_logger()` in `qwen-desktop/qwen_desktop/utils/logger.py`

## CI/CD & Deployment

**Hosting:**
- Not applicable (local desktop application, no server deployment)

**CI Pipeline:**
- Not detected (no GitHub Actions, Jenkins, or similar CI configuration files found)

**Distribution:**
- Source distribution via git
- Installable via `pip install -e .` or `pip install -r requirements.txt`
- Run via `py run.py` or `python -m qwen_desktop`

## Environment Configuration

**Required env vars:**
- None strictly required (all configurable via settings dialog or config.json)
- API keys are typically configured through the UI or config file

**Optional env vars (via python-dotenv):**
- Any API keys can be loaded from a `.env` file

**Secrets location:**
- API key: stored in `config.json` as plaintext (or via `keyring` for OS-level encryption)
- OAuth tokens: managed by `requests-oauthlib` (assuming token persistence in `token_manager.py` once implemented)
- No `.env` file is committed (controlled by `.gitignore`)

## Webhooks & Callbacks

**Incoming:**
- OAuth callback at `http://localhost:8080/callback` (Flask server)

**Outgoing:**
- None

## Desktop Automation Integrations

**Screen Capture & Automation:**
- `pyautogui` — Screen capture, mouse control (`click`, `moveTo`, `drag`, `scroll`, `write`), screenshot, resolution detection
- `pynput` — Global mouse click and keyboard press event listeners (triggers vision capture)
- `Pillow` — Image manipulation, resize, format conversion, base64 encoding
- `opencv-python` — Template matching (`cv2.matchTemplate` with `TM_CCOEFF_NORMED`), multi-scale matching, pixel change verification, contour detection
- `uiautomation` — Windows-only COM-based UI Automation for taskbar element detection (`WindowControl`, `GetForegroundControl`)
- `ctypes.windll` — Windows DPI awareness and screen metrics (`GetSystemMetrics`, `GetDeviceCaps`, `SetProcessDPIAware`)

**Executor Implementations:**
- `PyAutoGUIExecutor` (`qwen-desktop/qwen_desktop/core/pyautogui_executor.py`): JSON response parsing, coordinate validation, mouse action execution, template matching with multi-scale and DPI-aware detection
- `EnhancedExecutor` (`qwen-desktop/qwen_desktop/core/enhanced_executor.py`): Coordinate conversion (normalized/absolute), DPI scaling, `ClickValidator` for pixel-change verification, keyboard typing support

---

*Integration audit: 2026-06-06*
