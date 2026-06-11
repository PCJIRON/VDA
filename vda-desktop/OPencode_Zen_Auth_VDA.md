# OpenCode Zen Auth Implementation in VDA

## Overview

VDA uses **6 providers** for AI inference. OpenCode Zen is one of them, but it's special:

| Feature | OpenCode Zen | Others |
|---|---|---|
| Anonymous access | Yes (`"public"` key fallback) | No (API key required) |
| Dedicated client | `ZenClient` (`core/zen_client.py`) | `APIClient` (`core/api_client.py`) |
| Custom headers | `x-opencode-*` headers | Standard OpenAI-compatible headers |
| Free models | 6 models without any API key | No free models |
| Vision support | Yes (`image_url` in messages) | Varies by provider |

The OpenCode Zen server acts as a **proxy/multiplexer** — a single endpoint that routes to models from many providers (OpenAI, Anthropic, Google, DeepSeek, Meta, Mistral, etc.).

---

## Architecture

```
FloatingAssistant (_init_api)
    |
    ├── provider_id == "opencode" ──> ZenClient (core/zen_client.py)
    |                                      |
    |                                      ├── _get_headers() → "public" fallback
    |                                      ├── _get_base_url() → https://opencode.ai/zen/v1
    |                                      ├── test_connection()
    |                                      └── send_message() → streaming /chat/completions
    |
    └── provider_id != "opencode" ──> APIClient (core/api_client.py)

ProviderConfig (auth/provider_config.py)
    ├── allows_anonymous() → defaults.py "allow_anonymous" flag
    ├── is_configured() → Zen: only base_url needed; others: key + url
    └── save() → writes to config.json

SettingsDialog (TestWorker)
    ├── provider_id == "opencode" ──> ZenClient(self.settings)
    └── otherwise ──> APIClient(self.settings)
```

---

## File-by-File Breakdown

### 1. `config/defaults.py` — Provider Definition

The `"opencode"` entry defines the provider metadata:

```python
PROVIDERS = {
    "opencode": {
        "name": "OpenCode Zen",
        "base_url": "https://opencode.ai/zen/v1",
        "allow_anonymous": True,           # <-- KEY: enables anonymous access
        "models": [
            "deepseek-v4-flash",
            "claude-sonnet-4-20250514",
            "gemini-2.5-flash-preview-05-15",
            "gpt-5.4-mini",
            # ... 25+ models
        ],
        "free_models": [                    # <-- These work without any API key
            "deepseek-v4-flash-free",
            "mimo-v2.5-free",
            "vda3.6-plus-free",
            "minimax-m3-free",
            "nemotron-3-super-free",
            "gemini-2.0-flash-exp",
        ],
        "docs_url": "https://opencode.ai/zen",
        "api_key_hint": "occ_... or sk-...",
    },
    # ... other providers (deepseek, openrouter, nvidia, gemini, custom)
}
```

**Key design decisions:**
- `"allow_anonymous": True` — only OpenCode Zen has this flag
- `"free_models"` — separate list from paid `"models"`; the UI doesn't distinguish them visually, but `test_connection()` will try a free model if none is selected
- `"base_url"` is hardcoded; hidden from UI for predefined providers

---

### 2. `auth/provider_config.py` — Configuration Layer

```python
from vda.config.defaults import PROVIDERS


class ProviderConfig:
    def __init__(self, settings):
        self.settings = settings

    def get_provider_id(self) -> str:
        return self.settings.get("provider", "openrouter")

    def get_provider_info(self) -> dict:
        provider_id = self.get_provider_id()
        return PROVIDERS.get(provider_id, PROVIDERS["openrouter"])

    def get_api_key(self) -> str:
        return self.settings.get("api_key", "")

    def get_model(self) -> str:
        return self.settings.get("api_model", "")

    def get_base_url(self) -> str:
        return self.settings.get("api_base_url", "")

    def is_configured(self) -> bool:
        # Zen: only base_url needed (no API key required for free models)
        if self.get_provider_id() == "opencode":
            return bool(self.get_base_url())
        # All other providers: both key and url required
        return bool(self.get_api_key() and self.get_base_url())

    def allows_anonymous(self) -> bool:
        return bool(self.get_provider_info().get("allow_anonymous", False))

    def get_free_models(self) -> list[str]:
        return list(self.get_provider_info().get("free_models", []))

    def get_models(self) -> list[str]:
        return list(self.get_provider_info().get("models", []))

    def get_docs_url(self) -> str:
        return self.get_provider_info().get("docs_url", "")

    def get_api_key_hint(self) -> str:
        return self.get_provider_info().get("api_key_hint", "")

    def get_provider_name(self) -> str:
        return self.get_provider_info().get("name", "Unknown")

    def save(self, provider_id: str, api_key: str, model: str, base_url: str) -> None:
        self.settings.set("provider", provider_id)
        self.settings.set("api_key", api_key)
        self.settings.set("api_model", model)
        self.settings.set("api_base_url", base_url)
        self.settings.save()

    @staticmethod
    def get_all_providers() -> dict[str, dict]:
        return dict(PROVIDERS)
```

