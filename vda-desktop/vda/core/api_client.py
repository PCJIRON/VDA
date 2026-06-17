import logging
from collections.abc import AsyncGenerator
from typing import Any, Dict, List, Optional, Tuple

import httpx

from vda.config.settings import Settings
from vda.core._base_client import BaseClient

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    pass


class APIClient(BaseClient):
    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)

    def _get_headers(self) -> dict:
        provider_id = self._config.get_provider_id()
        api_key = self._config.get_api_key()

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        if provider_id == "gemini":
            headers["x-goog-api-key"] = api_key
        elif provider_id == "openrouter":
            headers["HTTP-Referer"] = "https://vda-desktop.local"
            headers["X-Title"] = "VDA Desktop"

        return headers

    async def test_connection(self) -> Tuple[bool, str]:
        model = self._config.get_model()
        client = self._create_client()
        try:
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": "Say OK"}],
                "stream": False,
                "max_tokens": 10,
            }
            response = await client.post("/chat/completions", json=payload)
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return True, content[:200]
            if response.status_code == 429:
                return False, "Rate limit exceeded — wait a moment and try again."
            error_body = await response.aread()
            return False, f"HTTP {response.status_code}: {error_body[:200].decode(errors='replace')}"
        except httpx.TimeoutException:
            return False, "Request timed out"
        except Exception as e:
            return False, str(e)
        finally:
            await client.aclose()

    async def send_message(
        self,
        message: str,
        conversation_history: List[Dict[str, Any]],
        attachments: Optional[List] = None,
        vision_mode: bool = False,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        model = self._config.get_model()
        messages = conversation_history.copy()

        self._ensure_system_prompt(messages, vision_mode)

        user_content, _ = BaseClient._build_user_content(message, attachments)

        messages.append({"role": "user", "content": user_content})

        provider_name = self._config.get_provider_name()
        logger.info(f"Sending {len(messages)} messages to {provider_name} model {model}")

        client = self._get_or_create_client()
        payload = self._build_payload(model, messages, max_tokens=max_tokens)

        async for chunk in self._stream_with_retry(client, payload, provider_name):
            yield chunk

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
        async for chunk in self.send_message(current_message, history, max_tokens=max_tokens):
            yield chunk

    async def chat_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[dict, None]:
        """Send messages with native tool definitions (delegates to BaseClient)."""
        async for event in super().chat_with_tools(messages, tools, model=model, max_tokens=max_tokens):
            yield event
