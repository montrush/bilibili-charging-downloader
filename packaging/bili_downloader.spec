# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec: B站下载器 onedir 打包 (Windows/Linux 共用).
用法(仓库根目录): pyinstaller packaging/bili_downloader.spec --noconfirm
前置: web/dist 已构建; vendor/ 下有 BBDown(.exe) 和 ffmpeg(.exe).
"""
import os
from PyInstaller.utils.hooks import collect_submodules

ROOT = os.path.abspath(os.getcwd())
IS_WIN = os.name == 'nt'
BIN_NAME = os.environ.get('APP_BIN_NAME', 'BiliDownloader' if IS_WIN else 'bili-downloader')

datas = [
    (os.path.join(ROOT, 'web', 'dist'), 'web_dist'),
    (os.path.join(ROOT, 'LICENSE'), '.'),
    (os.path.join(ROOT, 'THIRD_PARTY_NOTICES.md'), '.'),
]

# vendor/ 里的第三方二进制 (CI下载): BBDown + ffmpeg
binaries = []
for name in ('BBDown.exe', 'ffmpeg.exe', 'ffprobe.exe', 'BBDown', 'ffmpeg', 'ffprobe'):
    p = os.path.join(ROOT, 'vendor', name)
    if os.path.exists(p):
        binaries.append((p, '.'))

hiddenimports = (
    collect_submodules('uvicorn')
    + collect_submodules('server')
    + ['qrcode', 'qrcode.image.pil', 'PIL.Image', 'multipart']
)

a = Analysis(
    [os.path.join(ROOT, 'packaging', 'launcher.py')],
    pathex=[ROOT],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'pandas', 'torch'],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=BIN_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='BiliDownloader' if IS_WIN else 'bili-downloader',
)
