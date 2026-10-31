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
            self.assertEqual(path.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
