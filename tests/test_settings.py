"""Settings persistence and asynchronous result handling without a GUI session."""

import sys
import unittest
from unittest.mock import Mock, patch

if sys.platform == "win32":
    from src import main
    import settings


@unittest.skipUnless(sys.platform == "win32", "Windows desktop settings only")
class SettingsTests(unittest.TestCase):
    def make_window(self):
        with patch.object(main.Config, "_load_from_file"):
            config = main.Config()
        config.save = Mock()
        callback = Mock()
        window = settings.SettingsWindow(config, on_save_callback=callback)
        values = {
            "polling_interval": "2", "wallpaper_engine_path": "",
            "action_on_vr_start": "Pause", "auto_start": False,
            "auto_restart_wallpaper": True, "language": "English",
            "uu_enabled": True, "uu_trigger": "Either", "uu_auto_launch": True,
            "uu_stop_on_exit": True, "uu_cli_path": "", "uu_region": "Japan",
        }
        window._vars = {key: Mock(get=Mock(return_value=value)) for key, value in values.items()}
        window._action_choices = {"Stop": "stop", "Pause": "pause"}
        window._trigger_choices = {"Either": "either"}
        window._regions = [{"name": "Japan", "zone_id": "jp", "server_id": "all"}]
        window._feedback_var = Mock()
        window._close = Mock()
        window._show_page = Mock()
        return window, config, callback

    def test_save_keeps_settings_and_region_ids_together(self):
        window, config, callback = self.make_window()
        with (
            patch.object(settings, "is_autostart_enabled", return_value=False),
            patch.object(settings, "enable_autostart") as enable,
            patch.object(settings, "disable_autostart") as disable,
        ):
            window._on_save()
        self.assertEqual(config.polling_interval, 2)
        self.assertEqual(config.action_on_vr_start, "pause")
        self.assertEqual(config.language, "en")
        self.assertTrue(config.uu_enabled)
        self.assertEqual(config.uu_trigger, "either")
        self.assertEqual((config.uu_zone_id, config.uu_server_id), ("jp", "all"))
        self.assertEqual(config.uu_cli_path, "auto")
        config.save.assert_called_once()
        callback.assert_called_once()
        window._close.assert_called_once()
        enable.assert_not_called()
        disable.assert_not_called()

    def test_invalid_interval_does_not_partially_save(self):
        window, config, callback = self.make_window()
        window._vars["polling_interval"].get.return_value = "invalid"
        original = config.to_dict()
        window._on_save()
        self.assertEqual(config.to_dict(), original)
        config.save.assert_not_called()
        callback.assert_not_called()
        window._close.assert_not_called()

    def test_old_window_results_are_discarded(self):
        window, _, _ = self.make_window()
        window._window = Mock()
        window._generation = 2
        stale, current = Mock(), Mock()
        window._results.put((1, stale, "old", None))
        window._results.put((2, current, "new", None))
        window._drain_results()
        stale.assert_not_called()
        current.assert_called_once_with("new")

    def test_uu_switch_does_not_navigate_away(self):
        window, _, _ = self.make_window()
        window._sync_uu_options = Mock()
        window._ensure_regions = Mock()
        window._on_uu_toggle()
        window._sync_uu_options.assert_called_once()
        window._show_page.assert_not_called()

    def test_blank_choice_restores_last_valid_value(self):
        window, _, _ = self.make_window()
        window._combo_values = {"uu_trigger": ["VRChat", "SteamVR", "Either"]}
        window._combo_last_values = {"uu_trigger": "Either"}
        window._vars["uu_trigger"].get.return_value = ""
        combo = Mock()
        window._settle_combobox("uu_trigger", combo)
        window._vars["uu_trigger"].set.assert_called_once_with("Either")
        combo.selection_clear.assert_called_once()

    def test_valid_new_choice_is_remembered(self):
        window, _, _ = self.make_window()
        window._combo_values = {"uu_trigger": ["SteamVR", "Either"]}
        window._combo_last_values = {"uu_trigger": "SteamVR"}
        window._settle_combobox("uu_trigger", Mock())
        self.assertEqual(window._combo_last_values["uu_trigger"], "Either")
        window._vars["uu_trigger"].set.assert_not_called()

    def test_enabled_uu_requires_a_concrete_region(self):
        window, config, callback = self.make_window()
        window._regions = []
        window._vars["uu_region"].get.return_value = ""
        original = config.to_dict()
        window._on_save()
        config.save.assert_not_called()
        callback.assert_not_called()
        self.assertEqual(config.to_dict(), original)
        self.assertEqual(window._feedback_var.set.call_args.args[0], settings.t("uu_region_required", "zh"))

    def test_disabled_uu_can_save_without_region_and_keeps_existing_ids(self):
        window, config, _ = self.make_window()
        config.uu_zone_id, config.uu_server_id, config.uu_region_name = "saved", "server", "Saved"
        window._vars["uu_enabled"].get.return_value = False
        window._vars["uu_region"].get.return_value = ""
        window._regions = []
        collected = window._collect_settings()
        self.assertEqual((collected["uu_zone_id"], collected["uu_server_id"]), ("saved", "server"))

    def test_loaded_regions_drop_placeholders_and_choose_actual_region(self):
        window, _, _ = self.make_window()
        window._regions = [{"name": "Use UU", "zone_id": "", "server_id": ""}]
        window._vars["uu_region"].get.return_value = "Use UU"
        window._connection_var = window._connection_detail_var = Mock()
        window._connection_label = Mock()
        window._region_combo = Mock()
        window._region_status_label = Mock()
        window._connected([
            {"name": "Use UU", "zone_id": "", "server_id": ""},
            {"name": "Smart", "zone_id": "smart", "server_id": "all"},
            {"name": "Japan", "zone_id": "jp", "server_id": "all"},
        ])
        self.assertEqual([item["name"] for item in window._regions], ["Smart", "Japan"])
        window._vars["uu_region"].set.assert_called_once_with("Smart")

    def test_loaded_regions_preserve_explicit_saved_region(self):
        window, _, _ = self.make_window()
        window._connection_var = window._connection_detail_var = Mock()
        window._connection_label = Mock()
        window._region_combo = Mock()
        window._region_status_label = Mock()
        window._connected([
            {"name": "Smart", "zone_id": "smart", "server_id": "all"},
            {"name": "Japan", "zone_id": "jp", "server_id": "all"},
        ])
        window._vars["uu_region"].set.assert_called_once_with("Japan")

    def test_empty_region_refresh_keeps_previous_concrete_selection(self):
        window, _, _ = self.make_window()
        window._connection_var = window._connection_detail_var = Mock()
        window._connection_label = Mock()
        window._region_combo = window._region_status_label = Mock()
        window._connected([])
        self.assertEqual(window._regions, [{"name": "Japan", "zone_id": "jp", "server_id": "all"}])
        window._vars["uu_region"].set.assert_not_called()


