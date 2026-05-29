; HomeVault installer script
; Compile this to create HomeVault_Setup.exe

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
; Built launcher folder from PyInstaller
Source: "dist\HomeVault\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Python helper used during install
Source: "setup_helper.py"; DestDir: "{app}"; Flags: ignoreversion

; IP watcher is kept in the app folder too
Source: "ip_watcher.py"; DestDir: "{app}"; Flags: ignoreversion

; Local installer files for Python, Bonjour, and Nginx
Source: "installer_assets\*"; DestDir: "{app}\installer_assets"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
; Make the folders the app expects
Name: "{app}\storage\Photos"
Name: "{app}\storage\Videos"
Name: "{app}\storage\Documents"
Name: "{app}\storage\Others"
Name: "{app}\static\thumbnails"

[Icons]
; Start Menu shortcuts
Name: "{group}\HomeVault"; Filename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall HomeVault"; Filename: "{uninstallexe}"

; Optional desktop shortcut
Name: "{autodesktop}\HomeVault"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Registry]
; Start with Windows only if the user selects it
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "HomeVault"; ValueData: """{app}\{#AppExeName}"""; Flags: uninsdeletevalue; Tasks: startupentry

[Run]
; Install a temporary Python runtime for setup_helper.py.
Filename: "{app}\installer_assets\python-installer.exe"; \
  Parameters: "/quiet InstallAllUsers=0 PrependPath=0 Include_test=0 TargetDir=""{tmp}\HomeVaultPython"""; \
  StatusMsg: "Installing setup runtime..."; \
  Flags: runhidden waituntilterminated; \
  Check: not SetupPythonExists

; Run setup helper with that temporary runtime.
Filename: "{tmp}\HomeVaultPython\python.exe"; \
  Parameters: """{app}\setup_helper.py"" --install-dir ""{app}"""; \
  WorkingDir: "{app}"; \
  StatusMsg: "Configuring HomeVault..."; \
  Flags: runhidden waituntilterminated; \
  Check: SetupPythonExists

; Fallback for developer machines where Python already works.
Filename: "python"; \
  Parameters: """{app}\setup_helper.py"" --install-dir ""{app}"""; \
  WorkingDir: "{app}"; \
  StatusMsg: "Setting up HomeVault..."; \
  Flags: runhidden waituntilterminated; \
  Check: not SetupPythonExists

; Optional launch after setup finishes
Filename: "{app}\{#AppExeName}"; \
  Description: "Launch HomeVault now"; \
  Flags: nowait postinstall skipifsilent

[UninstallRun]
; Stop running app processes before uninstall
Filename: "taskkill"; Parameters: "/F /IM HomeVault.exe"; Flags: runhidden; RunOnceId: "KillHomeVault"
Filename: "taskkill"; Parameters: "/F /IM nginx.exe"; Flags: runhidden; RunOnceId: "KillNginx"

[UninstallDelete]
; Remove files created after installation
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
    // Remove HomeVault firewall rules on uninstall
    Exec('netsh', 'advfirewall firewall delete rule name="HomeVault"',
         '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    Exec('netsh', 'advfirewall firewall delete rule name="HomeVault-Flask"',
         '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    Exec('netsh', 'advfirewall firewall delete rule name="HomeVault-Nginx"',
         '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  end;
end;
