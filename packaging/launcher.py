# -*- coding: utf-8 -*-
"""安装包 exe 入口: 设置环境 -> 启动 uvicorn -> 自动开浏览器.
PyInstaller 冻结后 sys._MEIPASS 是运行时解包目录, BBDown/ffmpeg/web_dist 都在里面.
"""
import os
import socket
import sys
import threading
import webbrowser
from pathlib import Path

# GitHub runner等英文环境是cp1252, 中文print会UnicodeEncodeError崩进程;
# 但不能强转utf-8(中文Windows控制台是GBK, utf-8字节反而乱码) —— 保留原生编码, 只把编不了的字符替换掉
try:
    sys.stdout.reconfigure(errors='replace')
    sys.stderr.reconfigure(errors='replace')
except Exception:
    pass


def _base() -> Path:
    # PyInstaller onedir: 资源在 exe 同级 _internal (6.x) 或 _MEIPASS
    if getattr(sys, 'frozen', False):
        exe_dir = Path(sys.executable).resolve().parent
        internal = exe_dir / '_internal'
        return internal if internal.is_dir() else exe_dir
    return Path(__file__).resolve().parent


def _port_free(port: int) -> bool:
    # 不设SO_REUSEADDR: Windows下它会放行已占用端口, 失去检测意义
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', port))
            return True
        except OSError:
            return False


def _choose_port(default: int = 8000) -> int:
    """启动前选端口: BILI_PORT环境变量 > 用户输入 > 默认8000. 无控制台(Docker等)直接用默认."""
    env = os.environ.get('BILI_PORT', '').strip()
    if env.isdigit():
        return int(env)
    if not sys.stdin or not sys.stdin.isatty():
        return default
    print('  提示: 界面通过浏览器访问, 需要选一个本地端口')
    while True:
        try:
            s = input(f'  请输入端口 [{default}] (直接回车用 {default}): ').strip()
        except EOFError:
            print()
            return default
        if not s:
            if _port_free(default):
                return default
            print(f'  ⚠ {default} 端口已被占用, 请换一个')
            continue
        if not s.isdigit() or not 1 <= int(s) <= 65535:
            print('  ⚠ 请输入 1-65535 之间的数字')
            continue
        p = int(s)
        if not _port_free(p):
            print(f'  ⚠ {p} 端口已被占用, 请换一个')
            continue
        return p


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

    port = _choose_port(8000)
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