**`is_configured()` logic — critical for anonymous access:**
- OpenCode Zen: only requires a non-empty `base_url` → anonymous users are "configured"
- All others: requires both `api_key` AND `base_url` to be non-empty

**`allows_anonymous()`** — reads `"allow_anonymous"` from the provider's definition in `defaults.py`

---

### 3. `core/zen_client.py` — The Zen Client (FULL CODE)

This is the dedicated client for OpenCode Zen. Completely separate from `APIClient`.

```python
from typing import Optional, AsyncGenerator, List, Dict, Any, Tuple
import json
import logging
import uuid

import httpx

from vda.config.settings import Settings
from vda.auth.provider_config import ProviderConfig

logger = logging.getLogger(__name__)


class ZenClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._config = ProviderConfig(settings)

    # ─── HEADERS: "public" key fallback + OpenCode-specific headers ───
    def _get_headers(self) -> dict:
        api_key = self._config.get_api_key()
        if not api_key:
            api_key = "public"                   # <-- Anonymous fallback

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "x-opencode-client": "vda-desktop",   # Identifies the app
            "x-opencode-session": str(uuid.uuid4()),  # Fresh per call
            "x-opencode-project": "global",         # Project scope
            "x-opencode-request": str(uuid.uuid4()), # Fresh per request
        }
        return headers

    def _get_base_url(self) -> str:
        return self._config.get_base_url().rstrip("/")

    # ─── TEST CONNECTION ───
    async def test_connection(self) -> Tuple[bool, str]:
        model = self._config.get_model()
        free_models = self._config.get_free_models()
        # Fall back to a free model if none selected
        test_model = model if model else (
            free_models[0] if free_models else "deepseek-v4-flash-free"
        )

        headers = self._get_headers()
        base_url = self._get_base_url()

        client = httpx.AsyncClient(
            base_url=base_url,
            headers=headers,
            timeout=httpx.Timeout(15),
        )
        try:
            payload = {
                "model": test_model,
                "messages": [{"role": "user", "content": "Say OK"}],
                "stream": False,
                "max_tokens": 10,
            }
            response = await client.post("/chat/completions", json=payload)
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return True, content[:200]

            error_body = await response.aread()
            error_text = error_body[:200].decode(errors="replace")

            if response.status_code == 401:
                return False, "Invalid or missing API key — get one at https://opencode.ai/zen"
            if response.status_code == 500:
                return False, "Zen server error (500) — the service may be down or your key lacks billing. Try a free model like deepseek-v4-flash-free without a key, or visit console.opencode.ai"

            return False, f"HTTP {response.status_code}: {error_text}"

        except httpx.TimeoutException:
            return False, "Request timed out — check your internet or try a different model"
        except httpx.ConnectError:
            return False, f"Cannot connect to {base_url} — check your internet"
        except Exception as e:
            return False, str(e)
        finally:
            await client.aclose()

    # ─── VISION SYSTEM PROMPT ───
    VISION_SYSTEM_PROMPT = (... snipped for brevity ...)

    # ─── SEND MESSAGE (STREAMING) ───
    async def send_message(
        self,
        message: str,
        conversation_history: List[Dict[str, Any]],
        attachments: Optional[List] = None,
        vision_mode: bool = False,
    ) -> AsyncGenerator[str, None]:
        model = self._config.get_model()
        headers = self._get_headers()
        base_url = self._get_base_url()

        messages = conversation_history.copy()

        if vision_mode:
            has_system = any(m.get("role") == "system" for m in messages)
            if not has_system:
                messages.insert(0, {"role": "system", "content": self.VISION_SYSTEM_PROMPT})

        # Build user content with text + attachments
        user_content: List[Dict[str, Any]] = []
        user_content.append({"type": "text", "text": message})

        if attachments:
            for att in attachments:
                if att.get("type") == "image":
                    mime = att.get("mime", "image/png")
                    b64 = att.get("base64")
                    if b64:
                        user_content.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime};base64,{b64}"},
                        })
                elif att.get("type") == "file":
                    doc_text = att.get("content", "")
                    fname = att.get("name", "file")
                    user_content[0]["text"] += (
                        f"\n\n<document path='{fname}'>\n{doc_text}\n</document>"
                    )

        messages.append({"role": "user", "content": user_content})

        logger.info(f"Sending {len(messages)} messages to OpenCode Zen model {model}")

        client = httpx.AsyncClient(
            base_url=base_url,
            headers=headers,
            timeout=httpx.Timeout(self.settings.get("api_timeout", 120)),
        )
        try:
            payload = {
                "model": model,
                "messages": messages,
                "stream": True,
                "temperature": 0.7,
            }

            async with client.stream("POST", "/chat/completions", json=payload) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    logger.error(f"OpenCode Zen API error {response.status_code}: {error_text}")
                    if response.status_code == 401:
                        yield "Error: Invalid or missing API key..."
                    elif response.status_code == 500:
                        yield "Error: Zen server error (500)..."
                    else:
                        yield f"Error: API returned {response.status_code}..."
                    return

                # Parse SSE stream
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        choices = data.get("choices", [])
                        if not choices:    # <-- Skip cost-tracking chunks (empty choices)
                            continue
                        delta = choices[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue

        except httpx.TimeoutException:
            yield "Error: Request timed out..."
        except Exception as e:
            logger.error(f"OpenCode Zen API error: {e}", exc_info=True)
            yield f"Error: {e}"
        finally:
            await client.aclose()

    # ─── CHAT WRAPPER ───
    async def chat(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        stream: bool = True,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        current_message = messages[-1]["content"] if messages else ""
        history = messages[:-1] if len(messages) > 1 else []
        async for chunk in self.send_message(current_message, history):
            yield chunk
```

