"""Native settings with progressive disclosure and UU connection guidance."""

import logging
from pathlib import Path
import queue
import sys
import threading
import tkinter as tk
from tkinter import filedialog, font as tkfont, ttk
import webbrowser

from config import Config
from autostart import enable_autostart, disable_autostart, is_autostart_enabled
from i18n import t, Lang, uu_error_text, uu_status_text
from uu import UUClient, UUError, UUOptions, UUState

logger = logging.getLogger("steamvr_wallpaper_pause.settings")
GITHUB_URL = "https://github.com/ssldxss/steamvr-wallpaper-pause"
COLORS = {
    "canvas": "#F3F6F6", "surface": "#FFFFFF", "ink": "#182D36",
    "muted": "#51666E", "border": "#DCE5E7", "accent": "#087F72",
    "accent_hover": "#06695E", "sidebar": "#15262D", "nav_active": "#29464E",
    "nav_text": "#BDD0D5", "success_bg": "#E2F1EC", "error": "#B42318",
}


class RegionSelectionError(ValueError):
    """Enabled UU automation needs a real region/server selection."""


class SettingsWindow:
    def __init__(self, config: Config, on_save_callback=None, *,
                 uu_state_provider=None, client_factory=UUClient):
        self._config = config
        self._on_save_callback = on_save_callback
        self._uu_state_provider = uu_state_provider
        self._client_factory = client_factory
        self._ui_lang = config.language
        self._window: tk.Toplevel | None = None
        self._vars, self._pages, self._nav_buttons, self._field_widgets = {}, {}, {}, {}
        self._results = queue.Queue()
        self._generation = 0
        self._busy = self._checked = self._connection_ready = False
        self._operation_buttons = []
        self._check_button = self._enable_button = None
        self._feedback_var = self._feedback_label = None
        self._after_id = None
        self._focus_after_id = None
        self._active_page = "automation"
        self._regions = []
        self._combo_values, self._combo_last_values = {}, {}
        self._region_combo = self._region_status_label = None

    @property
    def _lang(self) -> Lang:
        return self._ui_lang

    def show(self):
        if self._window and self._window.winfo_exists():
            self._window.lift()
            self._window.focus_force()
            return
        self._generation += 1
        self._ui_lang = self._config.language
        self._busy = self._checked = self._connection_ready = False
        self._pages, self._nav_buttons, self._field_widgets = {}, {}, {}
        self._operation_buttons = []
        self._combo_values, self._combo_last_values = {}, {}
        self._window = tk.Toplevel()
        self._window.title(t("app_name", self._lang) + " · " + t("settings", self._lang))
        self._window.geometry("940x720")
        self._window.minsize(780, 560)
        self._window.configure(bg=COLORS["canvas"])
        self._window.protocol("WM_DELETE_WINDOW", self._close)
        self._bind_navigation()
        icon = (Path(sys.executable).parent if getattr(sys, "frozen", False)
                else Path(__file__).resolve().parent.parent) / "assets" / "app.ico"
        if icon.is_file():
            try:
                self._window.iconbitmap(str(icon))
            except tk.TclError:
                pass
        self._setup_styles()
        self._init_variables()
        self._build_sidebar()
        main = tk.Frame(self._window, bg=COLORS["canvas"])
        main.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self._build_footer(main)
        self._page_container = tk.Frame(main, bg=COLORS["canvas"])
        self._page_container.pack(fill=tk.BOTH, expand=True)
        self._build_automation(self._new_page("automation"))
        self._build_connection(self._new_page("connection"))
        self._build_advanced(self._new_page("advanced"))
        self._show_page("automation")
        self._sync_uu_options()
        self._ensure_regions()
        self._tick()
        self._window.update_idletasks()
        self._window.lift()

    def _setup_styles(self):
        families = set(tkfont.families(self._window))
        self._font = "Microsoft YaHei UI" if self._lang == "zh" and "Microsoft YaHei UI" in families else "Segoe UI"
        style = ttk.Style(self._window)
        style.theme_use("clam")
        style.configure("App.TButton", font=(self._font, 10), padding=(14, 9),
                        background=COLORS["surface"], foreground=COLORS["ink"],
                        bordercolor=COLORS["border"], focuscolor=COLORS["accent"])
        style.map("App.TButton", background=[("active", COLORS["canvas"])],
                  bordercolor=[("focus", COLORS["accent"])])
        style.configure("Primary.TButton", font=(self._font, 10, "bold"), padding=(20, 10),
                        background=COLORS["accent"], foreground="white",
                        bordercolor=COLORS["accent"], focuscolor="white")
        style.map("Primary.TButton", background=[("active", COLORS["accent_hover"])])
        style.configure("Link.TButton", font=(self._font, 10), padding=(0, 6),
                        background=COLORS["surface"], foreground=COLORS["accent"],
                        borderwidth=0, focuscolor=COLORS["accent"])
        style.configure("App.TCheckbutton", font=(self._font, 10), padding=(0, 5),
                        background=COLORS["surface"], foreground=COLORS["ink"])
        style.map("App.TCheckbutton", background=[("active", COLORS["surface"])],
                  indicatorbackground=[("selected", COLORS["accent"])])
        for name in ("App.TEntry", "App.TCombobox", "App.TSpinbox"):
            style.configure(name, padding=(8, 7), fieldbackground=COLORS["surface"],
                            foreground=COLORS["ink"], bordercolor=COLORS["border"],
                            focuscolor=COLORS["accent"])
            style.map(name, bordercolor=[("focus", COLORS["accent"])])
        style.map("App.TCombobox", foreground=[("disabled", COLORS["muted"]), ("readonly", COLORS["ink"])],
                  fieldbackground=[("readonly", COLORS["surface"])],
                  selectbackground=[("readonly", COLORS["surface"])],
                  selectforeground=[("readonly", COLORS["ink"])])
        self._window.option_add("*TCombobox*Listbox.font", (self._font, 10))

    def _init_variables(self):
        self._action_choices = {
            t("mode_stop", self._lang): "stop", t("mode_pause", self._lang): "pause"
        }
        self._trigger_choices = {
            t("uu_trigger_" + key, self._lang): key for key in ("vrchat", "steamvr", "either")
        }
        self._regions = []
        if self._config.uu_zone_id and self._config.uu_server_id and self._config.uu_region_name:
            self._regions.append({
                "name": self._config.uu_region_name,
                "zone_id": self._config.uu_zone_id, "server_id": self._config.uu_server_id,
            })
        values = {
            "polling_interval": str(self._config.polling_interval),
            "wallpaper_engine_path": "" if self._config.wallpaper_engine_path == "auto" else self._config.wallpaper_engine_path,
            "action_on_vr_start": next(name for name, key in self._action_choices.items() if key == self._config.action_on_vr_start),
            "auto_start": is_autostart_enabled(),
            "auto_restart_wallpaper": self._config.auto_restart_wallpaper,
            "language": "中文" if self._lang == "zh" else "English",
            "uu_enabled": self._config.uu_enabled,
            "uu_trigger": next(name for name, key in self._trigger_choices.items() if key == self._config.uu_trigger),
            "uu_auto_launch": self._config.uu_auto_launch,
            "uu_stop_on_exit": self._config.uu_stop_on_exit,
            "uu_cli_path": "" if self._config.uu_cli_path == "auto" else self._config.uu_cli_path,
            "uu_region": self._regions[0]["name"] if self._regions else "",
        }
        self._vars = {
            key: (tk.BooleanVar if isinstance(value, bool) else tk.StringVar)(
                master=self._window, value=value
            ) for key, value in values.items()
        }

    def _label(self, parent, text, *, muted=False, size=10, bold=False, bg=None, wrap=500):
        label = tk.Label(
            parent, text=text, font=(self._font, size, "bold" if bold else "normal"),
            fg=COLORS["muted" if muted else "ink"], bg=bg or parent.cget("bg"),
            anchor="w", justify=tk.LEFT, wraplength=wrap, borderwidth=0,
        )
        def wrap_text(event):
            if event.width > 80:
                available = event.width - 2 * int(parent.cget("padx"))
                label.configure(wraplength=max(80, min(wrap, available)))
        parent.bind("<Configure>", wrap_text, add="+")
        return label

    def _build_sidebar(self):
        sidebar = tk.Frame(self._window, width=174, bg=COLORS["sidebar"])
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)
        tk.Label(sidebar, text=t("app_name", self._lang),
                 font=(self._font, 17 if self._lang == "zh" else 14, "bold"),
                 fg="white", bg=COLORS["sidebar"], anchor="w", justify=tk.LEFT,
                 wraplength=130).pack(fill=tk.X, padx=22, pady=(32, 8))
        tk.Label(sidebar, text=t("app_tagline", self._lang), font=(self._font, 9),
                 fg=COLORS["nav_text"], bg=COLORS["sidebar"], anchor="w", justify=tk.LEFT,
                 wraplength=132).pack(fill=tk.X, padx=22, pady=(0, 34))
        for key in ("automation", "connection", "advanced"):
            button = tk.Button(
                sidebar, text=t("nav_" + key, self._lang), font=(self._font, 11),
                bg=COLORS["sidebar"], fg=COLORS["nav_text"], activeforeground="white",
                activebackground=COLORS["nav_active"], relief=tk.FLAT, anchor="w",
                borderwidth=0, padx=16, pady=13, highlightthickness=1,
                highlightbackground=COLORS["sidebar"], highlightcolor="#69C6B6",
                command=lambda page=key: self._show_page(page),
            )
            button.pack(fill=tk.X, padx=10, pady=3)
            self._nav_buttons[key] = button

    def _build_footer(self, parent):
        footer = tk.Frame(parent, bg=COLORS["surface"])
        footer.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Frame(footer, bg=COLORS["border"], height=1).pack(side=tk.TOP, fill=tk.X)
        actions = tk.Frame(footer, bg=COLORS["surface"])
        actions.pack(side=tk.RIGHT, padx=(8, 24), pady=18)
        ttk.Button(actions, text=t("cancel", self._lang), command=self._close,
                   style="App.TButton").pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(actions, text=t("save_settings", self._lang), command=self._on_save,
                   style="Primary.TButton").pack(side=tk.LEFT)
        self._feedback_var = tk.StringVar(master=self._window, value=t("save_hint", self._lang))
        self._feedback_label = self._label(footer, "", muted=True, size=9, wrap=290)
        self._feedback_label.configure(textvariable=self._feedback_var)
        self._feedback_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(28, 0), pady=12)

    def _new_page(self, name):
        holder = tk.Frame(self._page_container, bg=COLORS["canvas"])
        scrollbar = ttk.Scrollbar(holder, orient=tk.VERTICAL)
        canvas = tk.Canvas(holder, bg=COLORS["canvas"], highlightthickness=0,
                           yscrollcommand=scrollbar.set)
        scrollbar.configure(command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        content = tk.Frame(canvas, bg=COLORS["canvas"], padx=28, pady=26)
        item = canvas.create_window((0, 0), window=content, anchor="nw")
        canvas.bind("<Configure>", lambda event: canvas.itemconfigure(item, width=event.width))
        content.bind("<Configure>", lambda event: canvas.configure(scrollregion=canvas.bbox("all")))
        self._pages[name] = (holder, canvas)
        self._label(content, t("nav_" + name, self._lang), size=21, bold=True).pack(anchor="w")
        intro = "automation_intro" if name == "automation" else name + "_intro"
        self._label(content, t(intro, self._lang), muted=True, wrap=570).pack(
            anchor="w", fill=tk.X, pady=(8, 22)
        )
        return content

    def _card(self, parent, heading, description=None):
        border = tk.Frame(parent, bg=COLORS["surface"], highlightthickness=1,
                          highlightbackground=COLORS["border"])
        border.pack(fill=tk.X, pady=(0, 16))
        body = tk.Frame(border, bg=COLORS["surface"], padx=18, pady=16)
        body.pack(fill=tk.X)
        self._label(body, heading, size=12, bold=True).pack(anchor="w")
        if description:
            self._label(body, description, muted=True, size=9, wrap=520).pack(
                anchor="w", fill=tk.X, pady=(6, 12)
            )
        return body

    def _combo_row(self, parent, key, label, values, width=29):
        row = tk.Frame(parent, bg=parent.cget("bg"))
        row.pack(fill=tk.X, pady=5)
        self._label(row, label).pack(side=tk.LEFT, padx=(0, 14))
        combo = ttk.Combobox(row, textvariable=self._vars[key], values=values,
                             state="readonly", width=width, font=(self._font, 10),
                             style="App.TCombobox", exportselection=False)
        self._combo_values[key] = list(values)
        if self._vars[key].get() in values:
            self._combo_last_values[key] = self._vars[key].get()
        for sequence in ("<<ComboboxSelected>>", "<FocusOut>"):
            combo.bind(sequence, lambda event, name=key: self._settle_combobox(name, event.widget), add="+")
        combo.pack(side=tk.RIGHT)
        self._field_widgets[key] = combo
        return combo

    def _settle_combobox(self, key, combo):
        try:
            choices = self._combo_values.get(key, [])
            selected = self._vars[key].get()
            if selected in choices:
                self._combo_last_values[key] = selected
            elif choices:
                selected = self._combo_last_values.get(key)
                if selected not in choices:
                    selected = choices[0]
                self._vars[key].set(selected)
                self._combo_last_values[key] = selected
            # Remove highlighting, never the selected value itself.
            combo.selection_clear()
        except tk.TclError:
            pass  # Focus can leave a widget while its window is being destroyed.

    def _check(self, parent, key, label, command=None):
        widget = ttk.Checkbutton(parent, text=label, variable=self._vars[key],
                                 style="App.TCheckbutton", command=command)
        widget.pack(anchor="w", pady=3)
        return widget

    def _build_automation(self, parent):
        wallpaper = self._card(parent, t("wallpaper_heading", self._lang), t("wallpaper_intro", self._lang))
        self._combo_row(wallpaper, "action_on_vr_start", t("wallpaper_mode", self._lang), list(self._action_choices))
        self._check(wallpaper, "auto_restart_wallpaper", t("restart_short", self._lang))
        booster = self._card(parent, t("uu_heading", self._lang), t("uu_intro", self._lang))
        self._uu_toggle_row = tk.Frame(booster, bg=COLORS["surface"])
        self._uu_toggle_row.pack(fill=tk.X)
        ttk.Checkbutton(self._uu_toggle_row, text=t("uu_enable", self._lang), variable=self._vars["uu_enabled"],
                        command=self._on_uu_toggle, style="App.TCheckbutton").pack(side=tk.LEFT)
        self._runtime_var = tk.StringVar(master=self._window, value=t("uu_status_disabled", self._lang))
        self._runtime_label = self._label(self._uu_toggle_row, "", muted=True, size=9)
        self._runtime_label.configure(textvariable=self._runtime_var)
        self._runtime_label.pack(side=tk.RIGHT)
        self._uu_options_frame = tk.Frame(booster, bg=COLORS["surface"])
        self._combo_row(self._uu_options_frame, "uu_trigger", t("uu_trigger", self._lang), list(self._trigger_choices))
        self._region_combo = self._combo_row(self._uu_options_frame, "uu_region", t("uu_region", self._lang),
                                             [item["name"] for item in self._regions])
        self._region_status_label = self._label(self._region_combo.master,
                                                t("uu_region_connect", self._lang), muted=True, size=9, wrap=330)
        self._update_region_selector()
        self._check(self._uu_options_frame, "uu_auto_launch", t("uu_auto_launch", self._lang))
        self._check(self._uu_options_frame, "uu_stop_on_exit", t("uu_stop_on_exit", self._lang))
        self._label(self._uu_options_frame, t("uu_region_hint", self._lang), muted=True, size=9,
                    wrap=520).pack(fill=tk.X, pady=(7, 0))
        self._runtime_error = self._label(self._uu_options_frame, "", size=9, wrap=520)
        self._runtime_error.configure(fg=COLORS["error"])
        ttk.Button(booster, text=t("uu_configure", self._lang), style="Link.TButton",
                   command=lambda: self._show_page("connection")).pack(anchor="w", pady=(6, 0))
        general = self._card(parent, t("general_heading", self._lang))
        self._check(general, "auto_start", t("autostart", self._lang))
        self._label(general, t("startup_hint", self._lang), muted=True, size=9, wrap=520).pack(anchor="w", pady=(0, 2))

    def _build_connection(self, parent):
        card = self._card(parent, t("connection_heading", self._lang))
        self._connection_var = tk.StringVar(master=self._window, value=t("connection_unchecked", self._lang))
        self._connection_label = self._label(card, "", bold=True)
        self._connection_label.configure(textvariable=self._connection_var)
        self._connection_label.pack(anchor="w", pady=(12, 8))
        self._connection_detail_var = tk.StringVar(master=self._window, value=t("connection_hint", self._lang))
        detail = self._label(card, "", muted=True, size=9, wrap=520)
        detail.configure(textvariable=self._connection_detail_var)
        detail.pack(anchor="w", fill=tk.X)
        buttons = tk.Frame(card, bg=COLORS["surface"])
        buttons.pack(fill=tk.X, pady=(16, 0))
        self._check_button = ttk.Button(buttons, text=t("connection_check", self._lang),
                                        command=self._check_connection, style="App.TButton")
        self._check_button.pack(side=tk.LEFT, padx=(0, 8))
        self._enable_button = ttk.Button(buttons, text=t("connection_enable", self._lang),
                                         command=self._enable_automation, style="App.TButton", state="disabled")
        self._enable_button.pack(side=tk.LEFT)
        self._operation_buttons.append(self._check_button)
        guide = self._card(parent, t("guide_heading", self._lang))
        for number in range(1, 4):
            row = tk.Frame(guide, bg=COLORS["surface"])
            row.pack(fill=tk.X, pady=(15, 3))
            tk.Label(row, text=f"0{number}", fg=COLORS["accent"], bg=COLORS["success_bg"],
                     font=(self._font, 10, "bold"), padx=9, pady=6).pack(side=tk.LEFT, anchor="n", padx=(0, 14))
            words = tk.Frame(row, bg=COLORS["surface"])
            words.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self._label(words, t(f"guide_step_{number}", self._lang), bold=True).pack(anchor="w")
            self._label(words, t(f"guide_detail_{number}", self._lang), muted=True,
                        size=9, wrap=460).pack(anchor="w", fill=tk.X, pady=(5, 0))
        actions = tk.Frame(guide, bg=COLORS["surface"])
        actions.pack(fill=tk.X, pady=(18, 0))
        open_button = ttk.Button(actions, text=t("uu_open", self._lang), command=self._open_uu, style="App.TButton")
        open_button.pack(side=tk.LEFT, padx=(0, 16))
        self._operation_buttons.append(open_button)
        ttk.Button(actions, text=t("uu_download", self._lang), style="Link.TButton",
                   command=lambda: webbrowser.open("https://uu.163.com")).pack(side=tk.LEFT)

    def _path_row(self, parent, key, label, hint):
        self._label(parent, label).pack(anchor="w", pady=(14, 7))
        row = tk.Frame(parent, bg=parent.cget("bg"))
        row.pack(fill=tk.X)
        entry = ttk.Entry(row, textvariable=self._vars[key], font=(self._font, 10), style="App.TEntry")
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        ttk.Button(row, text=t("browse", self._lang), style="App.TButton",
                   command=lambda: self._browse_path(key)).pack(side=tk.RIGHT)
        self._field_widgets[key] = entry
        self._label(parent, hint, muted=True, size=9, wrap=520).pack(anchor="w", fill=tk.X, pady=(6, 0))

    def _build_advanced(self, parent):
        card = self._card(parent, t("advanced_detection", self._lang))
        row = tk.Frame(card, bg=COLORS["surface"])
        row.pack(fill=tk.X, pady=(14, 0))
        self._label(row, t("polling_interval", self._lang)).pack(side=tk.LEFT)
        spinbox = ttk.Spinbox(row, from_=1, to=300, textvariable=self._vars["polling_interval"],
                              width=7, font=(self._font, 10), style="App.TSpinbox")
        spinbox.pack(side=tk.RIGHT)
        self._field_widgets["polling_interval"] = spinbox
        self._label(card, t("advanced_poll_hint", self._lang), muted=True, size=9).pack(anchor="w", pady=(6, 4))
        self._path_row(card, "wallpaper_engine_path", t("wallpaper_path", self._lang), t("path_hint", self._lang))
        self._path_row(card, "uu_cli_path", t("uu_cli_path", self._lang), t("uu_cli_hint", self._lang))
        language = self._card(parent, t("language_heading", self._lang))
        self._combo_row(language, "language", t("language_label", self._lang), ["中文", "English"], width=15)
        self._label(language, t("language_hint", self._lang), muted=True, size=9).pack(anchor="w", pady=(6, 0))
        row = tk.Frame(parent, bg=COLORS["canvas"])
        row.pack(fill=tk.X)
        self._label(row, t("version", self._lang), muted=True, size=9).pack(side=tk.LEFT)
        ttk.Button(row, text=t("about", self._lang), style="App.TButton",
                   command=lambda: webbrowser.open(GITHUB_URL)).pack(side=tk.RIGHT)

    def _show_page(self, name):
        self._active_page = name
        for key, (holder, _) in self._pages.items():
            holder.pack_forget()
            self._nav_buttons[key].configure(bg=COLORS["nav_active"] if key == name else COLORS["sidebar"],
                                              fg="white" if key == name else COLORS["nav_text"])
        self._pages[name][0].pack(fill=tk.BOTH, expand=True)
        if name == "connection" and not self._checked and not self._busy:
            self._check_connection()

    def _scroll(self, amount, units="units"):
        page = self._pages.get(self._active_page)
        if page:
            page[1].yview_scroll(amount, units)

    def _mousewheel(self, event):
        if event.widget.winfo_class() not in ("TCombobox", "TSpinbox"):
            self._scroll(-int(event.delta / 120))

    def _bind_navigation(self):
        self._window.bind("<Escape>", lambda event: self._close())
        self._window.bind("<MouseWheel>", self._mousewheel)
        self._window.bind("<Next>", lambda event: self._scroll(1, "pages"))
        self._window.bind("<Prior>", lambda event: self._scroll(-1, "pages"))
        self._window.bind("<ButtonPress>", self._cancel_keyboard_reveal, add="+")
        for sequence in ("<Tab>", "<Shift-Tab>", "<ISO_Left_Tab>"):
            self._window.bind(sequence, self._queue_keyboard_reveal, add="+")

    def _queue_keyboard_reveal(self, event):
        self._cancel_keyboard_reveal()
        if self._window is not None:
            # Default Tab traversal runs after the toplevel binding. Reveal the
            # destination afterward, never during a mouse press/FocusIn event.
            self._focus_after_id = self._window.after_idle(self._reveal_keyboard_focus)

    def _cancel_keyboard_reveal(self, event=None):
        if self._focus_after_id is not None and self._window is not None:
            try:
                self._window.after_cancel(self._focus_after_id)
            except tk.TclError:
                pass
        self._focus_after_id = None

    def _reveal_keyboard_focus(self):
        self._focus_after_id = None
        if self._window is None:
            return
        page = self._pages.get(self._active_page)
        if not page:
            return
        widget = self._window.focus_get()
        if widget is None or not widget.winfo_ismapped():
            return
        if widget.winfo_class() not in (
            "TButton", "TCheckbutton", "TRadiobutton", "TCombobox", "TEntry", "TSpinbox", "Button"
        ):
            return
        canvas = page[1]
        if not str(widget).startswith(str(canvas) + "."):
            return
        top = widget.winfo_rooty() - canvas.winfo_rooty()
        bottom = top + widget.winfo_height()
        delta = top - 12 if top < 0 else bottom - canvas.winfo_height() + 12 if bottom > canvas.winfo_height() else 0
        bounds = canvas.bbox("all")
        if delta and bounds and bounds[3] > 0:
            canvas.yview_moveto((canvas.canvasy(0) + delta) / bounds[3])

    def _sync_uu_options(self):
        if self._vars["uu_enabled"].get():
            self._uu_options_frame.pack(fill=tk.X, after=self._uu_toggle_row, pady=(8, 0))
        else:
            self._uu_options_frame.pack_forget()

    def _on_uu_toggle(self):
        self._sync_uu_options()
        self._ensure_regions()

    def _ensure_regions(self):
        if self._vars["uu_enabled"].get() and not self._checked and not self._busy:
            self._check_connection()

    def _update_region_selector(self):
        if self._region_combo is None:
            return
        names = [item["name"] for item in self._regions]
        self._combo_values["uu_region"] = names
        self._region_combo.configure(values=names)
        if names:
            self._region_status_label.pack_forget()
            self._region_combo.configure(state="readonly")
            self._region_combo.pack(side=tk.RIGHT)
        else:
            self._region_combo.pack_forget()
            self._region_status_label.configure(text=t(
                "uu_region_loading" if self._busy else "uu_region_connect", self._lang
            ))
            self._region_status_label.pack(side=tk.RIGHT)

    def _enable_automation(self):
        self._vars["uu_enabled"].set(True)
        self._sync_uu_options()
        self._show_page("automation")

    def _background(self, task, success):
        if self._busy:
            return
        self._busy = True
        generation = self._generation
        self._sync_operation_buttons()

        def run():
            try:
                result, error = task(), None
            except UUError as failure:
                result, error = None, failure
            except Exception as failure:
                logger.exception("UU settings operation failed")
                result, error = None, UUError("API_ERROR", str(failure))
            self._results.put((generation, success, result, error))

        threading.Thread(target=run, name="uu-settings", daemon=True).start()

    def _sync_operation_buttons(self):
        for button in self._operation_buttons:
            button.configure(state="disabled" if self._busy else "normal")
        if self._check_button is not None:
            self._check_button.configure(text=t(
                "connection_checking" if self._busy else
                "connection_recheck" if self._checked else "connection_check", self._lang))
        if self._enable_button is not None:
            self._enable_button.configure(state="normal" if self._connection_ready and self._regions and not self._busy else "disabled")
        self._update_region_selector()

    def _check_connection(self):
        if self._busy:
            return
        self._checked = True
        self._connection_var.set(t("connection_checking", self._lang))
        client = self._client_factory(self._vars["uu_cli_path"].get().strip() or "auto")
        game_id = self._config.uu_game_id

        def check():
            doctor = client.doctor()
            if doctor.get("status") != "ready":
                raise UUError({"not_installed": "UU_NOT_INSTALLED", "not_running": "UU_NOT_RUNNING"}.get(
                    doctor.get("status"), "SERVICE_UNAVAILABLE"))
            client.status()
            return client.regions(game_id)

        self._background(check, self._connected)

    def _connected(self, regions):
        available = [item for item in regions if item.get("name") and item.get("zone_id") and item.get("server_id")]
        if not available:
            self._connection_ready = False
            self._connection_var.set(t("uu_status_error", self._lang))
            self._connection_label.configure(fg=COLORS["error"])
            self._connection_detail_var.set(t("uu_region_unavailable", self._lang))
            self._sync_operation_buttons()
            return
        self._connection_ready = True
        self._connection_var.set(t("connection_ready", self._lang))
        self._connection_label.configure(fg=COLORS["accent"])
        self._connection_detail_var.set(t("connection_hint", self._lang))
        selected = next((item for item in self._regions if item["name"] == self._vars["uu_region"].get()), None)
        preferred = ((selected["zone_id"], selected["server_id"]) if selected else
                     (self._config.uu_zone_id, self._config.uu_server_id))
        self._regions = available
        match = next((item for item in self._regions if
                      (item["zone_id"], item["server_id"]) == preferred), None)
        if match is None:
            match = self._regions[0]
        self._vars["uu_region"].set(match["name"])
        self._combo_last_values["uu_region"] = match["name"]
        self._sync_operation_buttons()

    def _open_uu(self):
        client = self._client_factory(self._vars["uu_cli_path"].get().strip() or "auto")
        self._background(client.open_app, lambda result: self._connection_detail_var.set(t("uu_opened", self._lang)))

    def _drain_results(self):
        while True:
            try:
                generation, success, result, error = self._results.get_nowait()
            except queue.Empty:
                break
            if generation != self._generation or self._window is None:
                continue
            self._busy = False
            if error:
                self._connection_ready = False
                self._connection_var.set(t("uu_status_error", self._lang))
                self._connection_label.configure(fg=COLORS["error"])
                self._connection_detail_var.set(uu_error_text(error.code, self._lang))
            else:
                success(result)
            self._sync_operation_buttons()

    def _tick(self):
        if self._window is None:
            return
        self._drain_results()
        state = UUState()
        enabled = self._vars["uu_enabled"].get()
        if enabled != self._config.uu_enabled:
            state = UUState("pending_enable" if enabled else "pending_disable")
        elif enabled:
            state = self._uu_state_provider() if self._uu_state_provider and self._config.uu_enabled else UUState("waiting")
        self._runtime_var.set(uu_status_text(state, self._lang))
        self._runtime_label.configure(fg=COLORS["error"] if state.key == "error" else COLORS["muted"])
        if state.key == "error":
            self._runtime_error.configure(text=uu_error_text(state.detail, self._lang))
            self._runtime_error.pack(fill=tk.X, pady=(8, 0))
        else:
            self._runtime_error.pack_forget()
        self._after_id = self._window.after(150, self._tick)

    def _browse_path(self, key):
        filename = filedialog.askopenfilename(parent=self._window, title=t("browse", self._lang),
                                             filetypes=[("Executable", "*.exe"), ("All files", "*.*")])
        if filename:
            self._vars[key].set(filename)

    def _collect_settings(self):
        values = {key: variable.get() for key, variable in self._vars.items()}
        interval = int(values["polling_interval"])
        if interval < 1:
            raise ValueError("Invalid polling interval")
        region = next((item for item in self._regions if item["name"] == values["uu_region"]
                       and item["zone_id"] and item["server_id"]), None)
        if region is None:
            if values["uu_enabled"]:
                raise RegionSelectionError("Select an actual UU region")
            region = {"name": self._config.uu_region_name, "zone_id": self._config.uu_zone_id,
                      "server_id": self._config.uu_server_id}
        collected = {
            "polling_interval": interval,
            "wallpaper_engine_path": values["wallpaper_engine_path"].strip() or "auto",
            "action_on_vr_start": self._action_choices[values["action_on_vr_start"]],
            "auto_start": bool(values["auto_start"]),
            "auto_restart_wallpaper": bool(values["auto_restart_wallpaper"]),
            "language": "zh" if values["language"] == "中文" else "en",
            "uu_enabled": bool(values["uu_enabled"]),
            "uu_trigger": self._trigger_choices[values["uu_trigger"]],
            "uu_auto_launch": bool(values["uu_auto_launch"]),
            "uu_stop_on_exit": bool(values["uu_stop_on_exit"]),
            "uu_cli_path": values["uu_cli_path"].strip() or "auto",
            "uu_zone_id": region["zone_id"], "uu_server_id": region["server_id"],
            "uu_region_name": region["name"] if region["zone_id"] else "",
        }
        UUOptions(game_id=self._config.uu_game_id, **{
            key[3:]: value for key, value in collected.items()
            if key.startswith("uu_") and key != "uu_region_name"
        })
        return collected

    def _set_feedback(self, message, *, error=False):
        if self._feedback_var is not None:
            self._feedback_var.set(message)
        if self._feedback_label is not None:
            self._feedback_label.configure(fg=COLORS["error" if error else "muted"])

    def _on_save(self):
        try:
            collected = self._collect_settings()
        except RegionSelectionError:
            self._show_page("automation")
            self._set_feedback(t("uu_region_required", self._lang), error=True)
            return
        except (ValueError, tk.TclError, KeyError, StopIteration):
            self._show_page("advanced")
            self._set_feedback(t("invalid_interval", self._lang), error=True)
            widget = self._field_widgets.get("polling_interval")
            if widget is not None:
                widget.focus_set()
            return
        enabled = collected["auto_start"]
        if enabled != is_autostart_enabled():
            if not (enable_autostart() if enabled else disable_autostart()):
                self._set_feedback(t("startup_error", self._lang), error=True)
                return
        for key, value in collected.items():
            setattr(self._config, key, value)
        self._config.save()
        if self._on_save_callback:
            self._on_save_callback()
        self._close()

    def _close(self):
        self._cancel_keyboard_reveal()
        self._generation += 1
        if self._window:
            if self._after_id is not None:
                self._window.after_cancel(self._after_id)
                self._after_id = None
            self._window.destroy()
            self._window = None
