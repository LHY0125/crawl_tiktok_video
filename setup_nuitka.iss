[Setup]
AppName=DouyinDownloader
AppVersion=1.0
DefaultDirName={autopf}\DouyinDownloader
DefaultGroupName=DouyinDownloader
OutputDir=Output
OutputBaseFilename=DouyinDownloader_Setup
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible

[Files]
; 包含主 exe
Source: "build_nuitka_v6_with_icon\爬取抖音视频.dist\爬取抖音视频.exe"; DestDir: "{app}"; Flags: ignoreversion
; 包含所有依赖文件（DLLs, pyds, 等）
Source: "build_nuitka_v6_with_icon\爬取抖音视频.dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\DouyinDownloader"; Filename: "{app}\爬取抖音视频.exe"; IconFilename: "{app}\ico\爬取抖音视频.ico"
Name: "{commondesktop}\DouyinDownloader"; Filename: "{app}\爬取抖音视频.exe"; Tasks: desktopicon; IconFilename: "{app}\ico\爬取抖音视频.ico"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Run]
Filename: "{app}\爬取抖音视频.exe"; Description: "{cm:LaunchProgram,DouyinDownloader}"; Flags: nowait postinstall skipifsilent
