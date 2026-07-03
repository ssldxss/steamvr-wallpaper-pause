"""SteamVR Wallpaper Pause — Main entry point.

Monitors SteamVR process state and controls Wallpaper Engine accordingly.
Runs as a system tray application with optional console logging.
"""

import argparse
import logging
import os
import sys

# Support both direct script execution and PyInstaller bundle.
# When run as `python -m src.main` or via PyInstaller, the src dir
# should be on sys.path. When run as `python src/main.py`, add it.
_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from config import Config  # noqa: E402
from detector import is_steamvr_running  # noqa: E402
from controller import find_wallpaper_engine, pause_wallpaper, resume_wallpaper  # noqa: E402
from autostart import enable_autostart, disable_autostart, is_autostart_enabled  # noqa: E402
from tray import TrayApp  # noqa: E402
from settings import SettingsWindow  # noqa: E402

import threading  # noqa: E402
import time  # noqa: E402
import tkinter as tk  # noqa: E402

logger = logging.getLogger("steamvr_wallpaper_pause")


class Monitor:
    """Main application that monitors SteamVR and controls Wallpaper Engine."""

    def __init__(self, config: Config):
        self._config = config
        self._steamvr_running = False
        self._paused_by_us = False
        self._wallpaper_path: str | None = None
        self._running = False
        self._tray_app: TrayApp | None = None
        self._monitor_thread: threading.Thread | None = None
        self._settings_window: SettingsWindow | None = None
        self._tk_root: tk.Tk | None = None

    def run(self) -> None:
        """Start the application: tkinter root + tray icon + monitoring loop."""
        logger.info("Starting SteamVR Wallpaper Pause")

        # Locate wallpaper engine
        self._wallpaper_path = find_wallpaper_engine(
            self._config.get_explicit_path()
        )
        if not self._wallpaper_path:
            logger.warning(
                "Could not find wallpaper32.exe. "
                "Wallpaper Engine control will be disabled. "
                "Set the path in Settings."
            )

        # Startup check: if SteamVR is not running, ensure wallpaper is resumed
        if not is_steamvr_running() and self._wallpaper_path:
            logger.info("Startup check: SteamVR not running, ensuring wallpaper resumed")
            resume_wallpaper(self._wallpaper_path)

        # Sync auto-start state with config
        if self._config.auto_start != is_autostart_enabled():
            if self._config.auto_start:
                enable_autostart()
            else:
                disable_autostart()

        # Create hidden tkinter root (main thread owns tkinter)
        self._tk_root = tk.Tk()
        self._tk_root.withdraw()

        # Set up system tray
        self._tray_app = TrayApp(
            on_pause=self._handle_manual_pause,
            on_resume=self._handle_manual_resume,
            on_settings=self._show_settings,
            on_exit=self._handle_exit,
        )

        # Start monitoring in background thread
        self._running = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop, daemon=True, name="monitor"
        )
        self._monitor_thread.start()

        # Initialize settings window factory
        def on_saved():
            new_path = find_wallpaper_engine(self._config.get_explicit_path())
            if new_path:
                self._wallpaper_path = new_path

        self._settings_window = SettingsWindow(self._config, on_save_callback=on_saved)

        # Run pystray in daemon thread; tkinter mainloop in main thread
        tray_thread = threading.Thread(
            target=self._tray_app.run, daemon=True, name="tray"
        )
        tray_thread.start()

        try:
            self._tk_root.mainloop()
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        finally:
            self._shutdown()

    def _shutdown(self) -> None:
        """Clean shutdown of tray, monitoring, and tkinter."""
        logger.info("Shutting down...")
        self._running = False

        if self._tray_app:
            self._tray_app.stop()

        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2)

        if self._tk_root:
            try:
                self._tk_root.quit()
                self._tk_root.destroy()
            except Exception:
                pass

        logger.info("Shutdown complete")

    def _monitor_loop(self) -> None:
        """Background thread: poll SteamVR state and control wallpaper."""
        heartbeat_count = 0
        while self._running:
            try:
                vr_now = is_steamvr_running()

                if vr_now and not self._steamvr_running:
                    logger.info("SteamVR started — pausing Wallpaper Engine")
                    self._steamvr_running = True
                    if self._tray_app:
                        self._tray_app.vr_running = True

                    if self._wallpaper_path:
                        success = pause_wallpaper(self._wallpaper_path)
                        if success:
                            self._paused_by_us = True
                            if self._tray_app:
                                self._tray_app.wallpaper_paused = True
                                self._tray_app.notify_pause()
                        elif self._tray_app:
                            self._tray_app.notify_error("Failed to pause Wallpaper Engine")
                    else:
                        logger.warning("No wallpaper engine path configured")

                elif not vr_now and self._steamvr_running:
                    logger.info("SteamVR stopped — resuming Wallpaper Engine")
                    self._steamvr_running = False
                    if self._tray_app:
                        self._tray_app.vr_running = False

                    if self._paused_by_us and self._wallpaper_path:
                        success = resume_wallpaper(self._wallpaper_path)
                        if success:
                            self._paused_by_us = False
                            if self._tray_app:
                                self._tray_app.wallpaper_paused = False
                                self._tray_app.notify_resume()
                        elif self._tray_app:
                            self._tray_app.notify_error("Failed to resume Wallpaper Engine")
                    elif self._tray_app:
                        self._tray_app.wallpaper_paused = False

                heartbeat_count += 1
                if self._config.verbose and heartbeat_count % 10 == 0:
                    state = "VR" if self._steamvr_running else "idle"
                    logger.debug(
                        f"Heartbeat [{heartbeat_count}]: SteamVR={state}, "
                        f"paused_by_us={self._paused_by_us}"
                    )

            except Exception as e:
                logger.error(f"Error in monitor loop: {e}", exc_info=True)

            time.sleep(self._config.polling_interval)

    def _handle_manual_pause(self) -> bool:
        """User clicked 'Pause Wallpaper' in tray menu."""
        if self._wallpaper_path:
            success = pause_wallpaper(self._wallpaper_path)
            if success:
                self._paused_by_us = True
                return True
        return False

    def _handle_manual_resume(self) -> bool:
        """User clicked 'Resume Wallpaper' in tray menu."""
        if self._wallpaper_path:
            success = resume_wallpaper(self._wallpaper_path)
            if success:
                self._paused_by_us = False
                return True
        return False

    def _show_settings(self) -> None:
        """Show the settings window (called from tray menu callback)."""
        if self._settings_window and self._tk_root:
            # pystray callbacks come from a background thread.
            # tkinter must be called from the main thread.
            self._tk_root.after(0, self._settings_window.show)

    def _handle_exit(self) -> None:
        """User clicked 'Exit' in tray menu."""
        logger.info("Exit requested from tray menu")
        self._running = False
        if self._tk_root:
            self._tk_root.after(0, self._tk_root.quit)


