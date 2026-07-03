"""Settings dialog window using tkinter."""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from config import Config
from autostart import enable_autostart, disable_autostart, is_autostart_enabled


class SettingsWindow:
    """Tkinter settings dialog for the application."""

    def __init__(self, config: Config, on_save_callback=None):
        """Initialize the settings window.

        Args:
            config: The application Config instance.
            on_save_callback: Optional callback invoked after successful save.
        """
        self._config = config
        self._on_save_callback = on_save_callback
        self._window: tk.Toplevel | None = None
        self._interval_var: tk.IntVar | None = None
        self._path_var: tk.StringVar | None = None
        self._autostart_var: tk.BooleanVar | None = None

    def show(self) -> None:
        """Show the settings window (non-blocking)."""
        if self._window and self._window.winfo_exists():
            self._window.lift()
            self._window.focus_force()
            return

        self._window = tk.Toplevel()
        self._window.title("SteamVR Wallpaper Pause — Settings")
        self._window.resizable(False, False)
        self._window.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # Icon — use default tkinter behavior, no custom icon needed
        self._window.geometry("420x220")

        # Style
        self._window.configure(bg="#f0f0f0")

        main_frame = ttk.Frame(self._window, padding=16)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Polling Interval ---
        ttk.Label(main_frame, text="Polling Interval (seconds):").grid(
            row=0, column=0, sticky=tk.W, pady=(0, 8)
        )
        self._interval_var = tk.IntVar(value=self._config.polling_interval)
        interval_spin = ttk.Spinbox(
            main_frame,
            from_=1,
            to=300,
            textvariable=self._interval_var,
            width=8,
        )
        interval_spin.grid(row=0, column=1, sticky=tk.W, pady=(0, 8), padx=(8, 0))

        # --- Wallpaper Engine Path ---
        ttk.Label(main_frame, text="Wallpaper Engine Path:").grid(
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

        browse_btn = ttk.Button(
            path_frame,
            text="Browse...",
            command=self._browse_path,
            width=9,
        )
        browse_btn.pack(side=tk.LEFT, padx=(4, 0))

        # Auto path hint
        ttk.Label(
            main_frame,
            text="Leave empty for auto-detection",
            foreground="#888888",
            font=("Segoe UI", 8),
        ).grid(row=2, column=1, sticky=tk.W, pady=(0, 12), padx=(8, 0))

        # --- Auto-start ---
        self._autostart_var = tk.BooleanVar(value=is_autostart_enabled())
        autostart_check = ttk.Checkbutton(
            main_frame,
            text="Start with Windows",
            variable=self._autostart_var,
        )
        autostart_check.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(4, 12))

        # --- Buttons ---
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, sticky=tk.E, pady=(8, 0))

        cancel_btn = ttk.Button(button_frame, text="Cancel", command=self._on_cancel)
        cancel_btn.pack(side=tk.RIGHT, padx=(8, 0))

        save_btn = ttk.Button(button_frame, text="Save", command=self._on_save)
        save_btn.pack(side=tk.RIGHT)

        # Center the window on screen
        self._window.update_idletasks()
        self._window.grab_set()

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
        if self._interval_var:
            try:
                interval = self._interval_var.get()
                if interval < 1:
                    raise ValueError("Interval must be at least 1 second")
            except (tk.TclError, ValueError):
                messagebox.showwarning(
                    "Invalid Value",
                    "Polling interval must be a number greater than 0.",
                    parent=self._window,  # type: ignore[arg-type]
                )
                return
            self._config.polling_interval = interval

        if self._path_var:
            path = self._path_var.get().strip()
            if path:
                self._config.wallpaper_engine_path = path
            else:
                self._config.wallpaper_engine_path = "auto"

        if self._autostart_var is not None:
            self._config.auto_start = self._autostart_var.get()
            if self._autostart_var.get():
                enable_autostart()
            else:
                disable_autostart()

        self._config.save()

        if self._on_save_callback:
            self._on_save_callback()

        self._close()

    def _on_cancel(self) -> None:
        """Close settings without saving."""
        self._close()

    def _close(self) -> None:
        """Close and destroy the settings window."""
        if self._window:
            self._window.destroy()
            self._window = None
