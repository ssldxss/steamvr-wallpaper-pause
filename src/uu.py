"""UU's official CLI adapter and optional background automation."""

from dataclasses import dataclass
import json
import logging
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time


logger = logging.getLogger("steamvr_wallpaper_pause.uu")
VRCHAT_GAME_ID = "5a4f5632e3a8b2db8b86a51f"
_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
_STARTUP_TIMEOUT = 45


class UUError(Exception):
    def __init__(self, code: str, message: str = ""):
        self.code = code
        super().__init__(message or code)


@dataclass(frozen=True)
class UUOptions:
    enabled: bool = False
    trigger: str = "vrchat"
    auto_launch: bool = True
    stop_on_exit: bool = False
    cli_path: str = "auto"
    game_id: str = VRCHAT_GAME_ID
    zone_id: str = ""
    server_id: str = ""

    def __post_init__(self):
        if self.trigger not in ("vrchat", "steamvr", "either"):
            raise ValueError("Unknown UU trigger")
        if bool(self.zone_id) != bool(self.server_id):
            raise ValueError("UU zone and server must be selected together")
        if not self.game_id.strip():
            raise ValueError("UU game ID is required")

    def matches(self, steamvr_running: bool, vrchat_running: bool) -> bool:
        return (
            (self.trigger in ("steamvr", "either") and steamvr_running)
            or (self.trigger in ("vrchat", "either") and vrchat_running)
        )

    @classmethod
    def from_config(cls, config):
        return cls(**{
            name: getattr(config, f"uu_{name}")
            for name in cls.__dataclass_fields__
        })


def _install_roots() -> list[Path]:
    roots = []
    for environment in ("ProgramFiles(x86)", "ProgramFiles", "LOCALAPPDATA"):
        base = os.environ.get(environment)
        if base:
            roots.append(Path(base) / "Netease" / "UU")
    if sys.platform == "win32":
        import winreg

        uninstall = r"Software\Microsoft\Windows\CurrentVersion\Uninstall"
        for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            for view in (winreg.KEY_WOW64_32KEY, winreg.KEY_WOW64_64KEY):
                try:
                    with winreg.OpenKey(hive, uninstall, 0, winreg.KEY_READ | view) as key:
                        for index in range(winreg.QueryInfoKey(key)[0]):
                            try:
                                with winreg.OpenKey(key, winreg.EnumKey(key, index)) as app:
                                    name = winreg.QueryValueEx(app, "DisplayName")[0]
                                    if "UU" not in name or not any(
                                        word in name for word in ("加速", "Booster", "booster")
                                    ):
                                        continue
                                    try:
                                        location = winreg.QueryValueEx(app, "InstallLocation")[0]
                                    except OSError:
                                        location = ""
                                    if location:
                                        roots.append(Path(location))
                                    else:
                                        command = winreg.QueryValueEx(app, "UninstallString")[0]
                                        match = re.match(r'^\s*"?(.+?\.exe)"?(?:\s|$)', command)
                                        if match:
                                            roots.append(Path(match.group(1)).parent)
                            except OSError:
                                continue
                except OSError:
                    continue
    return list(dict.fromkeys(root for root in roots if root.is_dir()))


