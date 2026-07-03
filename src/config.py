r"""Configuration management for SteamVR Wallpaper Pause.

Stores configuration in %APPDATA%\SteamVRWallpaperPause\config.json.
"""

import os
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

APP_NAME = "SteamVRWallpaperPause"
_VALID_ACTIONS = ("pause", "stop")

DEFAULT_CONFIG: dict[str, str | int | bool] = {
    "polling_interval": 5,
    "wallpaper_engine_path": "auto",
    "auto_start": True,
    "verbose": False,
    "action_on_vr_start": "stop",
}


def _get_config_dir() -> Path:
    """Get the application config directory, creating it if needed."""
    appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
    config_dir = Path(appdata) / APP_NAME
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def _get_config_path() -> Path:
    """Get the full path to config.json."""
    return _get_config_dir() / "config.json"


class Config:
    """Application configuration loaded from disk with defaults."""

    _data: dict[str, str | int | bool]

    def __init__(self, cli_overrides: dict | None = None):
        """Load configuration, with optional CLI argument overrides.

        Args:
            cli_overrides: Dict of config keys to override (e.g., from argparse).
        """
        self._data = dict(DEFAULT_CONFIG)
        self._load_from_file()
        if cli_overrides:
            self._data.update({k: v for k, v in cli_overrides.items() if v is not None})

    def _load_from_file(self) -> None:
        """Load configuration from config.json if it exists."""
        config_path = _get_config_path()
        try:
            if config_path.is_file():
                with open(config_path, "r", encoding="utf-8") as f:
                    file_data = json.load(f)
                # Only accept known keys
                for key in DEFAULT_CONFIG:
                    if key in file_data:
                        self._data[key] = file_data[key]
                logger.debug(f"Loaded config from {config_path}")
            else:
                # First run — create the config directory and file
                self.save()
                logger.info(f"Created default config at {config_path}")
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Error reading config file: {e}. Using defaults.")

    def save(self) -> None:
        """Save current configuration to config.json."""
        config_path = _get_config_path()
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
            logger.debug(f"Saved config to {config_path}")
        except OSError as e:
            logger.error(f"Error saving config file: {e}")

    @property
    def polling_interval(self) -> int:
        return max(1, int(self._data["polling_interval"]))

    @polling_interval.setter
    def polling_interval(self, value: int) -> None:
        self._data["polling_interval"] = max(1, int(value))

    @property
    def wallpaper_engine_path(self) -> str:
        return str(self._data["wallpaper_engine_path"])

    @wallpaper_engine_path.setter
    def wallpaper_engine_path(self, value: str) -> None:
        self._data["wallpaper_engine_path"] = value

    @property
    def auto_start(self) -> bool:
        return bool(self._data["auto_start"])

    @auto_start.setter
    def auto_start(self, value: bool) -> None:
        self._data["auto_start"] = bool(value)

    @property
    def verbose(self) -> bool:
        return bool(self._data["verbose"])

    @verbose.setter
    def verbose(self, value: bool) -> None:
        self._data["verbose"] = bool(value)

    @property
    def action_on_vr_start(self) -> str:
        val = self._data.get("action_on_vr_start", "pause")
        return val if val in _VALID_ACTIONS else "pause"

    @action_on_vr_start.setter
    def action_on_vr_start(self, value: str) -> None:
        if value not in _VALID_ACTIONS:
            raise ValueError(f"action_on_vr_start must be one of {_VALID_ACTIONS}")
        self._data["action_on_vr_start"] = value

    def to_dict(self) -> dict:
        return dict(self._data)

    def get_explicit_path(self) -> str | None:
        """Get wallpaper engine path if it's an explicit path (not 'auto')."""
        p = self.wallpaper_engine_path
        if p and p != "auto":
            return p
        return None
