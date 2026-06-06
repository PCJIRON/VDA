import logging
from collections.abc import AsyncGenerator
from typing import Any, Dict, List, Optional, Tuple

import httpx

from qwen_desktop.config.settings import Settings
from qwen_desktop.core._base_client import BaseClient

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
            headers["HTTP-Referer"] = "https://qwen-desktop.local"
            headers["X-Title"] = "Qwen Desktop"

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
    ) -> AsyncGenerator[str, None]:
        model = self._config.get_model()
        messages = conversation_history.copy()

        self._ensure_system_prompt(messages, vision_mode)

        user_content, _ = BaseClient._build_user_content(message, attachments)

        messages.append({"role": "user", "content": user_content})

        provider_name = self._config.get_provider_name()
        logger.info(f"Sending {len(messages)} messages to {provider_name} model {model}")

        client = self._create_client()
        try:
            payload = self._build_payload(model, messages)

            async with client.stream("POST", "/chat/completions", json=payload) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    logger.error(f"{provider_name} API error {response.status_code}: {error_text}")
                    yield self._handle_stream_error(response, provider_name)
                    return

                async for chunk in self._parse_sse_stream(response, provider_name):
                    yield chunk

        except httpx.TimeoutException:
            yield "Error: Request timed out. Check your internet connection."
        except Exception as e:
            logger.error(f"{provider_name} API error: {e}", exc_info=True)
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