**Key implementation details:**

#### `"public"` key fallback (line 23)
```python
if not api_key:
    api_key = "public"
```
When the user leaves the API key field blank:
1. `settings.get("api_key", "")` returns `""`
2. `_get_headers()` sees empty key → substitutes `"public"`
3. Authorization header becomes `Bearer public`
4. Zen server recognizes this as anonymous/free-tier access

#### OpenCode-specific headers (lines 28-31)
```python
"x-opencode-client": "vda-desktop",
"x-opencode-session": str(uuid.uuid4()),
"x-opencode-project": "global",
"x-opencode-request": str(uuid.uuid4()),
```
These headers are unique to the OpenCode Zen proxy. Sent on every request to help the server identify the client application, track sessions, and correlate requests.

#### Empty choices skip (lines 193-195)
```python
choices = data.get("choices", [])
if not choices:
    continue
```
The Zen server sends cost-tracking SSE chunks with empty `choices` arrays. Without this check, those chunks would cause an `IndexError`. This was a bug fix during development.

#### Vision support (lines 147-150)
```python
user_content.append({
    "type": "image_url",
    "image_url": {"url": f"data:{mime};base64,{b64}"},
})
```
ZenClient supports vision via OpenAI-compatible `image_url` with base64-encoded data URIs. Only vision-capable models (e.g., `gemini-2.5-flash-preview-05-15`, `claude-sonnet-4-20250514`) can process these.

#### httpx client per-request (not cached)
Each `send_message()` and `test_connection()` call creates a fresh `httpx.AsyncClient` and closes it in `finally`. This avoids the `Event loop is closed` error that occurs when `asyncio.run()` finishes inside a QThread with cached clients.

---

### 4. `ui/floating_assistant.py` — Client Dispatch

```python
from vda.core.zen_client import ZenClient
from vda.core.api_client import APIClient


class FloatingAssistant(QWidget):
    def __init__(self, settings, parent=None):
        ...
        self._config = ProviderConfig(settings)
        self._init_api()  # Called at startup

    def _init_api(self):
        self.api_client = None
        if self._config.is_configured():
            try:
                provider_id = self._config.get_provider_id()
                if provider_id == "opencode":
                    self.api_client = ZenClient(self.settings)
                    logger.info("ZenClient initialized for OpenCode Zen")
                else:
                    self.api_client = APIClient(self.settings)
                    logger.info(f"APIClient initialized for {provider_id}")
            except Exception as e:
                logger.error(f"API init failed: {e}")

    def open_settings(self):
        dialog = SettingsDialog(self._config, self.settings, self)
        dialog.exec()
        if self._config.is_configured():
            self._init_api()  # Re-init after settings change
            self.history_popup.add_message("Settings saved. API is configured.", "ai")
        else:
            self.history_popup.add_message("API not configured. Please set up your API key.", "ai")
```

