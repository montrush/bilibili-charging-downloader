; B站充电视频下载器 - Inno Setup 安装脚本
; CI用法: iscc packaging/windows/setup.iss /DAppVersion=1.0.0
#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif

[Setup]
AppName=B站充电视频下载器
AppVersion={#AppVersion}
AppPublisher=侯plus
AppPublisherURL=https://github.com/montrush/bilibili-charging-downloader
DefaultDirName={autopf}\BiliDownloader
DefaultGroupName=B站充电视频下载器
OutputDir=dist\installer
OutputBaseFilename=BiliDownloader-Setup-{#AppVersion}-win-x64
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
WizardStyle=modern

[Files]
Source: "dist\BiliDownloader\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\B站充电视频下载器"; Filename: "{app}\BiliDownloader.exe"
Name: "{group}\卸载 B站充电视频下载器"; Filename: "{uninstallexe}"
Name: "{autodesktop}\B站充电视频下载器"; Filename: "{app}\BiliDownloader.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加任务:"

[Run]
Filename: "{app}\BiliDownloader.exe"; Description: "立即启动"; Flags: postinstall nowait skipifsilent unchecked