@unittest.skipUnless(sys.platform == "win32", "Windows native combobox styling")
class ComboboxStyleTests(unittest.TestCase):
    def test_readonly_text_stays_visible_with_and_without_focus(self):
        import tkinter as tk
        from tkinter import ttk
        root = tk.Tk()
        root.withdraw()
        try:
            with patch.object(main.Config, "_load_from_file"):
                window = settings.SettingsWindow(main.Config())
            window._window = root
            window._setup_styles()
            style = ttk.Style(root)
            for state in (("readonly",), ("readonly", "focus")):
                with self.subTest(state=state):
                    self.assertEqual(style.lookup("App.TCombobox", "foreground", state), settings.COLORS["ink"])
        finally:
            root.destroy()

    def test_native_combobox_retains_value_after_selection_and_focus_change(self):
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        try:
            with patch.object(main.Config, "_load_from_file"):
                window = settings.SettingsWindow(main.Config())
            window._window = root
            window._setup_styles()
            window._vars = {"uu_trigger": tk.StringVar(root, value="SteamVR")}
            parent = tk.Frame(root, bg="white")
            combo = window._combo_row(parent, "uu_trigger", "Trigger", ["VRChat", "SteamVR"])
            combo.selection_range(0, "end")
            combo.state(["focus"])
            window._settle_combobox("uu_trigger", combo)
            combo.state(["!focus"])
            self.assertEqual(combo.get(), "SteamVR")
            self.assertEqual(window._vars["uu_trigger"].get(), "SteamVR")
            self.assertFalse(root.tk.getboolean(combo.cget("exportselection")))
        finally:
            root.destroy()


