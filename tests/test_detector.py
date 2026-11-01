import unittest
from unittest.mock import Mock, patch

from src import detector


class VRChatDetectionTests(unittest.TestCase):
    def test_vrchat_detection_is_case_insensitive(self):
        with patch.object(detector.psutil, "process_iter", return_value=[
            Mock(info={"name": "explorer.exe"}), Mock(info={"name": "VRChat.exe"})
        ]):
            self.assertTrue(detector.is_vrchat_running())

    def test_steamvr_alone_does_not_count_as_vrchat(self):
        with patch.object(detector.psutil, "process_iter", return_value=[
            Mock(info={"name": "vrserver.exe"})
        ]):
            self.assertFalse(detector.is_vrchat_running())


if __name__ == "__main__":
    unittest.main()
