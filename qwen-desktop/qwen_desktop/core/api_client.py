from typing import Optional, AsyncGenerator, List, Dict, Any, Tuple
import json
import logging

import httpx

from qwen_desktop.config.settings import Settings
from qwen_desktop.auth.provider_config import ProviderConfig


logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    pass


class APIClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._config = ProviderConfig(settings)

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

    def _create_client(self) -> httpx.AsyncClient:
        base_url = self._config.get_base_url().rstrip("/")
        return httpx.AsyncClient(
            base_url=base_url,
            headers=self._get_headers(),
            timeout=httpx.Timeout(self.settings.get("api_timeout", 120)),
        )

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

    VISION_SYSTEM_PROMPT = (
        "You are an expert desktop automation assistant with vision capabilities.\n\n"
        "=== YOUR TASK ===\n"
        "When you receive a screenshot with mouse coordinates:\n"
        "1. Analyze all visible UI elements\n"
        "2. Find the target element based on user request\n"
        "3. Return EXACT pixel coordinates [x, y] for the action\n\n"
        "=== COORDINATE RULES ===\n"
        "- Screen resolution: {W}x{H}\n"
        "- Valid X range: 0 to {W}\n"
        "- Valid Y range: 0 to {H}\n"
        "- Origin (0,0) is TOP-LEFT corner\n"
        "- X increases going RIGHT\n"
        "- Y increases going DOWN\n\n"
        "=== OUTPUT FORMAT ===\n"
        "Respond in this EXACT JSON format:\n"
        "{\n"
        '  "action": "click",\n'
        '  "target": [x, y],\n'
        '  "confidence": 0.95,\n'
        '  "description": "Found Submit button at bottom of form"\n'
        "}\n\n"
        "Action types: click, double_click, right_click, move, drag_start, drag_end\n\n"
        "=== IMPORTANT ===\n"
        "- Be PRECISE - user will click exactly where you specify\n"
        "- Center of buttons/icons is usually the best target\n"
        "- If multiple elements match, pick the most prominent one\n"
        "- If unsure, ask for clarification in description\n"
        "- Never return coordinates outside screen bounds\n\n"
        "=== ALTERNATIVE FORMAT ===\n"
        "You can also use PyAutoGUI format:\n"
        "[PYAUTOGUI]\n"
        "pyautogui.moveTo(x, y, duration=0.3)\n"
        "pyautogui.click(x, y)\n"
        "[/PYAUTOGUI]"
    )

    async def send_message(
        self,
        message: str,
        conversation_history: List[Dict[str, Any]],
        attachments: Optional[List] = None,
        vision_mode: bool = False,
    ) -> AsyncGenerator[str, None]:
        model = self._config.get_model()
        client = self._create_client()

        messages = conversation_history.copy()

        if vision_mode:
            has_system = any(m.get("role") == "system" for m in messages)
            if not has_system:
                messages.insert(0, {"role": "system", "content": self.VISION_SYSTEM_PROMPT})

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
                    user_content[0]["text"] += f"\n\n<document path='{fname}'>\n{doc_text}\n</document>"

        messages.append({"role": "user", "content": user_content})

        provider_name = self._config.get_provider_name()
        logger.info(f"Sending {len(messages)} messages to {provider_name} model {model}")

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
                    logger.error(f"{provider_name} API error {response.status_code}: {error_text}")
                    yield f"Error: API returned {response.status_code}. Check your API key and model name."
                    return

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