**Dispatch logic:** `_init_api()` checks `provider_id`:
- `"opencode"` → `ZenClient`
- everything else → `APIClient`

Both clients implement the same async-generator interface (`send_message`, `test_connection`, `chat`), so the rest of `FloatingAssistant` is provider-agnostic.

---

### 5. `ui/settings_dialog.py` — TestWorker Dispatch

```python
from vda.core.zen_client import ZenClient
from vda.core.api_client import APIClient


class TestWorker(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, settings: Settings):
        super().__init__()
        self.settings = settings

    def run(self):
        provider_id = self.settings.get("provider", "")
        if provider_id == "opencode":
            client = ZenClient(self.settings)
        else:
            client = APIClient(self.settings)
        try:
            success, msg = asyncio.run(client.test_connection())
            self.finished.emit(success, msg)
        except Exception as e:
            self.finished.emit(False, str(e))
```

The same dispatch pattern as `_init_api()` — check `provider_id`, create the appropriate client. This is necessary because `APIClient.test_connection()` would fail when no API key is set (it sends an empty `Authorization` header, causing `illegal header value` in httpx).

---

## Complete Data Flow: User Sends a Message

```
1. User types message in FloatingAssistant
2. FloatingAssistant calls self.api_client.send_message(...)
       │
3. ZenClient.send_message() called
       │
4. _get_headers()
   ├── Reads API key from settings
   ├── Empty? → "public" fallback
   └── Returns: Authorization: Bearer <key>, x-opencode-*
       │
5. Builds messages array
   ├── Copies conversation history
   ├── Inserts VISION_SYSTEM_PROMPT if vision_mode
   ├── Builds user_content with text + attachments (images/files)
   └── Appends to messages
       │
6. Creates httpx.AsyncClient
   ├── base_url = https://opencode.ai/zen/v1
   ├── headers from step 4
   └── timeout = api_timeout (default 120s)
       │
7. POST /chat/completions with streaming payload
       │
8. Parses SSE data: lines → json → choices[0].delta.content
   ├── Skips lines without "data: " prefix
   ├── Skips empty choices arrays (cost tracking chunks)
   ├── Stops at "[DONE]"
   └── Yields each content chunk
       │
9. FloatingAssistant receives chunks → rendered in chat UI
       │
10. Finally: client.aclose()
```

---

## Free Models — How They Work

No API key is needed for these 6 models:

| Model | Provider |
|---|---|
| `deepseek-v4-flash-free` | DeepSeek |
| `mimo-v2.5-free` | Mimo |
| `vda3.6-plus-free` | VDA |
| `minimax-m3-free` | MiniMax |
| `nemotron-3-super-free` | NVIDIA |
| `gemini-2.0-flash-exp` | Google |

When the user:
1. Selects "OpenCode Zen"
2. Leaves API key blank
3. Picks a free model (or any model — Zen server downgrades to free for anonymous)
4. Clicks Save

→ `ProviderConfig.is_configured()` returns `True` (only needs base_url for Zen)
→ `_get_headers()` substitutes `"public"` for the key
→ `Authorization: Bearer public` → Zen server grants free-tier access

---

## Settings Persistence

All settings are stored in `C:\Users\<user>\.vda-desktop\config.json`:

```json
{
    "provider": "opencode",
    "api_base_url": "https://opencode.ai/zen/v1",
    "api_model": "deepseek-v4-flash-free",
    "api_key": "",
    "api_timeout": 120,
    ...
}
```

Saved via `ProviderConfig.save()` → `Settings.set()` → `Settings.save()` → JSON dump.

---

## Error Handling

| Scenario | HTTP Status | User Message |
|---|---|---|
| No key + paid model | 401 | "Invalid or missing API key" |
| Server overload/billing | 500 | "Zen server error (500) — try a free model" |
| Connection failure | — | "Cannot connect to {url}" |
| Timeout | — | "Request timed out" |
| Empty choices in SSE | — | Skipped silently (cost tracking) |

---

## Why a Separate ZenClient?

OpenCode Zen was **intentionally separated** from the generic `APIClient` because:

1. **Anonymous access** — no other provider allows empty API keys
2. **Custom headers** — `x-opencode-*` headers are not standard OpenAI
3. **Proxy/multiplexer behavior** — Zen routes to multiple underlying providers, so model naming/error semantics differ
4. **Free model logic** — `test_connection()` auto-fallsback to free models
5. **Server behavior** — Zen sends cost-tracking chunks with empty choices that need special handling
