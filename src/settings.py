"""Settings dialog window using tkinter."""

import tkinter as tk
import webbrowser
from tkinter import filedialog, messagebox, ttk

from config import Config
from autostart import enable_autostart, disable_autostart, is_autostart_enabled
from i18n import t, Lang

GITHUB_URL = "https://github.com/ssldxss/steamvr-wallpaper-pause"


class SettingsWindow:
    """Tkinter settings dialog for the application."""

    def __init__(self, config: Config, on_save_callback=None):
        self._config = config
        self._on_save_callback = on_save_callback
        self._window: tk.Toplevel | None = None
        self._interval_var: tk.IntVar | None = None
        self._path_var: tk.StringVar | None = None
        self._autostart_var: tk.BooleanVar | None = None
        self._action_var: tk.StringVar | None = None
        self._language_var: tk.StringVar | None = None

    @property
    def _lang(self) -> Lang:
        return self._config.language  # type: ignore[return-value]

    def show(self) -> None:
        """Show the settings window (non-blocking)."""
        if self._window and self._window.winfo_exists():
            self._window.lift()
            self._window.focus_force()
            return

        lang = self._lang

        self._window = tk.Toplevel()
        self._window.title(t("settings_title", lang))
        self._window.resizable(False, False)
        self._window.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self._window.geometry("560x410")
        self._window.configure(bg="#f0f0f0")

        main_frame = ttk.Frame(self._window, padding=16)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Polling Interval ---
        ttk.Label(main_frame, text=t("polling_interval", lang)).grid(
            row=0, column=0, sticky=tk.W, pady=(0, 8)
        )
        self._interval_var = tk.IntVar(value=self._config.polling_interval)
        interval_spin = ttk.Spinbox(
            main_frame, from_=1, to=300, textvariable=self._interval_var, width=8
        )
        interval_spin.grid(row=0, column=1, sticky=tk.W, pady=(0, 8), padx=(8, 0))

        # --- Wallpaper Engine Path ---
        ttk.Label(main_frame, text=t("wallpaper_path", lang)).grid(
            row=1, column=0, sticky=tk.W, pady=(0, 8)
        )
        path_frame = ttk.Frame(main_frame)
        path_frame.grid(row=1, column=1, sticky=tk.EW, pady=(0, 8), padx=(8, 0))

        current_path = self._config.wallpaper_engine_path
        if current_path == "auto":
            current_path = ""
        self._path_var = tk.StringVar(value=current_path)
        path_entry = ttk.Entry(path_frame, textvariable=self._path_var, width=30)
        path_entry.pack(side=tk.LEFT)

        browse_btn = ttk.Button(path_frame, text=t("browse", lang), command=self._browse_path, width=9)
        browse_btn.pack(side=tk.LEFT, padx=(4, 0))

        ttk.Label(
            main_frame,
            text=t("path_hint", lang),
            foreground="#888888",
            font=("Segoe UI", 8),
        ).grid(row=2, column=1, sticky=tk.W, pady=(0, 12), padx=(8, 0))

        # --- Action on VR start ---
        ttk.Label(main_frame, text=t("action_label", lang)).grid(
            row=3, column=0, sticky=tk.W, pady=(0, 8)
        )
        action_display = t("action_pause", lang) if self._config.action_on_vr_start == "pause" else t("action_stop", lang)
        self._action_var = tk.StringVar(value=action_display)
        action_combo = ttk.Combobox(
            main_frame,
            textvariable=self._action_var,
            values=[t("action_pause", lang), t("action_stop", lang)],
            state="readonly",
            width=10,
        )
        action_combo.grid(row=3, column=1, sticky=tk.W, pady=(0, 8), padx=(8, 0))

        # --- Language ---
        ttk.Label(main_frame, text=t("language_label", lang)).grid(
            row=4, column=0, sticky=tk.W, pady=(0, 8)
        )
        lang_display = t("language_zh", lang) if self._config.language == "zh" else t("language_en", lang)
        self._language_var = tk.StringVar(value=lang_display)
        language_combo = ttk.Combobox(
            main_frame,
            textvariable=self._language_var,
            values=[t("language_zh", lang), t("language_en", lang)],
            state="readonly",
            width=12,
        )
        language_combo.grid(row=4, column=1, sticky=tk.W, pady=(0, 4), padx=(8, 0))

        ttk.Label(
            main_frame,
            text=t("language_hint", lang),
            foreground="#888888",
            font=("Segoe UI", 8),
        ).grid(row=5, column=1, sticky=tk.W, pady=(0, 12), padx=(8, 0))

        # --- Auto-start ---
        self._autostart_var = tk.BooleanVar(value=is_autostart_enabled())
        autostart_check = ttk.Checkbutton(
            main_frame,
            text=t("autostart", lang),
            variable=self._autostart_var,
        )
        autostart_check.grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=(4, 12))

        # --- Version ---
        ttk.Label(
            main_frame,
            text=t("version", lang),
            foreground="#888888",
            font=("Segoe UI", 8),
        ).grid(row=7, column=0, columnspan=2, sticky=tk.W, pady=(0, 4))

        # --- GitHub link ---
        link_label = tk.Label(
            main_frame,
            text=t("about", lang),
            foreground="#0066cc",
            cursor="hand2",
            font=("Segoe UI", 9, "underline"),
            bg="#f0f0f0",
        )
        link_label.grid(row=8, column=0, columnspan=2, sticky=tk.W, pady=(0, 12))
        link_label.bind("<Button-1>", self._open_github)

        # --- Buttons ---
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=9, column=0, columnspan=2, sticky=tk.E, pady=(8, 0))

        cancel_btn = ttk.Button(button_frame, text=t("cancel", lang), command=self._on_cancel)
        cancel_btn.pack(side=tk.RIGHT, padx=(8, 0))
        save_btn = ttk.Button(button_frame, text=t("save", lang), command=self._on_save)
        save_btn.pack(side=tk.RIGHT)

        self._window.update_idletasks()
        self._window.grab_set()

    def _open_github(self, event: tk.Event) -> None:
        """Open the GitHub repository in the default browser."""
        webbrowser.open(GITHUB_URL)

    def _browse_path(self) -> None:
        """Open file browser to select wallpaper32.exe."""
        filename = filedialog.askopenfilename(
            title="Select wallpaper32.exe",
            filetypes=[
                ("Wallpaper Engine", "wallpaper32.exe"),
                ("Executable files", "*.exe"),
                ("All files", "*.*"),
            ],
        )
        if filename and self._path_var:
            self._path_var.set(filename)

    def _on_save(self) -> None:
        """Save settings and close."""
        lang = self._lang

        if self._interval_var:
            try:
                interval = self._interval_var.get()
                if interval < 1:
                    raise ValueError("Interval must be at least 1 second")
            except (tk.TclError, ValueError):
                messagebox.showwarning(
                    t("invalid_title", lang),
                    t("invalid_interval", lang),
                    parent=self._window,  # type: ignore[arg-type]
                )
                return
            self._config.polling_interval = interval

        if self._path_var:
            path = self._path_var.get().strip()
            self._config.wallpaper_engine_path = path if path else "auto"

        if self._autostart_var is not None:
            self._config.auto_start = self._autostart_var.get()
            if self._autostart_var.get():
                enable_autostart()
            else:
                disable_autostart()

        if self._action_var is not None:
            action_display = self._action_var.get()
            # Map display value back to config value
            if action_display == t("action_pause", lang):
                self._config.action_on_vr_start = "pause"
            else:
                self._config.action_on_vr_start = "stop"

        if self._language_var is not None:
            lang_display = self._language_var.get()
            if lang_display == t("language_zh", lang):
                self._config.language = "zh"
            else:
                self._config.language = "en"

        self._config.save()

        if self._on_save_callback:
            self._on_save_callback()

        self._close()

    def _on_cancel(self) -> None:
        self._close()

    def _close(self) -> None:
        if self._window:
            self._window.destroy()
            self._window = None
