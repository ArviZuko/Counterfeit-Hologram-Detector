; Inno Setup Script for AI-Powered Hologram Authenticity Detection System
; Packages standalone HologramAuthenticity.exe into Windows installer HologramAuthenticity_Setup.exe

#define MyAppName "AI-Powered Hologram Authenticity Detection System"
#define MyAppShortName "HologramAuthenticity"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "Security Optics & AI Research"
#define MyAppExeName "HologramAuthenticity.exe"

[Setup]
AppId={{8B5C7D29-5E1B-4E7B-A320-D42A7C3284B9}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppShortName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=dist\installer
OutputBaseFilename=HologramAuthenticity_Setup
SetupIconFile=Counterfeit-Hologram-Detector-main\SRC\icon.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
DisableProgramGroupPage=auto

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: isreadme ignoreversion
Source: "Counterfeit-Hologram-Detector-main\SRC\icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "Counterfeit-Hologram-Detector-main\SRC\icon.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "Counterfeit-Hologram-Detector-main\SRC\Template.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "nbi.bmp"; DestDir: "{app}"; Flags: ignoreversion
Source: "cropped.png"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"
Name: "{group}\Readme and Documentation"; Filename: "{app}\README.md"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
