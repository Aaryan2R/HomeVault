; HomeVault installer script
; Compile this to create HomeVault_Setup.exe

#define AppName "HomeVault"
#define AppVersion "1.3.0"
#define AppPublisher "Aaryan2R"
#define AppURL "https://github.com/Aaryan2R/HomeVault"
#define AppExeName "HomeVault.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
DisableDirPage=no
OutputDir=installer_output
OutputBaseFilename=HomeVault_Setup
SetupIconFile=static\icon.ico
Compression=lzma2/fast
SolidCompression=no
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName}
VersionInfoVersion={#AppVersion}
VersionInfoCompany={#AppPublisher}
VersionInfoDescription=HomeVault Private Cloud Storage

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"
Name: "startupentry"; Description: "Start HomeVault automatically with Windows"; GroupDescription: "Startup:"; Flags: unchecked

[Files]
; Built launcher folder from PyInstaller
Source: "dist\HomeVault\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Python helper used during install
Source: "setup_helper.py"; DestDir: "{app}"; Flags: ignoreversion

; Keep the IP watcher with the app files
Source: "ip_watcher.py"; DestDir: "{app}"; Flags: ignoreversion

; Files needed while installing
; The small Python zip only runs setup_helper.py during setup
Source: "installer_assets\*"; DestDir: "{app}\installer_assets"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
; Folders used for uploads and thumbnails
Name: "{app}\storage\Photos"
Name: "{app}\storage\Videos"
Name: "{app}\storage\Documents"
Name: "{app}\storage\Others"
Name: "{app}\static\thumbnails"

[Icons]
; Start Menu shortcuts
Name: "{group}\HomeVault"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\_internal\static\icon.ico"
Name: "{group}\Uninstall HomeVault"; Filename: "{uninstallexe}"

; Use the HomeVault icon for the desktop shortcut
Name: "{autodesktop}\HomeVault"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\_internal\static\icon.ico"; Tasks: desktopicon

[Registry]
; Add autostart only when the user selects it
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "HomeVault"; ValueData: """{app}\{#AppExeName}"""; Flags: uninsdeletevalue; Tasks: startupentry

[Run]
; Unzip the small Python runtime into the temp folder
Filename: "cmd.exe"; \
  Parameters: "/C mkdir ""{tmp}\EmbedPy"" & tar -xf ""{app}\installer_assets\python-3.13.13-embed-amd64.zip"" -C ""{tmp}\EmbedPy"""; \
  StatusMsg: "Preparing setup runtime..."; \
  Flags: runhidden waituntilterminated

; Use it to run the setup helper
; The helper sets up Nginx, Bonjour, .env, firewall and hosts
Filename: "{tmp}\EmbedPy\python.exe"; \
  Parameters: """{app}\setup_helper.py"" --install-dir ""{app}"""; \
  WorkingDir: "{app}"; \
  StatusMsg: "Configuring HomeVault..."; \
  Flags: runhidden waituntilterminated

; Let the user launch HomeVault when setup finishes
Filename: "{app}\{#AppExeName}"; \
  Description: "Launch HomeVault now"; \
  Flags: shellexec nowait postinstall skipifsilent

[UninstallRun]
; Stop HomeVault and Nginx before uninstalling
Filename: "taskkill"; Parameters: "/F /IM HomeVault.exe"; Flags: runhidden; RunOnceId: "KillHomeVault"
Filename: "taskkill"; Parameters: "/F /IM nginx.exe"; Flags: runhidden; RunOnceId: "KillNginx"

[UninstallDelete]
; Remove files created after installation
; No venv is created because Python is already inside HomeVault.exe
Type: files; Name: "{app}\.env"
Type: files; Name: "{app}\homevault.db"
Type: files; Name: "{app}\setup.log"
Type: files; Name: "{app}\flask.log"
Type: files; Name: "{app}\debug.log"
Type: filesandordirs; Name: "{app}\storage"
Type: filesandordirs; Name: "{app}\static\thumbnails"

[Code]
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ResultCode: Integer;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    // Remove HomeVault firewall rules on uninstall
    Exec('netsh', 'advfirewall firewall delete rule name="HomeVault"',
         '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    Exec('netsh', 'advfirewall firewall delete rule name="HomeVault-Flask"',
         '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    Exec('netsh', 'advfirewall firewall delete rule name="HomeVault-Nginx"',
         '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  end;
end;
