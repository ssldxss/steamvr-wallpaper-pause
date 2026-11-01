"""Existing configurations remain usable without installer rewrites."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from src import config


class ExistingConfigTests(unittest.TestCase):
    def test_legacy_config_keeps_user_values_and_supplies_missing_defaults(self):
        values = {
            "polling_interval": 9,
            "wallpaper_engine_path": r"D:\My Apps\wallpaper_engine\wallpaper64.exe",
            "auto_start": False,
            "verbose": True,
            "action_on_vr_start": "pause",
            "language": "en",
        }
        original = (json.dumps(values, indent=4) + "\n").encode("utf-8")
        with TemporaryDirectory() as temporary_dir:
            path = Path(temporary_dir) / "config.json"
            path.write_bytes(original)
            with patch.object(config, "_get_config_path", return_value=path):
                loaded = config.Config()

            for key, value in values.items():
                with self.subTest(key=key):
                    self.assertEqual(loaded.to_dict()[key], value)
            self.assertFalse(loaded.auto_restart_wallpaper)
            self.assertFalse(loaded.uu_enabled)
            self.assertEqual(path.read_bytes(), original)

    def test_uu_settings_round_trip(self):
        values = {
            "uu_enabled": True, "uu_trigger": "either", "uu_auto_launch": False,
            "uu_stop_on_exit": True, "uu_cli_path": r"D:\UU Tools\uu-cli.exe",
            "uu_zone_id": "jp", "uu_server_id": "all", "uu_region_name": "日本",
        }
        with TemporaryDirectory() as temporary_dir:
            path = Path(temporary_dir) / "config.json"
            with patch.object(config, "_get_config_path", return_value=path):
                current = config.Config()
                for key, value in values.items():
                    setattr(current, key, value)
                current.save()
                loaded = config.Config()
                for key, value in values.items():
                    with self.subTest(key=key):
                        self.assertEqual(getattr(loaded, key), value)


if __name__ == "__main__":
    unittest.main()
