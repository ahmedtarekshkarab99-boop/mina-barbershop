; Inno Setup Script for "Mina Al Arabi Salon Manager"
; Requires Inno Setup (https://jrsoftware.org/isinfo.php) installed and `iscc` available in PATH.

[Setup]
AppName=مدير صالون مينا العربي
AppVersion=1.0.0
AppPublisher=Mina Al Arabi
DefaultDirName={pf}\MinaAlArabiSalonManager
DefaultGroupName=مدير صالون مينا العربي
OutputDir=installer\windows\output
OutputBaseFilename=MinaAlArabiSalonManagerSetup
Compression=lzma
SolidCompression=yes
DisableDirPage=no
DisableProgramGroupPage=no
ArchitecturesInstallIn64BitMode=x64
UsePreviousLanguage=no

[Languages]
Name: "arabic"; MessagesFile: "compiler:Languages\Arabic.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; Include all files created by PyInstaller
Source: "dist\MinaAlArabiSalonManager\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Always create Start Menu and Desktop shortcuts with app name
Name: "{group}\مدير صالون مينا العربي"; Filename: "{app}\MinaAlArabiSalonManager.exe"
Name: "{commondesktop}\مدير صالون مينا العربي"; Filename: "{app}\MinaAlArabiSalonManager.exe"

[Run]
Filename: "{app}\MinaAlArabiSalonManager.exe"; Description: "تشغيل التطبيق"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Optionally clean generated data folders on uninstall (comment out if you want to keep user data)
Type: filesandordirs; Name: "{app}\data"