@echo off
REM Build script for SteamVR Wallpaper Pause
REM Requires: Python 3.10+, PyInstaller, Inno Setup 6

echo ============================================
echo SteamVR Wallpaper Pause - Build Script
echo ============================================

REM Step 1: Install Python dependencies
echo.
echo [1/3] Installing Python dependencies...
pip install -r requirements.txt
pip install pyinstaller

REM Step 2: Generate icon if not present
echo.
echo [2/4] Ensuring app icon exists...
if not exist "assets\app.ico" (
    echo Generating default app icon...
    python -c "from PIL import Image, ImageDraw; img=Image.new('RGBA',(256,256),(0,0,0,0)); d=ImageDraw.Draw(img); d.ellipse([8,8,247,247],fill=(0,180,80),outline=(255,255,255,200),width=4); img.save('assets/app.ico',format='ICO',sizes=[(256,256),(64,64),(48,48),(32,32),(16,16)])"
)

REM Step 3: Build standalone exe with PyInstaller
echo.
echo [3/4] Building standalone executable with PyInstaller...
pyinstaller --clean --noconfirm SteamVRWallpaperPause.spec

REM Step 4: Inno Setup reminder
echo.
echo [4/4] Build complete!
echo.
echo The standalone exe is at: dist\SteamVRWallpaperPause.exe
echo.
echo To create the installer:
echo   1. Open installer\setup.iss in Inno Setup Compiler
echo   2. Click Build -^> Compile
echo   3. The installer will be at: installer\Output\SteamVRWallpaperPause-Setup.exe
echo.
echo ============================================
echo Done!
echo ============================================

pause
