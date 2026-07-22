[Setup]
AppName=VidCraft Media Converter
AppVersion=1.0.0
AppPublisher=VidCraft
DefaultDirName={autopf}\VidCraft Media Converter
DefaultGroupName=VidCraft Media Converter
UninstallDisplayIcon={app}\VidCraftMediaConverter.exe
Compression=lzma2/ultra64
SolidCompression=yes
OutputDir=Installer_Output
OutputBaseFilename=VidCraft_Media_Converter_Setup
SetupIconFile=app_icon.ico
ChangesAssociations=yes

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; Copies all PyInstaller output files into the installation directory
Source: "dist\VidCraftMediaConverter\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start Menu Shortcut
Name: "{autoprograms}\VidCraft Media Converter"; Filename: "{app}\VidCraftMediaConverter.exe"; WorkingDir: "{app}"; IconFilename: "{app}\VidCraftMediaConverter.exe"; IconIndex: 0

; Desktop Shortcut
Name: "{autodesktop}\VidCraft Media Converter"; Filename: "{app}\VidCraftMediaConverter.exe"; WorkingDir: "{app}"; IconFilename: "{app}\VidCraftMediaConverter.exe"; IconIndex: 0; Tasks: desktopicon

[Run]
; Option to launch app after installation finishes
Filename: "{app}\VidCraftMediaConverter.exe"; Description: "{cm:LaunchProgram,VidCraft Media Converter}"; Flags: nowait postinstall skipifsilent