"""UU protocol and ownership tests; no installed client is modified."""

import json
from pathlib import Path
import subprocess
import threading
import time
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from src import uu


GAME = "vrchat-id"


class UUClientTests(unittest.TestCase):
    def run_cli(self, payload, *, returncode=0):
        process = Mock(returncode=returncode, stdout=json.dumps(payload), stderr="")
        return patch.object(uu.subprocess, "run", return_value=process)

    def test_structured_error_is_checked_even_when_exit_code_is_zero(self):
        client = uu.UUClient("fake-cli.exe")
        with patch.object(uu, "find_cli", return_value=Path("fake-cli.exe")):
            with self.run_cli({"success": False, "error": {"code": "UU_BUSY"}}):
                with self.assertRaises(uu.UUError) as error:
                    client.doctor()
        self.assertEqual(error.exception.code, "UU_BUSY")

    def test_timeout_becomes_a_recoverable_error(self):
        with (
            patch.object(uu, "find_cli", return_value=Path("fake-cli.exe")),
            patch.object(uu.subprocess, "run", side_effect=subprocess.TimeoutExpired("uu", 10)),
        ):
            with self.assertRaises(uu.UUError) as error:
                uu.UUClient().doctor()
        self.assertEqual(error.exception.code, "TIMEOUT")

    def test_malformed_response_is_rejected(self):
        for payload in ("not json", "[]", '{"success": true, "data": []}'):
            with (
                self.subTest(payload=payload),
                patch.object(uu, "find_cli", return_value=Path("fake-cli.exe")),
                patch.object(uu.subprocess, "run", return_value=Mock(
                    returncode=0, stdout=payload, stderr=""
                )),
            ):
                with self.assertRaises(uu.UUError):
                    uu.UUClient().doctor()

    def test_regions_accept_actual_and_documented_field_names(self):
        zones = [
            {"zone_id": "jp", "zone_name": "日本", "servers": [
                {"server_id": "all", "server_name": "所有服务器"}
            ]},
            {"id": "us", "name": "US", "servers": [
                {"id": "west", "name": "West"}, {"id": "east", "name": "East"}
            ]},
        ]
        with patch.object(uu, "find_cli", return_value=Path("fake-cli.exe")):
            with self.run_cli({"success": True, "data": {"games": [{"zones": zones}]}}):
                regions = uu.UUClient().regions(GAME)
        self.assertEqual(regions, [
            {"name": "日本", "zone_id": "jp", "server_id": "all"},
            {"name": "US / West", "zone_id": "us", "server_id": "west"},
            {"name": "US / East", "zone_id": "us", "server_id": "east"},
        ])

    def test_start_uses_separate_arguments_and_stop_is_always_scoped(self):
        with patch.object(uu, "find_cli", return_value=Path("fake-cli.exe")):
            with self.run_cli({"success": True, "data": {}}) as run:
                client = uu.UUClient()
                client.start_boost(uu.UUOptions(game_id=GAME, zone_id="jp", server_id="all"))
                client.stop_boost(GAME)
        self.assertEqual(run.call_args_list[0].args[0], [
            "fake-cli.exe", "--json", "start", "--id", GAME,
            "--zone", "jp", "--server", "all"
        ])
        self.assertEqual(run.call_args_list[1].args[0][-3:], ["stop", "--id", GAME])
        self.assertEqual(run.call_args.kwargs["timeout"], 10)

    def test_zone_and_server_must_be_paired(self):
        with self.assertRaises(ValueError):
            uu.UUOptions(zone_id="jp")

    def test_client_launch_uses_native_launcher_without_cli_capture(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary) / "UU Tools"
            root.mkdir()
            launcher = root / "uu_launcher.exe"
            launcher.touch()
            with (
                patch.object(uu, "_install_roots", return_value=[root]),
                patch.object(uu.os, "startfile", create=True) as launch,
                patch.object(uu.subprocess, "run") as run,
            ):
                uu.UUClient().start_app()
                launch.assert_called_once_with(str(launcher))
                run.assert_not_called()

    def test_native_launch_failure_is_reported(self):
        with (
            patch.object(uu, "_install_roots", return_value=[Path("UU")]),
            patch.object(Path, "is_file", return_value=True),
            patch.object(uu.os, "startfile", create=True, side_effect=OSError("cancelled")),
        ):
            with self.assertRaises(uu.UUError) as error:
                uu.UUClient().start_app()
        self.assertEqual(error.exception.code, "UU_NOT_RUNNING")

    def test_explicit_cli_is_resolved_without_extracting_anything(self):
        with TemporaryDirectory() as temporary:
            path = Path(temporary) / "UU Tools" / "uu-cli.exe"
            path.parent.mkdir()
            path.touch()
            self.assertEqual(uu.find_cli(str(path)), path)
        with self.assertRaises(uu.UUError):
            uu.find_cli(str(path))


