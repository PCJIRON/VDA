"""
Settings management for Qwen Desktop.

Handles loading, saving, and accessing application settings.
"""

import json
from pathlib import Path
from typing import Any, Optional

from PyQt6.QtCore import QSettings

from qwen_desktop.config.defaults import DEFAULT_SETTINGS


class Settings:
    """Application settings manager.
    
    Provides access to user settings with defaults and persistence.
    """

    def __init__(self, config_path: Optional[Path] = None) -> None:
        """Initialize settings.
        
        Args:
            config_path: Optional path to config file.
        """
        self._settings: dict[str, Any] = DEFAULT_SETTINGS.copy()
        self._config_path = config_path or self._get_default_config_path()
        self._qt_settings = QSettings("Qwen", "Qwen Desktop")
        
        # Load settings
        self._load()

    def _get_default_config_path(self) -> Path:
        """Get default configuration file path.
        
        Returns:
            Path to config file.
        """
        # Use platform-specific app data directory
        from qwen_desktop.utils.platform import is_windows, is_macos, is_linux
        
        if is_windows():
            base = Path.home() / "AppData" / "Local" / "Qwen" / "Qwen Desktop"
        elif is_macos():
            base = Path.home() / "Library" / "Preferences" / "Qwen"
        elif is_linux():
            base = Path.home() / ".config" / "qwen-desktop"
        else:
            base = Path.home() / ".qwen-desktop"
        
        return base / "config.json"

    def _load(self) -> None:
        """Load settings from file and QSettings."""
        # Load from config file
        if self._config_path.exists():
            try:
                with open(self._config_path, "r", encoding="utf-8") as f:
                    file_settings = json.load(f)
                    self._settings.update(file_settings)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load config file: {e}")
        
        # Override with QSettings (for sensitive data)
        for key in self._settings:
            value = self._qt_settings.value(f"settings/{key}")
            if value is not None:
                self._settings[key] = value

    def save(self) -> None:
        """Save settings to file."""
        # Ensure directory exists
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to file
        with open(self._config_path, "w", encoding="utf-8") as f:
            json.dump(self._settings, f, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value.
        
        Args:
            key: Setting key.
            default: Default value if not found.
            
        Returns:
            Setting value.
        """
        return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a setting value.
        
        Args:
            key: Setting key.
            value: Setting value.
        """
        self._settings[key] = value
        self._qt_settings.setValue(f"settings/{key}", value)

    def reset(self, key: str) -> None:
        """Reset a setting to its default value.
        
        Args:
            key: Setting key to reset.
        """
        if key in DEFAULT_SETTINGS:
            self._settings[key] = DEFAULT_SETTINGS[key]

    def reset_all(self) -> None:
        """Reset all settings to defaults."""
        self._settings = DEFAULT_SETTINGS.copy()

    @property
    def all(self) -> dict[str, Any]:
        """Get all settings.
        
        Returns:
            Dictionary of all settings.
        """
        return self._settings.copy()
