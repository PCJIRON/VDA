import json
from pathlib import Path
from typing import Any, Optional

from qwen_desktop.config.defaults import DEFAULT_SETTINGS


class Settings:
    def __init__(self, config_path: Optional[Path] = None) -> None:
        self._settings: dict[str, Any] = DEFAULT_SETTINGS.copy()
        self._config_path = config_path or self._get_default_config_path()
        self._load()

    def _get_default_config_path(self) -> Path:
        from qwen_desktop.utils.platform import is_windows, is_macos, is_linux
        if is_windows():
            base = Path.home() / "AppData" / "Local" / "QwenDesktop"
        elif is_macos():
            base = Path.home() / "Library" / "Preferences" / "QwenDesktop"
        elif is_linux():
            base = Path.home() / ".config" / "qwen-desktop"
        else:
            base = Path.home() / ".qwen-desktop"
        return base / "config.json"

    def _load(self) -> None:
        if self._config_path.exists():
            try:
                with open(self._config_path, "r", encoding="utf-8") as f:
                    file_settings = json.load(f)
                    self._settings.update(file_settings)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load config file: {e}")

    def save(self) -> None:
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._config_path, "w", encoding="utf-8") as f:
            json.dump(self._settings, f, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._settings[key] = value

    def reset(self, key: str) -> None:
        if key in DEFAULT_SETTINGS:
            self._settings[key] = DEFAULT_SETTINGS[key]

    def reset_all(self) -> None:
        self._settings = DEFAULT_SETTINGS.copy()

    @property
    def all(self) -> dict[str, Any]:
        return self._settings.copy()
