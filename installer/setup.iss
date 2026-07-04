; Inno Setup Script for SteamVR Wallpaper Pause
; Requires Inno Setup 6: https://jrsoftware.org/isinfo.php

#define MyAppName "SteamVR Wallpaper Pause"
#define MyAppVersion "1.1.0"
#define MyAppPublisher "Open Source"
#define MyAppURL "https://github.com/ssldxss/steamvr-wallpaper-pause"
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
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "{#MyAppName}"; ValueData: """{app}\{#MyAppExeName}"" --minimized"; Tasks: autostart; Flags: uninsdeletevalue

[UninstallRun]
Filename: "{app}\{#MyAppExeName}"; Parameters: "--remove-autostart"; Flags: runhidden

[Code]
var
  LanguagePage: TInputOptionWizardPage;

procedure InitializeWizard;
begin
  LanguagePage := CreateInputOptionPage(
    wpWelcome,
    'Language / 语言',
    'Please select your language / 请选择语言',
    'The application will use this language as the default. You can change it later in Settings.' + #13#10 +
    '应用程序将以此语言作为默认语言。您之后可以在设置中更改。',
    True,
    False
  );
  LanguagePage.Add('中文 (Chinese)');
  LanguagePage.Add('English');
  LanguagePage.Values[0] := True;
end;

procedure WriteInitialConfig;
var
  ConfigDir, ConfigPath, AppDataDir: string;
  ConfigJSON: string;
begin
  AppDataDir := GetEnv('APPDATA');
  ConfigDir := AppDataDir + '\SteamVRWallpaperPause';
  ConfigPath := ConfigDir + '\config.json';

  if not DirExists(ConfigDir) then
    CreateDir(ConfigDir);

  if LanguagePage.Values[1] then
    ConfigJSON := '{' + #13#10 +
      '  "polling_interval": 5,' + #13#10 +
      '  "wallpaper_engine_path": "auto",' + #13#10 +
      '  "auto_start": true,' + #13#10 +
      '  "verbose": false,' + #13#10 +
      '  "action_on_vr_start": "stop",' + #13#10 +
      '  "language": "en"' + #13#10 +
      '}'
  else
    ConfigJSON := '{' + #13#10 +
      '  "polling_interval": 5,' + #13#10 +
      '  "wallpaper_engine_path": "auto",' + #13#10 +
      '  "auto_start": true,' + #13#10 +
      '  "verbose": false,' + #13#10 +
      '  "action_on_vr_start": "stop",' + #13#10 +
      '  "language": "zh"' + #13#10 +
      '}';

  SaveStringToFile(ConfigPath, ConfigJSON, False);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    WriteInitialConfig;
  end;
end;
