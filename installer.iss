[Setup]
AppName=PyPub
AppVersion=0.0.1
AppPublisher=Pablo Murad
AppPublisherURL=mailto:pmurad@disroot.org
DefaultDirName={autopf}\PyPub
DisableProgramGroupPage=yes
OutputBaseFilename=PyPub-Setup-0.0.1
Compression=lzma
SolidCompression=yes
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\PyPub\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\PyPub"; Filename: "{app}\PyPub.exe"
Name: "{autodesktop}\PyPub"; Filename: "{app}\PyPub.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\PyPub.exe"; Description: "{cm:LaunchProgram,PyPub}"; Flags: nowait postinstall skipifsilent
