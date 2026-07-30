# -*- coding: utf-8 -*-
"""安装包 exe 入口: 设置环境 -> 启动 uvicorn -> 自动开浏览器.
PyInstaller 冻结后 sys._MEIPASS 是运行时解包目录, BBDown/ffmpeg/web_dist 都在里面.
"""
import os
import sys
import threading
import webbrowser
from pathlib import Path


def _base() -> Path:
    # PyInstaller onedir: 资源在 exe 同级 _internal (6.x) 或 _MEIPASS
    if getattr(sys, 'frozen', False):
        exe_dir = Path(sys.executable).resolve().parent
        internal = exe_dir / '_internal'
        return internal if internal.is_dir() else exe_dir
    return Path(__file__).resolve().parent


def main():
    base = _base()

    # 内置前端构建产物
    os.environ.setdefault('BILI_WEB_DIST', str(base / 'web_dist'))

    # 配置目录 (cookie/登录态): 不污染安装目录
    if os.name == 'nt':
        cfg = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local')) / 'BiliDownloader'
    else:
        cfg = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')) / 'bili-downloader'
    cfg.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault('BILI_CONFIG_DIR', str(cfg))

    # 默认下载目录
    dl = Path.home() / 'Downloads' / 'bili-downloader'
    dl.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault('BILI_DOWNLOAD_DIR', str(dl))

    # 内置 BBDown / ffmpeg 加入 PATH (find_bbdown 会搜 PATH)
    os.environ['PATH'] = str(base) + os.pathsep + os.environ.get('PATH', '')

    port = int(os.environ.get('BILI_PORT', '8000'))
    print('=' * 50)
    print('  B站充电视频下载器')
    print(f'  浏览器访问: http://127.0.0.1:{port}')
    print(f'  配置目录: {cfg}')
    print(f'  下载目录: {dl}')
    print('  关闭本窗口即停止服务')
    print('=' * 50)
    threading.Timer(1.5, lambda: webbrowser.open(f'http://127.0.0.1:{port}')).start()

    import uvicorn
    uvicorn.run('server.main:app', host='127.0.0.1', port=port, log_level='warning')


if __name__ == '__main__':
    main()