def find_cli(explicit_path: str = "auto") -> Path:
    """Find a skill CLI or extract it from the package supplied with installed UU."""
    if explicit_path and explicit_path != "auto":
        path = Path(os.path.expandvars(explicit_path)).expanduser()
        if path.is_file():
            return path
        raise UUError("CLI_MISSING")

    home = Path.home()
    cache = Path(os.environ.get("LOCALAPPDATA", home / ".cache")) / "SteamVRWallpaperPause" / "tools"
    cached_cli = cache / "netease-uu-booster" / "bin" / "uu-cli.exe"
    candidates = [cached_cli]
    for directory in (".codex", ".claude", ".agents", ".codebuddy", ".gemini"):
        candidates.append(home / directory / "skills" / "netease-uu-booster" / "bin" / "uu-cli.exe")
    for candidate in candidates:
        if candidate.is_file():
            return candidate

    for root in _install_roots():
        versions = sorted(
            (path for path in root.iterdir() if path.is_dir() and path.name.isdigit()),
            key=lambda path: int(path.name), reverse=True,
        )
        for version in versions + [root]:
            archive = version / "netease-uu-booster.7z"
            extractor = version / "7za.exe"
            if not archive.is_file() or not extractor.is_file():
                continue
            try:
                cache.mkdir(parents=True, exist_ok=True)
                result = subprocess.run(
                    [str(extractor), "x", str(archive), f"-o{cache}",
                     r"netease-uu-booster\bin\uu-cli.exe", "-y"],
                    capture_output=True, timeout=15, creationflags=_NO_WINDOW,
                )
                if result.returncode == 0 and cached_cli.is_file():
                    return cached_cli
            except (OSError, subprocess.TimeoutExpired) as error:
                logger.warning("UU tool discovery failed: %s", error)
    raise UUError("CLI_MISSING")


class UUClient:
    def __init__(self, cli_path: str = "auto"):
        self.cli_path = cli_path
        self._resolved: Path | None = None

    def _run(self, *arguments: str) -> dict:
        if self._resolved is None:
            self._resolved = find_cli(self.cli_path)
        try:
            process = subprocess.run(
                [str(self._resolved), "--json", *arguments],
                capture_output=True, encoding="utf-8-sig", errors="replace",
                timeout=10, creationflags=_NO_WINDOW,
            )
        except subprocess.TimeoutExpired as error:
            raise UUError("TIMEOUT") from error
        except OSError as error:
            self._resolved = None
            raise UUError("CLI_MISSING", str(error)) from error
        try:
            result = json.loads(process.stdout)
        except (ValueError, TypeError) as error:
            raise UUError("INVALID_RESPONSE") from error
        if not isinstance(result, dict):
            raise UUError("INVALID_RESPONSE")
        if result.get("success") is not True or process.returncode != 0:
            failure = result.get("error") or {}
            if not isinstance(failure, dict):
                failure = {}
            raise UUError(str(failure.get("code", "API_ERROR")), str(failure.get("message", "")))
        data = result.get("data")
        if not isinstance(data, dict):
            raise UUError("INVALID_RESPONSE")
        return data

    def doctor(self) -> dict:
        return self._run("doctor")

    def status(self) -> list[dict]:
        boosters = self._run("status").get("boosters", [])
        if not isinstance(boosters, list) or not all(isinstance(item, dict) for item in boosters):
            raise UUError("INVALID_RESPONSE")
        return boosters

    def regions(self, game_id: str) -> list[dict]:
        games = self._run("games", "--id", game_id).get("games", [])
        if not isinstance(games, list):
            raise UUError("INVALID_RESPONSE")
        regions = []
        for game in games:
            if not isinstance(game, dict):
                continue
            for zone in game.get("zones", []):
                servers = zone.get("servers", [])
                for server in servers:
                    zone_id = str(zone.get("zone_id", zone.get("id", "")))
                    server_id = str(server.get("server_id", server.get("id", "")))
                    if not zone_id or not server_id:
                        continue
                    name = str(zone.get("zone_name", zone.get("name", zone_id)))
                    if len(servers) > 1:
                        name += " / " + str(server.get("server_name", server.get("name", server_id)))
                    regions.append({"name": name, "zone_id": zone_id, "server_id": server_id})
        return regions

    def start_app(self) -> None:
        # A GUI launch must not wait for captured CLI output/client lifetime.
        for root in _install_roots():
            launcher = root / "uu_launcher.exe"
            if launcher.is_file():
                try:
                    os.startfile(str(launcher))
                except OSError as error:
                    raise UUError("UU_NOT_RUNNING", str(error)) from error
                return
        raise UUError("UU_NOT_INSTALLED")

    def open_app(self) -> None:
        self.start_app()

    def start_boost(self, options: UUOptions) -> None:
        arguments = ["start", "--id", options.game_id]
        if options.zone_id:
            arguments += ["--zone", options.zone_id, "--server", options.server_id]
        self._run(*arguments)

    def stop_boost(self, game_id: str) -> None:
        if not game_id:
            raise ValueError("Stopping UU requires a game ID")
        self._run("stop", "--id", game_id)


