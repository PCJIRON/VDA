"""Shared base class for OpenAI-compatible API clients — SSE parsing, message construction, error handling."""

import json
import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any, Dict, List, Optional, Tuple

import httpx

from qwen_desktop.auth.provider_config import ProviderConfig
from qwen_desktop.config.settings import Settings
from qwen_desktop.core.default_prompt import build_system_prompt

logger = logging.getLogger(__name__)


class BaseClient(ABC):
    """Abstract base class for API clients with shared SSE parsing, message construction, and error handling."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._config = ProviderConfig(settings)

    @abstractmethod
    def _get_headers(self) -> dict:
        """Provider-specific HTTP headers."""

    def _get_base_url(self) -> str:
        return self._config.get_base_url().rstrip("/")

    def _create_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self._get_base_url(),
            headers=self._get_headers(),
            timeout=httpx.Timeout(self.settings.get("api_timeout", 120)),
        )

    @staticmethod
    def _get_system_prompt() -> str:
        return build_system_prompt()

    def _ensure_system_prompt(self, messages: list, vision_mode: bool) -> None:
        if vision_mode:
            has_system = any(m.get("role") == "system" for m in messages)
            if not has_system:
                messages.insert(0, {"role": "system", "content": self._get_system_prompt()})

    @staticmethod
    def _build_user_content(message: str | list, attachments: list | None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        user_content: List[Dict[str, Any]] = []
        if isinstance(message, list):
            user_content = list(message)
        else:
            user_content.append({"type": "text", "text": str(message)})

        text_block = None
        for block in user_content:
            if block.get("type") == "text":
                text_block = block
                break
        if text_block is None:
            text_block = {"type": "text", "text": ""}
            user_content.insert(0, text_block)

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
                    text_block["text"] += f"\n\n<document path='{fname}'>\n{doc_text}\n</document>"

        return user_content, text_block.get("text") if text_block else None

    def _build_payload(self, model: str, messages: list, temperature: float = 0.7) -> dict:
        return {
            "model": model,
            "messages": messages,
            "stream": True,
            "temperature": temperature,
        }

    async def _parse_sse_stream(self, response: httpx.Response, provider_name: str) -> AsyncGenerator[str, None]:
        async for line in response.aiter_lines():
            if not line.startswith("data: "):
                continue
            data_str = line[6:].strip()
            if data_str == "[DONE]":
                break
            try:
                data = json.loads(data_str)
                choices = data.get("choices", [])
                if not choices:
                    continue
                delta = choices[0].get("delta", {})
                content = delta.get("content", "")
                if content:
                    yield content
                reasoning = delta.get("reasoning_content") or delta.get("reasoning_details")
                if reasoning:
                    if isinstance(reasoning, list):
                        for r in reasoning:
                            if isinstance(r, dict):
                                t = r.get("text", "")
                                if t:
                                    yield f"<think>{t}</think>"
                    elif isinstance(reasoning, str):
                        yield f"<think>{reasoning}</think>"
            except json.JSONDecodeError:
                continue

    def _handle_stream_error(self, response: httpx.Response, provider_name: str) -> str:
        return f"Error: API returned {response.status_code}. Check your API key and model name."