def _setup_logging(verbose: bool, console_mode: bool) -> None:
    """Configure logging.

    Args:
        verbose: Enable DEBUG level logging.
        console_mode: Also log to stdout (for --console mode).
    """
    level = logging.DEBUG if verbose else logging.INFO
    root_logger = logging.getLogger("steamvr_wallpaper_pause")
    root_logger.setLevel(level)

    if root_logger.handlers:
        return

    appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
    log_dir = os.path.join(appdata, "SteamVRWallpaperPause")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "app.log")

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    root_logger.addHandler(file_handler)

    if console_mode:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%H:%M:%S",
        ))
        root_logger.addHandler(console_handler)


def main() -> None:
    """Application entry point."""
    parser = argparse.ArgumentParser(
        description="SteamVR Wallpaper Pause — Auto-pause Wallpaper Engine during VR"
    )
    parser.add_argument(
        "--interval", type=int, default=None,
        help="Polling interval in seconds (default: 5)",
    )
    parser.add_argument(
        "--wallpaper-engine-path", type=str, default=None,
        help="Path to wallpaper32.exe or its directory",
    )
    parser.add_argument(
        "--console", action="store_true",
        help="Show console window with log output",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Enable verbose (DEBUG) logging",
    )
    parser.add_argument(
        "--minimized", action="store_true",
        help="Start minimized to tray (used by auto-start)",
    )
    parser.add_argument(
        "--remove-autostart", action="store_true",
        help="Remove auto-start registry key and exit (used by uninstaller)",
    )
    args = parser.parse_args()

    # Handle special uninstall cleanup mode
    if args.remove_autostart:
        _setup_logging(verbose=True, console_mode=False)
        logger.info("Removing auto-start registry key (uninstall cleanup)")
        disable_autostart()
        logger.info("Cleanup complete")
        return

    # Build CLI overrides
    cli_overrides = {}
    if args.interval is not None:
        cli_overrides["polling_interval"] = args.interval
    if args.wallpaper_engine_path is not None:
        cli_overrides["wallpaper_engine_path"] = args.wallpaper_engine_path
    if args.verbose:
        cli_overrides["verbose"] = args.verbose

    config = Config(cli_overrides)
    _setup_logging(config.verbose, args.console)

    logger.info("=" * 50)
    logger.info("SteamVR Wallpaper Pause starting")
    logger.info(f"Polling interval: {config.polling_interval}s")
    logger.info(f"Wallpaper engine path: {config.wallpaper_engine_path}")

    monitor = Monitor(config)
    monitor.run()


if __name__ == "__main__":
    main()