@dataclass(frozen=True)
class UUState:
    key: str = "disabled"
    detail: str = ""
    ping: float | None = None


class UUAutomation:
    """Reconcile one state step; pending commands never count as verified boosts."""

    def __init__(self, client: UUClient, *, clock=time.monotonic):
        self.client = client
        self.clock = clock
        self.state = UUState()
        self._owned: str | None = None
        self._pending: str | None = None
        self._fingerprint: tuple | None = None
        self._pending_deadline: float | None = None
        self._launch_deadline: float | None = None
        self._activation_deadline: float | None = None
        self._retry_at = 0.0

    def _set(self, key: str, detail: str = "", ping=None):
        self.state = UUState(key, detail, ping if isinstance(ping, (int, float)) else None)
        return self.state

    @staticmethod
    def _target(boosters: list[dict], game_id: str) -> dict:
        return next((item for item in boosters if str(item.get("gameId")) == game_id), {})

    @staticmethod
    def _node(booster: dict) -> tuple:
        return booster.get("nodeId"), booster.get("regionId")

    def _release(self):
        self._owned = self._pending = None
        self._fingerprint = None
        self._pending_deadline = None

    def reconcile(self, active: bool, options: UUOptions, *, still_current=lambda: True):
        if not still_current():
            return self.state
        now = self.clock()
        operation = "doctor"
        try:
            if not active or not options.enabled:
                self._launch_deadline = None
                self._activation_deadline = None
                game_id = self._owned or self._pending
                if game_id and options.stop_on_exit:
                    doctor = self.client.doctor()
                    if doctor.get("status") == "not_running":
                        self._release()
                    elif doctor.get("status") != "ready":
                        raise UUError("SERVICE_UNAVAILABLE")
                    else:
                        operation = "status"
                        current = self._target(self.client.status(), game_id)
                        if not current or current.get("status") == "not_boosting":
                            logger.info("UU target already stopped; cleared previous request: game=%s", game_id)
                            self._release()
                        elif self._fingerprint is not None and self._node(current) != self._fingerprint:
                            # The user chose another node; that session is no longer ours.
                            self._release()
                        elif current.get("status") == "stopping":
                            return self._set("stopping")
                        elif still_current():
                            operation = "stop_boost"
                            stop_error = None
                            try:
                                self.client.stop_boost(game_id)
                            except UUError as error:
                                if error.code != "API_ERROR" or str(error).strip().lower() != "game is not being boosted":
                                    raise
                                stop_error = error
                            operation = "status"
                            current = self._target(self.client.status(), game_id)
                            if current.get("status") in ("boosting", "starting", "stopping"):
                                if stop_error:
                                    operation = "stop_boost"
                                    raise stop_error
                                return self._set("stopping")
                            self._release()
                else:
                    self._release()
                self._retry_at = 0
                return self._set("waiting" if options.enabled else "disabled")

            if now < self._retry_at:
                return self.state
            if self._activation_deadline is None:
                self._activation_deadline = now + _STARTUP_TIMEOUT
            doctor = self.client.doctor()
            status = doctor.get("status")
            if status == "not_installed":
                raise UUError("UU_NOT_INSTALLED")
            if status == "not_running":
                if not options.auto_launch:
                    raise UUError("UU_NOT_RUNNING")
                if self._launch_deadline is None:
                    if still_current():
                        self._launch_deadline = now + _STARTUP_TIMEOUT
                        operation = "start_app"
                        self.client.start_app()
                        logger.info("UU client launched; waiting for its acceleration service")
                elif now >= self._launch_deadline:
                    self._launch_deadline = None
                    raise UUError("UU_NOT_RUNNING")
                return self._set("connecting")
            if status != "ready":
                raise UUError("SERVICE_UNAVAILABLE")
            operation = "status"
            current = self._target(self.client.status(), options.game_id)
            if current.get("status") == "boosting":
                self._launch_deadline = None
                self._pending_deadline = None
                if self._pending == options.game_id:
                    self._owned, self._pending = self._pending, None
                    self._fingerprint = self._node(current)
                elif self._owned and self._fingerprint != self._node(current):
                    self._release()
                return self._set("boosting", ping=current.get("ping"))
            if self._pending:
                if self._pending_deadline is not None and self.clock() >= self._pending_deadline:
                    # Retry only after verifying that the old request produced no session.
                    if not current or current.get("status") == "not_boosting":
                        logger.info("UU start produced no session; allowing retry after backoff: game=%s", self._pending)
                        self._release()
                    operation = "start_boost"
                    raise UUError("START_TIMEOUT")
                return self._set("connecting")
            if current.get("status") in ("starting", "stopping"):
                return self._set("connecting")
            if still_current():
                operation = "start_boost"
                self._pending = options.game_id
                self._pending_deadline = self.clock() + _STARTUP_TIMEOUT
                try:
                    self.client.start_boost(options)
                    logger.info("UU acceleration requested; verifying status: game=%s", options.game_id)
                except UUError as error:
                    # A lost reply does not prove that UU rejected the command.
                    if error.code not in ("TIMEOUT", "INVALID_RESPONSE"):
                        self._pending = self._pending_deadline = None
                    raise
            return self._set("connecting")
        except UUError as error:
            transient = error.code in ("TIMEOUT", "SERVICE_UNAVAILABLE", "INVALID_RESPONSE") or (
                error.code == "API_ERROR" and str(error).strip().lower() == "game_id is required"
            )
            deadlines = [end for end in (
                self._activation_deadline, self._launch_deadline, self._pending_deadline
            ) if end is not None]
            if active and options.enabled and transient and deadlines and self.clock() < max(deadlines):
                logger.info("UU awaiting readiness: operation=%s code=%s (%s)", operation, error.code, error)
                return self._set("connecting")
            if self.state.detail != error.code:
                logger.warning("UU automation: operation=%s code=%s (%s)", operation, error.code, error)
            self._retry_at = self.clock() + 30
            return self._set("error", error.code)


