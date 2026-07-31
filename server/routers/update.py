# -*- coding: utf-8 -*-
"""应用内自更新: 检查GitHub最新Release -> 下载平台对应资产 -> 外部脚本自替换并重启.

更新模式 (_mode):
- auto:   Windows安装版/便携版 + Linux tar.gz(目录可写) — 下载压缩包, 生成更新脚本,
          脚本等本进程退出后整体覆盖程序目录再拉起exe
- manual: Docker / deb(装在/opt, root所有) — 只给下载页/命令提示
- dev:    源码运行(非PyInstaller冻结) — 禁用apply
"""
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

import requests
from fastapi import APIRouter

from ..version import __version__

router = APIRouter(prefix='/api/update', tags=['update'])

REPO = 'montrush/bilibili-charging-downloader'
API_URL = f'https://api.github.com/repos/{REPO}/releases/latest'
PAGE_URL = f'https://github.com/{REPO}/releases/latest'

_state = {
    'checked_at': 0.0,
    'cache': None,
    'stage': 'idle',      # idle/downloading/applying/restarting/error
    'percent': 0,
    'error': '',
    'version': '',
}
_lock = threading.Lock()


def _parse_ver(v: str) -> tuple:
    nums = [int(x) for x in re.findall(r'\d+', v or '')][:3]
    return tuple(nums + [0] * (3 - len(nums)))


