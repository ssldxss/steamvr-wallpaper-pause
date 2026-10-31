"""Exercise control ownership across simulated SteamVR sessions."""

import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

if sys.platform == "win32":
    from src import main
    import controller


@unittest.skipUnless(sys.platform == "win32", "Windows wallpaper control only")
class MonitorOwnershipTests(unittest.TestCase):
    def run_session(
        self,
        action: str,
        *,
        wallpaper_running: bool,
        auto_restart: bool = False,
        starts_during_vr: bool = False,
        command_returncode: int = 0,
    ):
        with patch.object(main.Config, "_load_from_file"):
            config = main.Config({
                "action_on_vr_start": action,
                "auto_restart_wallpaper": auto_restart,
            })
        monitor = main.Monitor(config)
        monitor._wallpaper_path = "mock-wallpaper.exe"
        monitor._running = True
        tray = Mock()
        monitor._tray_app = tray
        process_running = Mock(return_value=wallpaper_running)
        polls = []

        def after_poll(_):
            polls.append((monitor._paused_by_us, tray.wallpaper_status))
            if len(polls) == 1 and starts_during_vr:
                process_running.return_value = True
            if len(polls) == 3:
                monitor._running = False

        with (
            patch.object(main, "is_steamvr_running", side_effect=[True, True, False]),
            patch.object(main, "is_wallpaper_running", process_running),
            patch.object(controller, "is_wallpaper_running", process_running),
            patch.object(controller.os.path, "isfile", return_value=True),
            patch.object(controller.subprocess, "run", return_value=SimpleNamespace(
                returncode=command_returncode, stderr="simulated command failure"
            )) as command,
            patch.object(main, "start_wallpaper_process", return_value=True) as start,
            patch.object(main.time, "sleep", side_effect=after_poll),
        ):
            monitor._monitor_loop()

        return SimpleNamespace(polls=polls, command=command, start=start, tray=tray)

    def test_skipped_control_does_not_claim_ownership_or_resume(self):
        for action in ("stop", "pause"):
            with self.subTest(action=action):
                result = self.run_session(action, wallpaper_running=False)
                self.assertEqual(result.polls, [(False, "not_running")] * 3)
                result.command.assert_not_called()
                result.start.assert_not_called()
                result.tray.notify_stop.assert_not_called()
                result.tray.notify_pause.assert_not_called()
                result.tray.notify_resume.assert_not_called()
                result.tray.notify_error.assert_not_called()

    def test_successful_control_resumes_once(self):
        for action, status in (("stop", "stopped"), ("pause", "paused")):
            with self.subTest(action=action):
                result = self.run_session(action, wallpaper_running=True)
                self.assertEqual(
                    result.polls, [(True, status), (True, status), (False, "running")]
                )
                self.assertEqual(
                    [call.args[0] for call in result.command.call_args_list],
                    [
                        ["mock-wallpaper.exe", "-control", action],
                        ["mock-wallpaper.exe", "-control", "play"],
                    ],
                )
                getattr(result.tray, f"notify_{action}").assert_called_once_with()
                result.tray.notify_resume.assert_called_once_with()
                result.tray.notify_error.assert_not_called()
                result.start.assert_not_called()

    def test_explicit_auto_restart_still_starts_without_spurious_play(self):
        for action in ("stop", "pause"):
            with self.subTest(action=action):
                result = self.run_session(
                    action, wallpaper_running=False, auto_restart=True
                )
                self.assertEqual(result.polls, [(False, "not_running")] * 3)
                result.command.assert_not_called()
                result.start.assert_called_once_with("mock-wallpaper.exe")
                result.tray.notify_error.assert_not_called()
                result.tray.notify_resume.assert_not_called()

    def test_wallpaper_started_after_skipped_control_is_not_reported_paused(self):
        for action in ("stop", "pause"):
            with self.subTest(action=action):
                result = self.run_session(
                    action, wallpaper_running=False, starts_during_vr=True
                )
                self.assertEqual(result.polls, [
                    (False, "not_running"), (False, "running"), (False, "running")
                ])
                result.command.assert_not_called()
                result.start.assert_not_called()
                result.tray.notify_error.assert_not_called()

    def test_failed_control_reports_error_without_claiming_ownership(self):
        for action in ("stop", "pause"):
            with self.subTest(action=action):
                with self.assertLogs(controller.logger, level="WARNING"):
                    result = self.run_session(
                        action, wallpaper_running=True, command_returncode=1
                    )
                self.assertEqual(result.polls, [(False, "running")] * 3)
                result.command.assert_called_once()
                result.tray.notify_error.assert_called_once()
                result.tray.notify_stop.assert_not_called()
                result.tray.notify_pause.assert_not_called()
                result.tray.notify_resume.assert_not_called()
                result.start.assert_not_called()


if __name__ == "__main__":
    unittest.main()
