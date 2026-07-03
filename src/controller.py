"""Wallpaper Engine control via its command-line interface."""

import subprocess
import os
import logging
import winreg

logger = logging.getLogger(__name__)

_WALLPAPER_EXE = "wallpaper32.exe"
_DEFAULT_STEAM_PATH = r"C:\Program Files (x86)\Steam\steamapps\common\wallpaper_engine"
_STEAM_REGISTRY_KEY = r"Software\Valve\Steam"


def find_wallpaper_engine(explicit_path: str | None = None) -> str | None:
    """Locate wallpaper32.exe on the system.

    Resolution order:
    1. Explicit path if provided
    2. Default Steam library path
    3. Steam registry key → library folders → wallpaper_engine

    Args:
        explicit_path: Optional user-specified path to wallpaper32.exe.

    Returns:
        Full path to wallpaper32.exe, or None if not found.
    """
    # 1. Explicit path
    if explicit_path and explicit_path != "auto":
        full = os.path.join(explicit_path, _WALLPAPER_EXE) if os.path.isdir(explicit_path) else explicit_path
        if os.path.isfile(full):
            logger.info(f"Using explicit wallpaper engine path: {full}")
            return full
        logger.warning(f"Explicit path not found: {full}")

    # 2. Default Steam path
    default_full = os.path.join(_DEFAULT_STEAM_PATH, _WALLPAPER_EXE)
    if os.path.isfile(default_full):
        logger.info(f"Found wallpaper engine at default path: {default_full}")
        return default_full

    # 3. Search via Steam registry
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _STEAM_REGISTRY_KEY)
        steam_path, _ = winreg.QueryValueEx(key, "SteamPath")
        winreg.CloseKey(key)

        # Default library: Steam\steamapps\common\wallpaper_engine
        candidate = os.path.join(steam_path, "steamapps", "common", "wallpaper_engine", _WALLPAPER_EXE)
        if os.path.isfile(candidate):
            logger.info(f"Found wallpaper engine via Steam registry: {candidate}")
            return candidate

        # Check libraryfolders.vdf for additional library paths
        library_folders_path = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
        if os.path.isfile(library_folders_path):
            library_paths = _parse_library_folders(library_folders_path)
            for lib_path in library_paths:
                candidate = os.path.join(lib_path, "steamapps", "common", "wallpaper_engine", _WALLPAPER_EXE)
                if os.path.isfile(candidate):
                    logger.info(f"Found wallpaper engine in Steam library: {candidate}")
                    return candidate

    except (OSError, FileNotFoundError):
        logger.debug("Steam registry key not found")

    logger.error("Could not locate wallpaper32.exe")
    return None


def _parse_library_folders(vdf_path: str) -> list[str]:
    """Parse Steam's libraryfolders.vdf to extract library paths.

    This is a minimal parser for the Valve Data Format used by Steam.
    It looks for "path" entries in the library folders configuration.
    """
    paths: list[str] = []
    try:
        with open(vdf_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Simple regex-free parsing: look for lines with "path"
        for line in content.split("\n"):
            stripped = line.strip()
            if stripped.startswith('"path"'):
                # Format: "path"\t\t"<path>"
                # Extract the quoted path value
                parts = stripped.split('"')
                if len(parts) >= 4:
                    path = parts[3]
                    # Convert Steam's escaped backslashes to real backslashes
                    path = path.replace("\\\\", "\\")
                    paths.append(path)
    except Exception as e:
        logger.warning(f"Error parsing libraryfolders.vdf: {e}")

    return paths


def pause_wallpaper(path: str) -> bool:
    """Pause Wallpaper Engine via -control pause.

    Args:
        path: Full path to wallpaper32.exe.

    Returns:
        True if the command succeeded, False otherwise.
    """
    return _run_control_command(path, "pause")


def resume_wallpaper(path: str) -> bool:
    """Resume Wallpaper Engine via -control play.

    Args:
        path: Full path to wallpaper32.exe.

    Returns:
        True if the command succeeded, False otherwise.
    """
    return _run_control_command(path, "play")


def stop_wallpaper(path: str) -> bool:
    """Stop Wallpaper Engine via -control stop.

    Args:
        path: Full path to wallpaper32.exe.

    Returns:
        True if the command succeeded, False otherwise.
    """
    return _run_control_command(path, "stop")


def _run_control_command(exe_path: str, action: str) -> bool:
    """Execute a wallpaper32.exe control command.

    Args:
        exe_path: Full path to wallpaper32.exe.
        action: "pause" or "play".

    Returns:
        True if the command returned exit code 0, False otherwise.
    """
    if not os.path.isfile(exe_path):
        logger.error(f"Wallpaper engine executable not found: {exe_path}")
        return False

    try:
        result = subprocess.run(
            [exe_path, "-control", action],
            capture_output=True,
            text=True,
            timeout=10,  # Should complete almost instantly
        )
        if result.returncode == 0:
            logger.info(f"Wallpaper Engine {action} succeeded")
            return True
        else:
            logger.warning(
                f"Wallpaper Engine {action} returned code {result.returncode}: "
                f"{result.stderr.strip()}"
            )
            return False

    except subprocess.TimeoutExpired:
        logger.error(f"Wallpaper Engine {action} timed out after 10s")
        return False
    except Exception as e:
        logger.error(f"Error running wallpaper32.exe: {e}")
        return False