class UUAutomationTests(unittest.TestCase):
    def setUp(self):
        self.client = Mock()
        self.client.doctor.return_value = {"status": "ready", "running": True}
        self.client.status.return_value = []
        self.options = uu.UUOptions(enabled=True, game_id=GAME, stop_on_exit=True)
        self.engine = uu.UUAutomation(self.client, clock=lambda: 100)

    def test_disabled_options_do_not_contact_uu(self):
        self.engine.reconcile(True, uu.UUOptions())
        self.client.doctor.assert_not_called()

    def test_start_is_verified_and_not_repeated(self):
        self.engine.reconcile(True, self.options)
        self.assertEqual(self.engine.state.key, "connecting")
        self.client.status.return_value = [{"gameId": GAME, "status": "boosting", "ping": 42}]
        self.engine.reconcile(True, self.options)
        self.engine.reconcile(True, self.options)
        self.client.start_boost.assert_called_once_with(self.options)
        self.assertEqual(self.engine.state.key, "boosting")
        self.assertEqual(self.engine.state.ping, 42)
        self.engine.reconcile(False, self.options)
        self.client.stop_boost.assert_called_once_with(GAME)

    def test_existing_acceleration_is_never_owned_or_stopped(self):
        self.client.status.return_value = [{"gameId": GAME, "status": "boosting"}]
        self.engine.reconcile(True, self.options)
        self.engine.reconcile(False, self.options)
        self.client.start_boost.assert_not_called()
        self.client.stop_boost.assert_not_called()

    def test_pending_start_is_not_resent_and_can_be_stopped_on_exit(self):
        self.engine.reconcile(True, self.options)
        self.engine.reconcile(True, self.options)
        self.client.start_boost.assert_called_once()
        self.client.status.side_effect = [[{"gameId": GAME, "status": "starting"}], []]
        self.engine.reconcile(False, self.options)
        self.client.stop_boost.assert_called_once_with(GAME)

    def test_exit_after_failed_start_releases_absent_target_without_stop(self):
        self.client.start_boost.side_effect = uu.UUError("TIMEOUT")
        self.engine.reconcile(True, self.options)
        self.assertEqual(self.engine.reconcile(False, self.options).key, "waiting")
        self.client.stop_boost.assert_not_called()
        self.client.start_boost.side_effect = None
        self.assertEqual(self.engine.reconcile(True, self.options).key, "connecting")
        self.assertEqual(self.client.start_boost.call_count, 2)

    def test_stop_race_is_ignored_only_after_verified_absence(self):
        for after, expected in (([], "waiting"), ([{"gameId": GAME, "status": "boosting"}], "error")):
            with self.subTest(after=after):
                client = Mock()
                client.doctor.return_value = {"status": "ready"}
                client.status.side_effect = [[], [{"gameId": GAME, "status": "starting"}], after]
                client.stop_boost.side_effect = uu.UUError("API_ERROR", "game is not being boosted")
                engine = uu.UUAutomation(client, clock=lambda: 100)
                engine.reconcile(True, self.options)
                self.assertEqual(engine.reconcile(False, self.options).key, expected)

    def test_unrelated_stop_error_is_not_silenced(self):
        self.engine.reconcile(True, self.options)
        self.client.status.return_value = [{"gameId": GAME, "status": "starting"}]
        self.client.stop_boost.side_effect = uu.UUError("API_ERROR", "access denied")
        self.assertEqual(self.engine.reconcile(False, self.options).key, "error")

    def test_missing_target_after_pending_timeout_can_retry_after_backoff(self):
        now = [100]
        engine = uu.UUAutomation(self.client, clock=lambda: now[0])
        self.client.start_boost.side_effect = uu.UUError("TIMEOUT")
        engine.reconcile(True, self.options)
        now[0] = 146
        self.assertEqual(engine.reconcile(True, self.options).detail, "START_TIMEOUT")
        now[0] = 160
        engine.reconcile(True, self.options)
        self.client.start_boost.assert_called_once()
        now[0] = 177
        self.client.start_boost.side_effect = None
        self.assertEqual(engine.reconcile(True, self.options).key, "connecting")
        self.assertEqual(self.client.start_boost.call_count, 2)

    def test_starting_target_after_timeout_is_not_started_again(self):
        now = [100]
        engine = uu.UUAutomation(self.client, clock=lambda: now[0])
        engine.reconcile(True, self.options)
        self.client.status.return_value = [{"gameId": GAME, "status": "starting"}]
        now[0] = 146
        engine.reconcile(True, self.options)
        now[0] = 177
        engine.reconcile(True, self.options)
        self.client.start_boost.assert_called_once()

    def test_stale_request_cannot_start_client_or_acceleration(self):
        self.engine.reconcile(True, self.options, still_current=lambda: False)
        self.client.start_boost.assert_not_called()
        self.client.doctor.return_value = {"status": "not_running", "running": False}
        self.engine.reconcile(True, self.options, still_current=lambda: False)
        self.client.start_app.assert_not_called()

    def test_client_launch_waits_for_readiness_before_starting_boost(self):
        self.client.doctor.return_value = {"status": "not_running", "running": False}
        self.engine.reconcile(True, self.options)
        self.engine.reconcile(True, self.options)
        self.client.start_app.assert_called_once()
        self.client.start_boost.assert_not_called()
        self.client.doctor.return_value = {"status": "ready", "running": True}
        self.engine.reconcile(True, self.options)
        self.client.start_boost.assert_called_once()

    def test_errors_back_off_instead_of_spawning_commands_each_poll(self):
        self.client.doctor.side_effect = uu.UUError("UU_BUSY")
        self.engine.reconcile(True, self.options)
        self.engine.reconcile(True, self.options)
        self.client.doctor.assert_called_once()
        self.assertEqual(self.engine.state.detail, "UU_BUSY")

    def test_cold_start_retries_transient_endpoints_until_boost_verified(self):
        now = [100]
        engine = uu.UUAutomation(self.client, clock=lambda: now[0])
        self.client.doctor.return_value = {"status": "not_running"}
        self.assertEqual(engine.reconcile(True, self.options).key, "connecting")
        now[0] = 103
        self.client.doctor.return_value = {"status": "service_unavailable"}
        self.assertEqual(engine.reconcile(True, self.options).key, "connecting")
        now[0] = 106
        self.client.doctor.return_value = {"status": "ready"}
        self.client.start_boost.side_effect = uu.UUError("API_ERROR", "game_id is required")
        self.assertEqual(engine.reconcile(True, self.options).key, "connecting")
        now[0] = 109
        self.client.start_boost.side_effect = None
        self.assertEqual(engine.reconcile(True, self.options).key, "connecting")
        self.client.status.return_value = [{"gameId": GAME, "status": "boosting"}]
        now[0] = 112
        self.assertEqual(engine.reconcile(True, self.options).key, "boosting")
        self.client.start_app.assert_called_once()
        self.assertEqual(self.client.start_boost.call_count, 2)

    def test_cold_start_grace_is_bounded_and_errors_identify_operation(self):
        now = [100]
        engine = uu.UUAutomation(self.client, clock=lambda: now[0])
        self.client.doctor.return_value = {"status": "not_running"}
        engine.reconcile(True, self.options)
        self.client.doctor.return_value = {"status": "ready"}
        self.client.status.side_effect = uu.UUError("TIMEOUT")
        now[0] = 110
        self.assertEqual(engine.reconcile(True, self.options).key, "connecting")
        now[0] = 146
        with self.assertLogs(uu.logger, level="WARNING") as logs:
            self.assertEqual(engine.reconcile(True, self.options).key, "error")
        self.assertIn("status", " ".join(logs.output))
        self.assertEqual(engine.state.detail, "TIMEOUT")

    def test_cold_start_does_not_hide_busy_or_unrelated_api_errors(self):
        for error in (uu.UUError("UU_BUSY"), uu.UUError("API_ERROR", "access denied")):
            with self.subTest(code=str(error)):
                engine = uu.UUAutomation(self.client, clock=lambda: 100)
                self.client.doctor.return_value = {"status": "not_running"}
                engine.reconcile(True, self.options)
                self.client.doctor.return_value = {"status": "ready"}
                self.client.status.side_effect = error
                self.assertEqual(engine.reconcile(True, self.options).key, "error")

    def test_exit_during_client_warmup_cancels_acceleration(self):
        self.client.doctor.return_value = {"status": "not_running"}
        self.engine.reconcile(True, self.options)
        self.assertEqual(self.engine.reconcile(False, self.options).key, "waiting")
        self.client.doctor.return_value = {"status": "ready"}
        self.engine.reconcile(False, self.options)
        self.client.start_boost.assert_not_called()

    def test_pending_boost_uses_elapsed_time_and_retains_exit_cleanup(self):
        now = [100]
        engine = uu.UUAutomation(self.client, clock=lambda: now[0])
        engine.reconcile(True, self.options)
        self.client.status.return_value = [{"gameId": GAME, "status": "starting"}]
        for tick in range(103, 143, 3):
            now[0] = tick
            self.assertEqual(engine.reconcile(True, self.options).key, "connecting")
        now[0] = 146
        self.assertEqual(engine.reconcile(True, self.options).detail, "START_TIMEOUT")
        self.client.start_boost.assert_called_once()
        self.client.status.side_effect = [[{"gameId": GAME, "status": "starting"}], []]
        engine.reconcile(False, self.options)
        self.client.stop_boost.assert_called_once_with(GAME)

    def test_timed_out_start_is_verified_without_duplicate_commands(self):
        self.client.start_boost.side_effect = uu.UUError("TIMEOUT")
        self.assertEqual(self.engine.reconcile(True, self.options).key, "connecting")
        self.assertEqual(self.engine.reconcile(True, self.options).key, "connecting")
        self.client.start_boost.assert_called_once()
        self.client.status.return_value = [{"gameId": GAME, "status": "boosting"}]
        self.assertEqual(self.engine.reconcile(True, self.options).key, "boosting")
        self.engine.reconcile(False, self.options)
        self.client.stop_boost.assert_called_once_with(GAME)

    def test_exit_after_timed_out_start_cleans_up_pending_request(self):
        self.client.start_boost.side_effect = uu.UUError("TIMEOUT")
        self.engine.reconcile(True, self.options)
        self.client.status.side_effect = [[{"gameId": GAME, "status": "starting"}], []]
        self.engine.reconcile(False, self.options)
        self.client.stop_boost.assert_called_once_with(GAME)

    def test_initial_doctor_timeout_recovers_within_bounded_activation_grace(self):
        now = [100]
        engine = uu.UUAutomation(self.client, clock=lambda: now[0])
        self.client.doctor.side_effect = uu.UUError("TIMEOUT")
        self.assertEqual(engine.reconcile(True, self.options).key, "connecting")
        now[0] = 112
        self.client.doctor.side_effect = None
        self.assertEqual(engine.reconcile(True, self.options).key, "connecting")
        self.client.start_boost.assert_called_once()
        self.client.status.return_value = [{"gameId": GAME, "status": "boosting"}]
        self.assertEqual(engine.reconcile(True, self.options).key, "boosting")
        self.client.doctor.side_effect = uu.UUError("TIMEOUT")
        now[0] = 146
        self.assertEqual(engine.reconcile(True, self.options).key, "error")

    def test_trigger_selection(self):
        self.assertTrue(uu.UUOptions(trigger="vrchat").matches(False, True))
        self.assertFalse(uu.UUOptions(trigger="vrchat").matches(True, False))
        self.assertTrue(uu.UUOptions(trigger="steamvr").matches(True, False))
        self.assertTrue(uu.UUOptions(trigger="either").matches(False, True))

    def test_manual_node_change_is_not_stopped(self):
        self.engine.reconcile(True, self.options)
        self.client.status.return_value = [{"gameId": GAME, "status": "boosting", "nodeId": "ours"}]
        self.engine.reconcile(True, self.options)
        self.client.status.return_value = [{"gameId": GAME, "status": "boosting", "nodeId": "manual"}]
        self.engine.reconcile(False, self.options)
        self.client.stop_boost.assert_not_called()

    def test_exit_can_leave_owned_acceleration_running(self):
        options = uu.UUOptions(enabled=True, game_id=GAME, stop_on_exit=False)
        self.engine.reconcile(True, options)
        self.engine.reconcile(False, options)
        self.client.stop_boost.assert_not_called()


class UUWorkerTests(unittest.TestCase):
    def test_process_exit_during_readiness_check_cancels_start(self):
        entered, release = threading.Event(), threading.Event()
        client = Mock()
        client.status.return_value = []

        def doctor():
            entered.set()
            if not release.wait(2):
                raise RuntimeError("Test readiness wait timed out")
            return {"status": "ready", "running": True}

        client.doctor.side_effect = doctor
        worker = uu.UUWorker(client_factory=lambda path: client)
        options = uu.UUOptions(enabled=True)
        try:
            worker.update(options, steamvr_running=False, vrchat_running=True)
            self.assertTrue(entered.wait(2))
            worker.update(options, steamvr_running=False, vrchat_running=False)
            release.set()
            deadline = time.monotonic() + 2
            while worker.state.key != "waiting" and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertEqual(worker.state.key, "waiting")
            client.start_boost.assert_not_called()
            client.start_app.assert_not_called()
        finally:
            release.set()
            worker.close()


if __name__ == "__main__":
    unittest.main()