class UUWorker:
    """One lazy worker, with the latest process snapshot replacing stale requests."""

    def __init__(self, *, client_factory=UUClient):
        self._factory = client_factory
        self._lock = threading.Lock()
        self._wake = threading.Event()
        self._closed = threading.Event()
        self._request: tuple[UUOptions, bool] | None = None
        self._thread: threading.Thread | None = None
        self._state = UUState()

    @property
    def started(self) -> bool:
        return self._thread is not None

    @property
    def state(self) -> UUState:
        with self._lock:
            return self._state

    def update(self, options: UUOptions, *, steamvr_running: bool, vrchat_running: bool):
        if self._closed.is_set() or (not options.enabled and not self.started):
            return
        request = (options, options.enabled and options.matches(steamvr_running, vrchat_running))
        with self._lock:
            if self._request == request:
                return
            self._request = request
            if self._thread is None:
                self._thread = threading.Thread(target=self._run, name="uu-automation", daemon=True)
                self._thread.start()
        self._wake.set()

    def _current(self, request) -> bool:
        with self._lock:
            return not self._closed.is_set() and self._request is request

    def _run(self):
        engine = None
        path = None
        delay = None
        while not self._closed.is_set():
            self._wake.wait(delay)
            self._wake.clear()
            with self._lock:
                request = self._request
            if self._closed.is_set() or request is None:
                break
            options, active = request
            try:
                if path != options.cli_path:
                    client = self._factory(options.cli_path)
                    if engine is None:
                        engine = UUAutomation(client)
                    else:
                        engine.client = client
                    path = options.cli_path
                state = engine.reconcile(active, options, still_current=lambda: self._current(request))
            except Exception:
                logger.exception("Unexpected UU worker failure")
                state = UUState("error", "API_ERROR")
            with self._lock:
                if self._request is request:
                    self._state = state
            delay = 3 if state.key in ("connecting", "stopping") else 30

    def close(self):
        self._closed.set()
        self._wake.set()
        if self._thread and self._thread is not threading.current_thread():
            self._thread.join(timeout=2)