def _app_dir():
    """冻结模式返回exe所在目录(安装版/便携版的程序根目录); 源码模式None."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent
    return None


def _is_docker() -> bool:
    return os.name != 'nt' and os.path.exists('/.dockerenv')


def _mode() -> str:
    if _app_dir() is None:
        return 'dev'
    if _is_docker():
        return 'manual'
    if os.name == 'nt':
        return 'auto'
    return 'auto' if os.access(_app_dir(), os.W_OK) else 'manual'


def _pick_asset(assets, patterns):
    for pat in patterns:
        for a in assets:
            if re.search(pat, a.get('name', ''), re.I):
                return a
    return None


def _do_check(force: bool = False) -> dict:
    now = time.time()
    if not force and _state['cache'] and now - _state['checked_at'] < 600:
        return _state['cache']
    # requests默认读HTTPS_PROXY环境变量, 代理用户无需额外配置
    r = requests.get(API_URL, timeout=15, headers={'Accept': 'application/vnd.github+json'})
    r.raise_for_status()
    rel = r.json()
    latest = (rel.get('tag_name') or '').lstrip('v')
    cur = __version__.lstrip('v')
    assets = rel.get('assets') or []
    if os.name == 'nt':
        asset = _pick_asset(assets, [r'portable.*\.zip$'])
    else:
        asset = _pick_asset(assets, [r'linux-x64\.tar\.gz$'])
    res = {
        'current': cur,
        'latest': latest,
        'has_update': _parse_ver(latest) > _parse_ver(cur),
        'notes': (rel.get('body') or '')[:4000],
        'page_url': rel.get('html_url') or PAGE_URL,
        'mode': _mode(),
        'asset_name': asset.get('name') if asset else None,
        'asset_url': asset.get('browser_download_url') if asset else None,
        'asset_size': asset.get('size') if asset else 0,
    }
    _state['cache'] = res
    _state['checked_at'] = now
    return res


@router.get('/check')
def check(force: bool = False):
    try:
        return _do_check(force)
    except Exception as e:
        return {'error': str(e), 'current': __version__.lstrip('v'), 'mode': _mode(), 'page_url': PAGE_URL}


@router.get('/progress')
def progress():
    return {k: _state[k] for k in ('stage', 'percent', 'error', 'version')}


@router.post('/apply')
def apply():
    if _mode() != 'auto':
        return {'ok': False, 'error': '当前安装方式不支持自动更新, 请前往发布页手动下载'}
    with _lock:
        if _state['stage'] in ('downloading', 'applying', 'restarting'):
            return {'ok': False, 'error': '更新已在进行中'}
        _state.update(stage='downloading', percent=0, error='')
    threading.Thread(target=_apply_worker, daemon=True).start()
    return {'ok': True}


def _apply_worker():
    try:
        info = _do_check()
        if not info.get('asset_url'):
            raise RuntimeError('最新Release里找不到适用于当前平台的更新包')
        _state['version'] = info['latest']
        pkg = _download(info['asset_url'], info.get('asset_size') or 0)
        _state.update(stage='applying', percent=96)
        _spawn_updater(pkg)
        _state.update(stage='restarting', percent=100)
        time.sleep(1.5)  # 让前端先拿到restarting状态
        os._exit(0)      # 本进程退出后, 外部脚本完成覆盖并重新拉起
    except Exception as e:
        _state.update(stage='error', error=str(e), percent=0)


def _download(url: str, total: int) -> Path:
    tmp = Path(tempfile.gettempdir()) / 'bili-update-pkg'
    tmp.mkdir(parents=True, exist_ok=True)
    fn = tmp / url.rsplit('/', 1)[-1]
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        got = 0
        with open(fn, 'wb') as f:
            for chunk in r.iter_content(1 << 20):
                if not chunk:
                    continue
                f.write(chunk)
                got += len(chunk)
                if total:
                    _state['percent'] = min(95, int(got * 95 / total))
    return fn


def _spawn_updater(pkg: Path):
    """生成独立更新脚本并detach启动: 等本进程退出 -> 解压覆盖程序目录 -> 重启exe."""
    app_dir = _app_dir()
    exe = app_dir / ('BiliDownloader.exe' if os.name == 'nt' else 'bili-downloader')
    pid = os.getpid()
    tmp = Path(tempfile.gettempdir()) / 'bili-update-pkg'
    tmp.mkdir(parents=True, exist_ok=True)

    if os.name == 'nt':
        script = tmp / 'bili-updater.ps1'
        script.write_text(
            "param([int]$ProcId, [string]$Pkg, [string]$Dest, [string]$Exe)\n"
            "$ErrorActionPreference = 'Stop'\n"
            "while (Get-Process -Id $ProcId -ErrorAction SilentlyContinue) { Start-Sleep -Milliseconds 500 }\n"
            "Start-Sleep 1\n"
            "$tmp = Join-Path $env:TEMP 'bili-update-extract'\n"
            "if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }\n"
            "Expand-Archive -Path $Pkg -DestinationPath $tmp -Force\n"
            "$src = (Get-ChildItem $tmp -Directory | Select-Object -First 1).FullName\n"
            "robocopy $src $Dest /MIR /NFL /NDL /NJH /NJS /R:2 /W:1 | Out-Null\n"
            "Remove-Item $Pkg -Force -ErrorAction SilentlyContinue\n"
            "Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue\n"
            "Start-Process -FilePath $Exe\n",
            encoding='utf-8')
        # ⚠️不能用DETACHED_PROCESS: 该flag下powershell.exe静默退出不执行脚本(实测).
        # CREATE_NO_WINDOW=隐藏窗口且脚本正常执行
        subprocess.Popen(
            ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-WindowStyle', 'Hidden',
             '-File', str(script), str(pid), str(pkg), str(app_dir), str(exe)],
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000),
            close_fds=True)
    else:
        script = tmp / 'bili-updater.sh'
        script.write_text(
            "#!/bin/sh\n"
            f"while kill -0 {pid} 2>/dev/null; do sleep 0.5; done\n"
            "sleep 1\n"
            "TMPD=$(mktemp -d)\n"
            f"tar -xzf '{pkg}' -C \"$TMPD\"\n"
            f"cp -a \"$TMPD\"/bili-downloader/. '{app_dir}'/\n"
            f"chmod +x '{exe}'\n"
            f"rm -rf \"$TMPD\" '{pkg}'\n"
            f"nohup '{exe}' >/dev/null 2>&1 &\n",
            encoding='utf-8')
        subprocess.Popen(['/bin/sh', str(script)], start_new_session=True,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
