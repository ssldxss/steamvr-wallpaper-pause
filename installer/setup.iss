; Inno Setup Script for SteamVR Wallpaper Pause
; Requires Inno Setup 6: https://jrsoftware.org/isinfo.php

#define MyAppName "SteamVR Wallpaper Pause"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Open Source"
#define MyAppURL "https://github.com/user/steamvr-wallpaper-pause"
#define MyAppExeName "SteamVRWallpaperPause.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={localappdata}\Programs\SteamVRWallpaperPause
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=Output
OutputBaseFilename=SteamVRWallpaperPause-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
PrivilegesRequired=lowest

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"
Name: "startmenu"; Description: "Create a &Start Menu folder"; GroupDescription: "Additional icons:"
Name: "autostart"; Description: "&Start with Windows (minimized to tray)"; GroupDescription: "Startup options:"; Flags: checkedonce

[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\assets\app.ico"; DestDir: "{app}\assets"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\app.ico"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\app.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[Registry]
; Auto-start with Windows (user-level — no admin required)
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "{#MyAppName}"; ValueData: """{app}\{#MyAppExeName}"" --minimized"; Tasks: autostart; Flags: uninsdeletevalue

[UninstallRun]
; Clean up auto-start if it was enabled outside the installer
Filename: "{app}\{#MyAppExeName}"; Parameters: "--remove-autostart"; Flags: runhidden

[Code]
// Optional: Add custom wizard page or validation here
