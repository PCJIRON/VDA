from dataclasses import dataclass
from typing import Optional

from qwen_desktop.config.defaults import PROVIDERS


@dataclass
class ModelInfo:
    id: str
    name: str
    description: str = ""
    max_tokens: int = 8192
    supports_vision: bool = False
    supports_function_calling: bool = False

    @classmethod
    def get_default_models(cls) -> list["ModelInfo"]:
        models = []
        for pid, info in PROVIDERS.items():
            for mid in info.get("models", []):
                models.append(cls(
                    id=mid,
                    name=f"{info['name']}: {mid}",
                    description=f"via {info['name']}",
                    max_tokens=8192,
                    supports_vision=True,
                    supports_function_calling=True,
                ))
        return models

    @classmethod
    def get_provider_models(cls, provider_id: str) -> list["ModelInfo"]:
        info = PROVIDERS.get(provider_id, {})
        return [cls(
            id=mid,
            name=f"{info.get('name', provider_id)}: {mid}",
            description=f"via {info.get('name', provider_id)}",
            max_tokens=8192,
            supports_vision=True,
            supports_function_calling=True,
        ) for mid in info.get("models", [])]


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    @classmethod
    def from_api_response(cls, data: dict) -> "TokenUsage":
        return cls(
            prompt_tokens=data.get("prompt_tokens", 0),
            completion_tokens=data.get("completion_tokens", 0),
            total_tokens=data.get("total_tokens", 0),
        )
