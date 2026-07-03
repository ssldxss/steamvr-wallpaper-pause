"""System tray icon and menu for SteamVR Wallpaper Pause."""

import logging
from typing import Callable

import pystray
from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)

# Constants for icon drawing
_ICON_SIZE = 64
_GREEN = (0, 180, 80)
_ORANGE = (255, 160, 30)

# Callback type aliases
OnPauseCallback = Callable[[], bool]
OnResumeCallback = Callable[[], bool]
OnExitCallback = Callable[[], None]
OnSettingsCallback = Callable[[], None]


def _create_icon_image(color: tuple[int, int, int]) -> Image.Image:
    """Create a circular icon of the given color.

    Args:
        color: RGB tuple for the circle fill.

    Returns:
        A Pillow Image with a colored circle on transparent background.
    """
    image = Image.new("RGBA", (_ICON_SIZE, _ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    padding = 4
    draw.ellipse(
        [padding, padding, _ICON_SIZE - padding - 1, _ICON_SIZE - padding - 1],
        fill=color,
        outline=(255, 255, 255, 200),
        width=2,
    )
    return image


class TrayApp:
    """Manages the system tray icon, menu, and notifications."""

    def __init__(
        self,
        on_pause: OnPauseCallback,
        on_resume: OnResumeCallback,
        on_settings: OnSettingsCallback,
        on_exit: OnExitCallback,
    ):
        """Initialize the tray application.

        Args:
            on_pause: Called when user clicks "Pause Wallpaper". Returns True if successful.
            on_resume: Called when user clicks "Resume Wallpaper". Returns True if successful.
            on_settings: Called when user clicks "Settings".
            on_exit: Called when user clicks "Exit".
        """
        self._on_pause = on_pause
        self._on_resume = on_resume
        self._on_settings = on_settings
        self._on_exit = on_exit

        self._icon_green = _create_icon_image(_GREEN)
        self._icon_orange = _create_icon_image(_ORANGE)

        self._wallpaper_paused = False
        self._vr_running = False
        self._icon: pystray.Icon | None = None

    @property
    def wallpaper_paused(self) -> bool:
        return self._wallpaper_paused

    @wallpaper_paused.setter
    def wallpaper_paused(self, value: bool) -> None:
        self._wallpaper_paused = value
        self._update_icon()

    @property
    def vr_running(self) -> bool:
        return self._vr_running

    @vr_running.setter
    def vr_running(self, value: bool) -> None:
        self._vr_running = value
        self._update_icon()

    def _update_icon(self) -> None:
        """Update the tray icon based on current state."""
        if self._icon is None:
            return

        if self._vr_running:
            self._icon.icon = self._icon_orange
        else:
            self._icon.icon = self._icon_green

        self._icon.update_menu()

    def _build_menu(self) -> pystray.Menu:
        """Build the right-click context menu."""

        # Status display item (disabled — shows current state)
        if self._vr_running:
            status_text = "Status: VR Active — Wallpaper Paused"
        elif self._wallpaper_paused:
            status_text = "Status: Wallpaper Paused (manual)"
        else:
            status_text = "Status: Monitoring"

        # Manual toggle item
        if self._wallpaper_paused:
            toggle_item = pystray.MenuItem(
                "Resume Wallpaper",
                self._on_manual_resume,
                default=True,
            )
        else:
            toggle_item = pystray.MenuItem(
                "Pause Wallpaper",
                self._on_manual_pause,
                default=True,
            )

        return pystray.Menu(
            pystray.MenuItem(status_text, None, enabled=False),
            pystray.Menu.SEPARATOR,
            toggle_item,
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Settings", self._on_settings_click),
            pystray.MenuItem("Exit", self._on_exit_click),
        )

    def _on_manual_pause(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        """Handle manual pause via tray menu."""
        success = self._on_pause()
        if success:
            self._wallpaper_paused = True
            icon.update_menu()
            icon.notify("Wallpaper Engine paused", "SteamVR Wallpaper Pause")

    def _on_manual_resume(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        """Handle manual resume via tray menu."""
        success = self._on_resume()
        if success:
            self._wallpaper_paused = False
            icon.update_menu()
            icon.notify("Wallpaper Engine resumed", "SteamVR Wallpaper Pause")

    def _on_settings_click(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        """Open the settings window."""
        self._on_settings()

    def _on_exit_click(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        """Handle exit from tray menu."""
        self._on_exit()
        if self._icon:
            self._icon.stop()

    def notify_pause(self) -> None:
        """Show a notification that Wallpaper Engine was paused for VR."""
        if self._icon:
            self._icon.notify(
                "Wallpaper Engine paused — SteamVR is running",
                "SteamVR Wallpaper Pause",
            )

    def notify_resume(self) -> None:
        """Show a notification that Wallpaper Engine was resumed."""
        if self._icon:
            self._icon.notify(
                "Wallpaper Engine resumed — SteamVR closed",
                "SteamVR Wallpaper Pause",
            )

    def notify_error(self, message: str) -> None:
        """Show an error notification."""
        if self._icon:
            self._icon.notify(message, "SteamVR Wallpaper Pause")

    def run(self) -> None:
        """Start the system tray icon and enter the event loop.

        This is blocking — runs until the user exits via the tray menu.
        """
        self._icon = pystray.Icon(
            "SteamVRWallpaperPause",
            self._icon_green,
            "SteamVR Wallpaper Pause",
            menu=self._build_menu(),
        )

        # Run the tray icon in the main thread
        self._icon.run()

    def stop(self) -> None:
        """Stop the tray icon and exit the event loop."""
        if self._icon:
            self._icon.stop()
            self._icon = None
