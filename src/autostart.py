"""Windows auto-start management via registry Run key."""

import sys
import os
import logging
import winreg

logger = logging.getLogger(__name__)

_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_VALUE_NAME = "SteamVRWallpaperPause"


def _get_exe_path() -> str:
    """Get the path to use for the auto-start registry entry.

    When running as a PyInstaller bundle, use sys.executable.
    When running as a script, use the Python interpreter + main.py.
    """
    if getattr(sys, "frozen", False):
        # Running as PyInstaller bundle
        return sys.executable

    # Running as script — construct command to launch main.py
    python = sys.executable
    main_py = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
    return f'"{python}" "{main_py}"'


def enable_autostart() -> bool:
    """Register the application to start with Windows.

    Returns:
        True if the registry key was written successfully.
    """
    exe_path = _get_exe_path()
    # Add --minimized so it starts to tray without showing a window
    command = f'"{exe_path}" --minimized'

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, _VALUE_NAME, 0, winreg.REG_SZ, command)
        winreg.CloseKey(key)
        logger.info(f"Auto-start enabled: {command}")
        return True
    except OSError as e:
        logger.error(f"Failed to enable auto-start: {e}")
        return False


def disable_autostart() -> bool:
    """Remove the application from Windows startup.

    Returns:
        True if the registry key was removed successfully (or didn't exist).
    """
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _RUN_KEY, 0,
            winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE
        )
        try:
            winreg.QueryValueEx(key, _VALUE_NAME)
            winreg.DeleteValue(key, _VALUE_NAME)
            logger.info("Auto-start disabled (registry key removed)")
        except FileNotFoundError:
            # Key doesn't exist — that's fine
            logger.debug("Auto-start key already absent")
        winreg.CloseKey(key)
        return True
    except OSError as e:
        logger.error(f"Failed to disable auto-start: {e}")
        return False


def is_autostart_enabled() -> bool:
    """Check if the application is registered to start with Windows.

    Returns:
        True if the registry Run key exists.
    """
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_READ
        )
        try:
            winreg.QueryValueEx(key, _VALUE_NAME)
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            winreg.CloseKey(key)
            return False
    except OSError:
        return False
