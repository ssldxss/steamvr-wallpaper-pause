# SteamVR Wallpaper Pause

[中文](README.md)

A small utility for VRChat and other SteamVR players.

Automatically stops or pauses Wallpaper Engine when SteamVR is running, and resumes it when SteamVR exits. Lives in your system tray, starts with Windows — install once and forget about it.

## Quick Start

[Installer](https://github.com/ssldxss/steamvr-wallpaper-pause/releases/latest/download/SteamVRWallpaperPause-Setup.exe)

[Installer (Lanzou Cloud)](https://zako.lanzoul.com/iZIL74e9746f)

Password:

```
aey9
```

## ZakoZako!

<img width="300" height="300" alt="53EA5472A0EF239DD1011DE851DD1100" src="https://github.com/user-attachments/assets/d11caf12-852e-4740-8d8d-f9817c6e7c1c" />
<img width="300" height="300" alt="image" src="https://github.com/user-attachments/assets/97d9fca7-7643-4b45-981a-6ff4694b8f85" />

## Features

- **System tray icon** with status indication (green = monitoring, orange = VR active)
- **Configurable action**: Choose between "Stop" (`-control stop`) or "Pause" (`-control pause`) when SteamVR starts
- **Auto-start with Windows**, minimized to tray
- **Automatic detection** of SteamVR via process monitoring
- **Manual control**: Stop/resume Wallpaper Engine from the tray menu
- **Settings window**: Configure polling interval, Wallpaper Engine path, action mode, and auto-start
- **Optional UU automation**: Open UU and accelerate VRChat when VRChat, SteamVR, or either starts; choose a region and optional exit cleanup
- **Connection guide**: Manual UU authorization steps and read-only connection checks; technical paths and polling settings stay in Advanced
- **Windows installer** with Start Menu shortcuts and uninstaller
- **Toast notifications** when wallpaper is stopped/resumed

## Set Up UU Automation

1. Open Settings from the tray menu and select **Connect UU**.
2. Install and sign into NetEase UU. Open its top-right menu > Settings > AI Settings,
   then manually enable authorization.
3. Close UU's settings window, return here, and choose **Check connection**.
4. Enable automation, choose a trigger and a specific region, and save.

Enabling UU options loads actual regions. While loading or unavailable, the UI
shows connection guidance instead of an empty dropdown. There is no unspecified
"Use UU preferences" choice, and a failed refresh preserves an existing region.

UU automation is disabled by default. It can open UU when needed and preserves
the node of any existing acceleration. Optional exit cleanup stops only
acceleration initiated by this utility. With **Either app starts**, the session
ends after both apps exit. SteamVR is a trigger; the acceleration target is VRChat.

The official control tool is discovered in installed skills or extracted from the
package shipped with UU; Codex is not required. If discovery fails, select
`uu-cli.exe` in Advanced. Authorization is always enabled manually in UU.

Preview the settings without changing real configuration or Windows startup:

```bash
python scripts/preview_settings.py
python scripts/preview_settings.py --language en --enabled --size 780x560
```

## Requirements (Development)

To build without local compiler setup, manually run **Build Windows release** in
GitHub Actions for the desired branch or tag. It runs tests, builds both executables,
verifies fresh installation and configuration preservation on upgrade, and uploads
the packages with SHA256 checksums.

- Python 3.10+
- Dependencies: `pystray`, `Pillow`, `psutil` (see `requirements.txt`)
- PyInstaller (for building the exe)
- Inno Setup 6 (for building the installer)

## Quick Start (Development)

```bash
# Install dependencies
pip install -r requirements.txt

# Run in console mode (for debugging)
python src/main.py --console --verbose

# Run normally (tray only)
python src/main.py
```

## Building the Installer

```bash
# 1. Build the standalone exe with PyInstaller
build.bat

# 2. Open installer/setup.iss in Inno Setup Compiler and compile
#    Output: installer/Output/SteamVRWallpaperPause-Setup.exe
```

## Configuration

Configuration is stored in `%APPDATA%\SteamVRWallpaperPause\config.json`:

```json
{
  "polling_interval": 1,
  "wallpaper_engine_path": "auto",
  "auto_start": true,
  "verbose": false,
  "action_on_vr_start": "stop"
}
```

- **polling_interval**: Seconds between SteamVR / VRChat process checks (default: 1). Upgrades preserve existing settings.
- **wallpaper_engine_path**: Path to `wallpaper32.exe`, or `"auto"` to auto-detect (default: "auto")
- **auto_start**: Whether to start with Windows (default: true)
- **verbose**: Enable verbose console logging (default: false)
- **action_on_vr_start**: `"stop"` or `"pause"` — what to do when SteamVR starts (default: "stop")

## How It Works

1. Every N seconds, checks if `vrserver.exe` (SteamVR) is running
2. When SteamVR starts → stops or pauses Wallpaper Engine via `wallpaper32.exe -control stop/pause`
3. When SteamVR stops → resumes Wallpaper Engine via `wallpaper32.exe -control play`
4. Only acts on state transitions — no repeated commands while SteamVR stays running/stopped

## License

MIT
