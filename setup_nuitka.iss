[Setup]
AppName=VideoDownloader
AppVersion=1.0
DefaultDirName={autopf}\VideoDownloader
DefaultGroupName=VideoDownloader
OutputDir=Output
OutputBaseFilename=VideoDownloader_Setup
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible

[Files]
; 包含主 exe
Source: "build_nuitka\video_downloader.dist\video_downloader.exe"; DestDir: "{app}"; Flags: ignoreversion
; 包含所有依赖文件（DLLs, pyds, 等）
Source: "build_nuitka\video_downloader.dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\VideoDownloader"; Filename: "{app}\video_downloader.exe"; IconFilename: "{app}\ico\video_downloader.ico"
Name: "{commondesktop}\VideoDownloader"; Filename: "{app}\video_downloader.exe"; Tasks: desktopicon; IconFilename: "{app}\ico\video_downloader.ico"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Run]
Filename: "{app}\video_downloader.exe"; Description: "{cm:LaunchProgram,VideoDownloader}"; Flags: nowait postinstall skipifsilent
