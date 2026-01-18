; NormCode Canvas - Inno Setup Installer Script
; ==============================================
;
; This script creates a Windows installer for NormCode Canvas.
; Requires: Inno Setup 6.x (https://jrsoftware.org/isdl.php)
;
; Build command:
;   iscc installer.iss
;
; Output:
;   build/output/NormCodeCanvasSetup.exe

#define MyAppName "NormCode Canvas"
#define MyAppVersion "1.0.2-alpha"
#define MyAppPublisher "NormCode"
#define MyAppURL "https://github.com/normcode"
#define MyAppExeName "NormCodeCanvas.exe"

[Setup]
; Application info
AppId={{B8F3D2A1-5C4E-4F2B-9A1D-3E2C1F0A9B8D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Installation paths
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; Output settings
OutputDir=output
OutputBaseFilename=NormCodeCanvasSetup-{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes

; UI settings
WizardStyle=modern
SetupIconFile=resources\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

; Privileges
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; Architecture
ArchitecturesInstallIn64BitMode=x64compatible

; License (optional - uncomment if you have a license file)
; LicenseFile=..\LICENSE

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Main application files
Source: "dist\NormCodeCanvas\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Settings example
Source: "dist\NormCodeCanvas\settings.yaml.example"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

; Desktop icon (optional task)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

; Quick Launch (legacy Windows)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
; Offer to run after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up any generated files on uninstall
Type: files; Name: "{app}\settings.yaml"
Type: dirifempty; Name: "{app}"

[Code]
// Custom code for additional functionality

function InitializeSetup(): Boolean;
begin
  Result := True;
  // Add any custom initialization here
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Copy settings.yaml.example to settings.yaml if it doesn't exist
    if not FileExists(ExpandConstant('{app}\settings.yaml')) then
    begin
      if FileExists(ExpandConstant('{app}\settings.yaml.example')) then
      begin
        FileCopy(ExpandConstant('{app}\settings.yaml.example'), 
                 ExpandConstant('{app}\settings.yaml'), False);
      end;
    end;
  end;
end;

