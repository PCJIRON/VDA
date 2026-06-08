"""Shared base class for OpenAI-compatible API clients — SSE parsing, message construction, error handling, retry & rate limiting."""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any, Dict, List, Optional, Tuple

import httpx

from qwen_desktop.auth.provider_config import ProviderConfig
from qwen_desktop.config.settings import Settings
from qwen_desktop.core.default_prompt import build_system_prompt

logger = logging.getLogger(__name__)

# Default rate limit config used when a provider doesn't specify one.
_DEFAULT_RATE_LIMIT = {
    "min_request_interval": 1.0,
    "max_retries": 3,
    "base_backoff": 1.0,
}


class BaseClient(ABC):
    """Abstract base class for API clients with shared SSE parsing, message construction, error handling, retry & rate limiting."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._config = ProviderConfig(settings)
        # Persistent client for connection reuse (lazy-created)
        self._persistent_client: Optional[httpx.AsyncClient] = None
        # Timestamp of the last API request — used for inter-request throttling
        self._last_request_time: float = 0.0

    @abstractmethod
    def _get_headers(self) -> dict:
        """Provider-specific HTTP headers."""

    def _get_base_url(self) -> str:
        return self._config.get_base_url().rstrip("/")

    def _get_rate_limit_config(self) -> dict:
        """Return rate limit config for the current provider."""
        provider_info = self._config.get_provider_info()
        return provider_info.get("rate_limit", _DEFAULT_RATE_LIMIT)

    def _create_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self._get_base_url(),
            headers=self._get_headers(),
            timeout=httpx.Timeout(self.settings.get("api_timeout", 120)),
        )

    def _get_or_create_client(self) -> httpx.AsyncClient:
        """Return a persistent httpx client, creating one if needed.

        Reusing the client enables HTTP/2 connection reuse and avoids
        per-request TLS handshakes — which can trigger anti-abuse rate
        limits on some providers.
        """
        if self._persistent_client is None or self._persistent_client.is_closed:
            self._persistent_client = self._create_client()
        return self._persistent_client

    async def close(self) -> None:
        """Close the persistent HTTP client."""
        if self._persistent_client and not self._persistent_client.is_closed:
            await self._persistent_client.aclose()
            self._persistent_client = None

    async def _rate_limit_delay(self) -> None:
        """Enforce minimum inter-request interval to prevent burst patterns.

        Reads the provider's ``min_request_interval`` and sleeps for the
        remaining time if the last request was too recent.
        """
        rl = self._get_rate_limit_config()
        min_interval = rl.get("min_request_interval", 1.0)
        elapsed = time.monotonic() - self._last_request_time
        if elapsed < min_interval:
            wait = min_interval - elapsed
            logger.info("[RateLimit] Throttling: waiting %.1fs before next request", wait)
            await asyncio.sleep(wait)
        self._last_request_time = time.monotonic()

    async def _stream_with_retry(
        self,
        client: httpx.AsyncClient,
        payload: dict,
        provider_name: str,
    ) -> AsyncGenerator[str, None]:
        """Stream a POST /chat/completions request with automatic retry on 429.

        On a 429 response, waits for ``Retry-After`` seconds (or exponential
        backoff) and retries up to ``max_retries`` times. Non-429 errors are
        yielded as error strings immediately (no retry).
        """
        rl = self._get_rate_limit_config()
        max_retries = rl.get("max_retries", 3)
        base_backoff = rl.get("base_backoff", 1.0)

        for attempt in range(max_retries + 1):
            # Throttle between requests
            await self._rate_limit_delay()

            try:
                async with client.stream("POST", "/chat/completions", json=payload) as response:
                    if response.status_code == 429:
                        # Parse Retry-After header if present
                        retry_after = response.headers.get("retry-after")
                        if retry_after:
                            try:
                                wait_time = float(retry_after)
                            except ValueError:
                                wait_time = base_backoff * (2 ** attempt)
                        else:
                            wait_time = base_backoff * (2 ** attempt)

                        # Consume the response body so httpx releases the connection
                        await response.aread()

                        if attempt < max_retries:
                            logger.warning(
                                "[RateLimit] 429 from %s (attempt %d/%d). Retrying in %.1fs...",
                                provider_name, attempt + 1, max_retries + 1, wait_time,
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            logger.error(
                                "[RateLimit] 429 from %s — all %d retries exhausted.",
                                provider_name, max_retries + 1,
                            )
                            yield self._handle_429_error(provider_name, wait_time)
                            return

                    if response.status_code != 200:
                        error_text = await response.aread()
                        logger.error(
                            "%s API error %d: %s",
                            provider_name, response.status_code, error_text,
                        )
                        yield self._handle_stream_error(response, provider_name)
                        return

                    # Successful response — stream SSE chunks
                    async for chunk in self._parse_sse_stream(response, provider_name):
                        yield chunk
                    return

            except httpx.TimeoutException:
                yield "Error: Request timed out. Check your internet connection."
                return
            except Exception as e:
                logger.error("%s API error: %s", provider_name, e, exc_info=True)
                yield f"Error: {e}"
                return

        # Should not reach here, but just in case
        yield "Error: Rate limit exceeded after all retries."

    @staticmethod
    def _handle_429_error(provider_name: str, last_wait: float) -> str:
        """User-friendly error message for 429 after all retries are exhausted."""
        return (
            f"⚠️ Rate limit exceeded ({provider_name}). "
            f"The API is receiving too many requests. "
            f"VDA retried automatically but the limit persists. "
            f"Please wait ~{int(last_wait * 2)}s and try again, "
            f"or switch to a provider with higher rate limits."
        )

    @staticmethod
    def _get_system_prompt(vision_mode: bool = False) -> str:
        return build_system_prompt(vision_mode=vision_mode)

    def _ensure_system_prompt(self, messages: list, vision_mode: bool) -> None:
        if vision_mode:
            has_system = any(m.get("role") == "system" for m in messages)
            if not has_system:
                messages.insert(0, {"role": "system", "content": self._get_system_prompt(vision_mode=True)})
        else:
            # Chat mode: always inject the chat assistant prompt so the LLM
            # knows it is in chat mode and should NOT emit JSON action blocks.
            has_system = any(m.get("role") == "system" for m in messages)
            if not has_system:
                messages.insert(0, {"role": "system", "content": self._get_system_prompt(vision_mode=False)})

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

    def _build_payload(self, model: str, messages: list, temperature: float = 0.7, max_tokens: Optional[int] = None) -> dict:
        # OpenCode Strategy: Keep only the most recent image to save massive amounts of tokens
        # and prevent 'Too Many Requests' on limited providers like Nvidia NIM.
        processed_messages = []
        for i, msg in enumerate(messages):
            if isinstance(msg.get("content"), list):
                new_content = []
                for block in msg["content"]:
                    if block.get("type") == "image_url":
                        # If this is not the last message, replace image with text placeholder
                        if i < len(messages) - 1:
                            new_content.append({"type": "text", "text": "[Screenshot removed to save tokens]"})
                        else:
                            # Add detail: low to the last image to guarantee API resizes it
                            block["image_url"]["detail"] = "low"
                            new_content.append(block)
                    else:
                        new_content.append(block)
                processed_messages.append({"role": msg["role"], "content": new_content})
            else:
                processed_messages.append(msg)

        payload = {
            "model": model,
            "messages": processed_messages,
            "stream": True,
            "temperature": temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        return payload

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
        if response.status_code == 429:
            return self._handle_429_error(provider_name, 5.0)
        return f"Error: API returned {response.status_code}. Check your API key and model name."
