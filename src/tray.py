r"""System tray icon and menu for SteamVR Wallpaper Pause."""

import logging
from typing import Callable

import pystray
from PIL import Image, ImageDraw

from i18n import t, Lang

logger = logging.getLogger(__name__)

_ICON_SIZE = 64
_GREEN = (0, 180, 80)
_YELLOW = (255, 160, 32)
_RED = (224, 64, 64)

OnPauseCallback = Callable[[], bool]
OnResumeCallback = Callable[[], bool]
OnExitCallback = Callable[[], None]
OnSettingsCallback = Callable[[], None]


def _create_icon_image(color: tuple[int, int, int]) -> Image.Image:
    """Create a circular icon of the given color."""
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
        lang: Lang,
        on_settings: OnSettingsCallback,
        on_exit: OnExitCallback,
    ):
        self._lang = lang
        self._on_settings = on_settings
        self._on_exit = on_exit

        self._icon_green = _create_icon_image(_GREEN)
        self._icon_yellow = _create_icon_image(_YELLOW)
        self._icon_red = _create_icon_image(_RED)

        self._wallpaper_paused = False
        self._vr_running = False
        self._is_stopped = False
        self._icon: pystray.Icon | None = None

    @property
    def lang(self) -> Lang:
        return self._lang

    @lang.setter
    def lang(self, value: Lang) -> None:
        self._lang = value
        if self._icon:
            self._icon.update_menu()

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

    @property
    def is_stopped(self) -> bool:
        return self._is_stopped

    @is_stopped.setter
    def is_stopped(self, value: bool) -> None:
        self._is_stopped = value
        if self._icon:
            self._icon.update_menu()

    def _update_icon(self) -> None:
        """Update the tray icon based on current state."""
        if self._icon is None:
            return
        if self._vr_running:
            self._icon.icon = self._icon_red
        elif self._wallpaper_paused:
            self._icon.icon = self._icon_yellow
        else:
            self._icon.icon = self._icon_green
        self._icon.update_menu()

    def _build_menu(self) -> pystray.Menu:
        """Build the right-click context menu (no manual pause/resume)."""
        if self._vr_running and self._is_stopped:
            status_text = t("status_vr_stopped", self._lang)
        elif self._vr_running:
            status_text = t("status_vr_active", self._lang)
        elif self._wallpaper_paused:
            status_text = t("status_vr_active", self._lang)
        else:
            status_text = t("status_monitoring", self._lang)

        return pystray.Menu(
            pystray.MenuItem(status_text, None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(t("settings", self._lang), self._on_settings_click),
            pystray.MenuItem(t("exit", self._lang), self._on_exit_click),
        )

    def _on_settings_click(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        self._on_settings()

    def _on_exit_click(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        self._on_exit()
        if self._icon:
            self._icon.stop()

    def notify_pause(self) -> None:
        if self._icon:
            self._icon.notify(
                t("notify_pause", self._lang),
                t("tray_tooltip", self._lang),
            )

    def notify_stop(self) -> None:
        if self._icon:
            self._icon.notify(
                t("notify_stop", self._lang),
                t("tray_tooltip", self._lang),
            )

    def notify_resume(self) -> None:
        if self._icon:
            self._icon.notify(
                t("notify_resume", self._lang),
                t("tray_tooltip", self._lang),
            )

    def notify_error(self, message: str) -> None:
        if self._icon:
            self._icon.notify(message, t("tray_tooltip", self._lang))

    def run(self) -> None:
        """Start the system tray icon (blocking)."""
        self._icon = pystray.Icon(
            "SteamVRWallpaperPause",
            self._icon_green,
            t("tray_tooltip", self._lang),
            menu=self._build_menu(),
        )
        self._icon.run()

    def stop(self) -> None:
        """Stop the tray icon."""
        if self._icon:
            self._icon.stop()
            self._icon = None
