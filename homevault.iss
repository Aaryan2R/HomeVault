; HomeVault Inno Setup Script
; Builds HomeVault_Setup.exe

#define AppName "HomeVault"
#define AppVersion "1.2.0"
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
OutputDir=installer_output
OutputBaseFilename=HomeVault_Setup
SetupIconFile=static\icon.ico
Compression=lzma
SolidCompression=yes
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
; Main application files
Source: "dist\HomeVault\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Setup helper script
Source: "setup_helper.py"; DestDir: "{app}"; Flags: ignoreversion

; Nginx config and ip_watcher
Source: "ip_watcher.py"; DestDir: "{app}"; Flags: ignoreversion

; Installer assets (Python, Bonjour, Nginx)
Source: "installer_assets\*"; DestDir: "{app}\installer_assets"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
; Create storage folders
Name: "{app}\storage\Photos"
Name: "{app}\storage\Videos"
Name: "{app}\storage\Documents"
Name: "{app}\storage\Others"
Name: "{app}\static\thumbnails"

[Icons]
; Start Menu
Name: "{group}\HomeVault"; Filename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall HomeVault"; Filename: "{uninstallexe}"

; Desktop shortcut
Name: "{autodesktop}\HomeVault"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Registry]
; Autostart with Windows — only if user chose this task
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "HomeVault"; ValueData: """{app}\{#AppExeName}"""; Flags: uninsdeletevalue; Tasks: startupentry

[Run]
; Install a small local Python runtime only for setup_helper.py.
Filename: "{app}\installer_assets\python-installer.exe"; \
  Parameters: "/quiet InstallAllUsers=0 PrependPath=0 Include_test=0 TargetDir=""{tmp}\HomeVaultPython"""; \
  StatusMsg: "Installing setup runtime..."; \
  Flags: runhidden waituntilterminated; \
  Check: not SetupPythonExists

; Run setup helper through the local runtime.
Filename: "{tmp}\HomeVaultPython\python.exe"; \
  Parameters: """{app}\setup_helper.py"" --install-dir ""{app}"""; \
  WorkingDir: "{app}"; \
  StatusMsg: "Configuring HomeVault..."; \
  Flags: runhidden waituntilterminated; \
  Check: SetupPythonExists

; Last fallback for developer machines if the local runtime is not available.
Filename: "python"; \
  Parameters: """{app}\setup_helper.py"" --install-dir ""{app}"""; \
  WorkingDir: "{app}"; \
  StatusMsg: "Setting up HomeVault..."; \
  Flags: runhidden waituntilterminated; \
  Check: not SetupPythonExists

; Launch HomeVault after install if user wants
Filename: "{app}\{#AppExeName}"; \
  Description: "Launch HomeVault now"; \
  Flags: nowait postinstall skipifsilent

[UninstallRun]
; Stop HomeVault before uninstalling
Filename: "taskkill"; Parameters: "/F /IM HomeVault.exe"; Flags: runhidden; RunOnceId: "KillHomeVault"
Filename: "taskkill"; Parameters: "/F /IM nginx.exe"; Flags: runhidden; RunOnceId: "KillNginx"

[UninstallDelete]
; Clean up generated files on uninstall
Type: files; Name: "{app}\.env"
Type: files; Name: "{app}\homevault.db"
Type: files; Name: "{app}\setup.log"
Type: files; Name: "{app}\flask.log"
Type: files; Name: "{app}\debug.log"
Type: filesandordirs; Name: "{app}\storage"
Type: filesandordirs; Name: "{app}\static\thumbnails"
Type: filesandordirs; Name: "{app}\venv"

[Code]
function SetupPythonExists(): Boolean;
begin
  Result := FileExists(ExpandConstant('{tmp}\HomeVaultPython\python.exe'));
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ResultCode: Integer;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    // Remove firewall rules on uninstall
    Exec('netsh', 'advfirewall firewall delete rule name="HomeVault"',
         '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    Exec('netsh', 'advfirewall firewall delete rule name="HomeVault-Flask"',
         '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    Exec('netsh', 'advfirewall firewall delete rule name="HomeVault-Nginx"',
         '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  end;
end;
