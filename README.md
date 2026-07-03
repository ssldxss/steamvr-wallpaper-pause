# SteamVR Wallpaper Pause

Automatically pauses Wallpaper Engine when SteamVR is running, and resumes it when SteamVR exits. Lives in your system tray, starts with Windows — install once and forget about it.

## Features

- **System tray icon** with status indication (green = monitoring, orange = VR active)
- **Auto-start with Windows**, minimized to tray
- **Automatic detection** of SteamVR via process monitoring
- **Manual override** via tray menu (pause/resume Wallpaper Engine on demand)
- **Settings window** for configuring polling interval, Wallpaper Engine path, and auto-start
- **Windows installer** with Start Menu shortcuts and uninstaller
- **Toast notifications** when wallpaper is paused/resumed

## Requirements (Development)

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
  "polling_interval": 5,
  "wallpaper_engine_path": "auto",
  "auto_start": true,
  "verbose": false
}
```

- **polling_interval**: Seconds between SteamVR process checks (default: 5)
- **wallpaper_engine_path**: Path to `wallpaper32.exe`, or `"auto"` to auto-detect (default: "auto")
- **auto_start**: Whether to start with Windows (default: true)
- **verbose**: Enable verbose console logging (default: false)

## How It Works

1. Every N seconds, checks if `vrserver.exe` (SteamVR) is running
2. When SteamVR starts → pauses Wallpaper Engine via `wallpaper32.exe -control pause`
3. When SteamVR stops → resumes Wallpaper Engine via `wallpaper32.exe -control play`
4. Only acts on state transitions — no repeated commands while SteamVR stays running/stopped

## License

MIT
