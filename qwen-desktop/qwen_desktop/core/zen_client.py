import logging
import uuid
from collections.abc import AsyncGenerator
from typing import Any, Dict, List, Optional, Tuple

import httpx

from qwen_desktop.config.settings import Settings
from qwen_desktop.core._base_client import BaseClient

logger = logging.getLogger(__name__)


class ZenClient(BaseClient):
    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)

    def _get_headers(self) -> dict:
        api_key = self._config.get_api_key()

        headers = {
            "Content-Type": "application/json",
            "x-opencode-client": "vda-desktop",
            "x-opencode-session": str(uuid.uuid4()),
            "x-opencode-project": "global",
            "x-opencode-request": str(uuid.uuid4()),
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        return headers

    async def test_connection(self) -> Tuple[bool, str]:
        model = self._config.get_model()
        free_models = self._config.get_free_models()
        test_model = model if model else (free_models[0] if free_models else "deepseek-v4-flash-free")

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

    def _handle_stream_error(self, response: httpx.Response, provider_name: str) -> str:
        if response.status_code == 401:
            return "Error: Invalid or missing API key. Get one at https://opencode.ai/zen or use a free model without a key."
        if response.status_code == 500:
            return "Error: Zen server error (500). Try a free model like deepseek-v4-flash-free without an API key, or visit console.opencode.ai to set up billing."
        return f"Error: API returned {response.status_code}. Check your API key and model name."

    async def send_message(
        self,
        message: str,
        conversation_history: List[Dict[str, Any]],
        attachments: Optional[List] = None,
        vision_mode: bool = False,
    ) -> AsyncGenerator[str, None]:
        model = self._config.get_model()
        messages = conversation_history.copy()

        self._ensure_system_prompt(messages, vision_mode)

        user_content, _ = BaseClient._build_user_content(message, attachments)

        messages.append({"role": "user", "content": user_content})

        logger.info(f"Sending {len(messages)} messages to OpenCode Zen model {model}")

        client = self._create_client()
        try:
            payload = self._build_payload(model, messages)

            async with client.stream("POST", "/chat/completions", json=payload) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    logger.error(f"OpenCode Zen API error {response.status_code}: {error_text}")
                    yield self._handle_stream_error(response, "Zen")
                    return

                line_count = 0
                async for chunk in self._parse_sse_stream(response, "Zen"):
                    line_count += 1
                    if line_count == 1:
                        logger.info("[ZenClient] First chunk received")
                    yield chunk
                logger.info(f"[ZenClient] Stream ended: {line_count} total chunks")

        except httpx.TimeoutException:
            yield "Error: Request timed out. Check your internet connection."
        except Exception as e:
            logger.error(f"OpenCode Zen API error: {e}", exc_info=True)
            yield f"Error: {e}"
        finally:
            await client.aclose()

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
