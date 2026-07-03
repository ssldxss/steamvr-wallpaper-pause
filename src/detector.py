"""SteamVR process detection using psutil."""

import psutil
import logging

logger = logging.getLogger(__name__)

# Process names that indicate SteamVR is running (case-insensitive)
_PRIMARY_PROCESS = "vrserver.exe"
_FALLBACK_PROCESS = "vrmonitor.exe"


def is_steamvr_running() -> bool:
    """Check if SteamVR is currently running.

    Checks for vrserver.exe first (the core SteamVR server that runs for
    the entire VR session). Falls back to vrmonitor.exe (dashboard process).

    Returns:
        True if SteamVR appears to be running, False otherwise.
    """
    try:
        # Use attrs to minimize overhead — we only need the process name
        for proc in psutil.process_iter(attrs=["name"]):
            try:
                name = proc.info["name"] or ""
                name_lower = name.lower()

                if name_lower == _PRIMARY_PROCESS:
                    return True
                if name_lower == _FALLBACK_PROCESS:
                    return True

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # Process terminated between iteration and access, or
                # we don't have permission to read it — skip safely
                continue

    except Exception as e:
        logger.warning(f"Error iterating processes: {e}")

    return False
