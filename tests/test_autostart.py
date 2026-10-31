"""Validate registered startup commands with the Windows command-line parser."""

import ctypes
import sys
import unittest
from unittest.mock import patch

if sys.platform == "win32":
    from src import autostart


def parse_windows_command(command: str) -> list[str]:
    shell32 = ctypes.WinDLL("shell32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    shell32.CommandLineToArgvW.argtypes = [
        ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_int)
    ]
    shell32.CommandLineToArgvW.restype = ctypes.POINTER(ctypes.c_wchar_p)
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p

    count = ctypes.c_int()
    arguments = shell32.CommandLineToArgvW(command, ctypes.byref(count))
    if not arguments:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        return [arguments[index] for index in range(count.value)]
    finally:
        kernel32.LocalFree(ctypes.cast(arguments, ctypes.c_void_p))


@unittest.skipUnless(sys.platform == "win32", "Windows auto-start only")
class AutostartCommandTests(unittest.TestCase):
    def registered_arguments(
        self, executable: str, module_file: str, *, frozen: bool
    ) -> list[str]:
        with (
            patch.object(autostart.sys, "executable", executable),
            patch.object(autostart.sys, "frozen", frozen, create=True),
            patch.object(autostart, "__file__", module_file),
            patch.object(autostart.winreg, "OpenKey"),
            patch.object(autostart.winreg, "SetValueEx") as write,
            patch.object(autostart.winreg, "CloseKey"),
        ):
            self.assertTrue(autostart.enable_autostart())

        write.assert_called_once()
        self.assertEqual(write.call_args.args[1], "SteamVR Wallpaper Pause")
        return parse_windows_command(write.call_args.args[-1])

    def test_source_paths_without_spaces(self):
        self.assertEqual(
            self.registered_arguments(
                r"C:\Python\python.exe",
                r"D:\projects\vr\src\autostart.py",
                frozen=False,
            ),
            [r"C:\Python\python.exe", r"D:\projects\vr\src\main.py", "--minimized"],
        )

    def test_source_paths_with_spaces_and_unicode(self):
        self.assertEqual(
            self.registered_arguments(
                r"C:\Program Files\Python\python.exe",
                r"D:\项目\VR Tools\src\autostart.py",
                frozen=False,
            ),
            [
                r"C:\Program Files\Python\python.exe",
                r"D:\项目\VR Tools\src\main.py",
                "--minimized",
            ],
        )

    def test_packaged_paths_without_spaces(self):
        executable = r"C:\Apps\SteamVRWallpaperPause.exe"
        self.assertEqual(
            self.registered_arguments(executable, r"C:\bundle\autostart.py", frozen=True),
            [executable, "--minimized"],
        )

    def test_packaged_paths_with_spaces_and_unicode(self):
        executable = r"C:\用户\VR Tools\SteamVRWallpaperPause.exe"
        self.assertEqual(
            self.registered_arguments(executable, r"C:\bundle\autostart.py", frozen=True),
            [executable, "--minimized"],
        )


if __name__ == "__main__":
    unittest.main()
