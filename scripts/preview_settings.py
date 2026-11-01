"""Preview the real settings UI without modifying user config or startup entries."""

import argparse
from pathlib import Path
import sys
import tkinter as tk
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import settings
from config import Config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--language", choices=("zh", "en"), default="zh")
    parser.add_argument("--page", choices=("automation", "connection", "advanced"), default="automation")
    parser.add_argument("--size", default="940x720")
    parser.add_argument("--enabled", action="store_true")
    arguments = parser.parse_args()
    with patch.object(Config, "_load_from_file"):
        config = Config({"language": arguments.language, "uu_enabled": arguments.enabled})
    config.save = lambda: None
    root = tk.Tk()
    root.withdraw()
    with (
        patch.object(settings, "is_autostart_enabled", return_value=False),
        patch.object(settings, "enable_autostart", return_value=True),
        patch.object(settings, "disable_autostart", return_value=True),
    ):
        window = settings.SettingsWindow(config)
        window.show()
        window._window.title(window._window.title() + " [Preview]")
        window._window.geometry(arguments.size)
        window._show_page(arguments.page)

        def watch_window():
            if window._window is None:
                root.destroy()
            else:
                root.after(250, watch_window)

        root.after(250, watch_window)
        root.after(900000, root.destroy)
        root.mainloop()


if __name__ == "__main__":
    main()
