"""Verify real installers only on disposable GitHub-hosted Windows runners."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parent.parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    # Setup writes HKCU uninstall metadata even with a temporary /DIR.
    if sys.platform != "win32" or os.environ.get("GITHUB_ACTIONS") != "true":
        raise SystemExit("Run only on a disposable GitHub Actions Windows runner.")

    executable = ROOT / "dist" / "SteamVRWallpaperPause.exe"
    installer = ROOT / "installer" / "Output" / "SteamVRWallpaperPause-Setup.exe"
    subprocess.run([str(executable), "--settings", "--help"], check=True, timeout=30)

    with TemporaryDirectory(prefix="steamvr-release-check-") as temporary:
        directory = Path(temporary)
        appdata = directory / "appdata"
        localappdata = directory / "localappdata"
        appdata.mkdir()
        localappdata.mkdir()
        environment = dict(os.environ, APPDATA=str(appdata), LOCALAPPDATA=str(localappdata))
        installed = directory / "installation"
        command = [
            str(installer), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART",
            "/NOCLOSEAPPLICATIONS", "/NORESTARTAPPLICATIONS", "/NOICONS", "/TASKS=",
            f"/DIR={installed}",
        ]
        subprocess.run(command + [f"/LOG={directory / 'fresh-install.log'}"],
                       env=environment, check=True, timeout=120)
        config = appdata / "SteamVRWallpaperPause" / "config.json"
        values = json.loads(config.read_text(encoding="utf-8-sig"))
        assert values["polling_interval"] == 1, "Fresh-install interval must be 1 second"
        assert digest(installed / executable.name) == digest(executable), "Installer contains a different exe"

        values.update(polling_interval=7, language="en", auto_start=False,
                      uu_enabled=True, uu_zone_id="saved-zone", uu_server_id="saved-server")
        original = (json.dumps(values, ensure_ascii=False, indent=4) + "\n").encode("utf-8")
        config.write_bytes(original)
        subprocess.run(command + [f"/LOG={directory / 'upgrade.log'}"],
                       env=environment, check=True, timeout=120)
        assert config.read_bytes() == original, "Upgrade changed existing configuration"
        assert digest(installed / executable.name) == digest(executable), "Upgrade installed a different exe"
        print("Installer checks passed: fresh install, 1-second default, exact exe, config preservation")

    release = ROOT / "dist" / "release"
    release.mkdir(exist_ok=True)
    packages = [executable, installer]
    for package in packages:
        shutil.copy2(package, release / package.name)
    (release / "SHA256SUMS.txt").write_text(
        "".join(f"{digest(package)}  {package.name}\n" for package in packages), encoding="ascii"
    )
    print("Verified packages ready:", release)


if __name__ == "__main__":
    main()