class FocusWidget:
    def __init__(self, path, top, height, kind="TEntry"):
        self.path, self.top, self.height, self.kind = path, top, height, kind

    def __str__(self):
        return self.path

    def winfo_rooty(self):
        return self.top

    def winfo_height(self):
        return self.height

    def winfo_class(self):
        return self.kind

    def winfo_ismapped(self):
        return True


@unittest.skipUnless(sys.platform == "win32", "Windows desktop settings only")
class KeyboardRevealTests(unittest.TestCase):
    def setUp(self):
        from unittest.mock import MagicMock
        with patch.object(main.Config, "_load_from_file"):
            self.window = settings.SettingsWindow(main.Config())
        self.window._window = Mock()
        self.canvas = MagicMock()
        self.canvas.__str__.return_value = ".settings.canvas"
        self.canvas.winfo_rooty.return_value = 100
        self.canvas.winfo_height.return_value = 400
        self.canvas.bbox.return_value = (0, 0, 600, 1000)
        self.canvas.canvasy.return_value = 200
        self.window._pages = {"automation": (Mock(), self.canvas)}

    def test_focus_events_do_not_schedule_mouse_scrolling(self):
        self.window._bind_navigation()
        sequences = [call.args[0] for call in self.window._window.bind.call_args_list]
        self.assertNotIn("<FocusIn>", sequences)
        self.assertIn("<Tab>", sequences)
        self.assertIn("<Shift-Tab>", sequences)

    def test_keyboard_reveal_is_deferred_until_after_normal_traversal(self):
        self.window._queue_keyboard_reveal(Mock())
        self.window._window.after_idle.assert_called_once()
        self.window._window.focus_get.assert_not_called()
        self.canvas.yview_moveto.assert_not_called()

    def test_pointer_press_cancels_pending_keyboard_reveal(self):
        self.window._focus_after_id = "pending-reveal"
        self.window._cancel_keyboard_reveal(Mock())
        self.window._window.after_cancel.assert_called_once_with("pending-reveal")
        self.assertIsNone(self.window._focus_after_id)
        self.canvas.yview_moveto.assert_not_called()

    def test_visible_control_does_not_move(self):
        self.window._window.focus_get.return_value = FocusWidget(".settings.canvas.entry", 150, 30)
        self.window._reveal_keyboard_focus()
        self.canvas.yview_moveto.assert_not_called()

    def test_offscreen_control_is_revealed(self):
        self.window._window.focus_get.return_value = FocusWidget(".settings.canvas.entry", 480, 40)
        self.window._reveal_keyboard_focus()
        self.canvas.yview_moveto.assert_called_once()
        self.assertAlmostEqual(self.canvas.yview_moveto.call_args.args[0], 0.232)

    def test_ancestor_frame_and_other_page_focus_are_ignored(self):
        for widget in (
            FocusWidget(".settings.canvas.content", 100, 1000, "Frame"),
            FocusWidget(".settings.other.entry", 800, 30),
            None,
        ):
            with self.subTest(widget=str(widget)):
                self.window._window.focus_get.return_value = widget
                self.window._reveal_keyboard_focus()
                self.canvas.yview_moveto.assert_not_called()


if __name__ == "__main__":
    unittest.main()
