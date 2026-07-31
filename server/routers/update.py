# -*- coding: utf-8 -*-
"""应用内自更新: 国内无代理用户优先走 GitHub 加速镜像, 不依赖 Gitee.

通道设计 (Gitee release 上传不稳, 改用 GitHub 国内加速源):
- 版本检查: jsDelivr CDN(读仓库version.py, 国内直连) -> GitHub API 兜底
- 下载: GitHub 加速镜像(ghfast.top/gh-proxy.com/ghproxy.net, 代理GH release) -> GitHub 直连
- 用户可在界面填自定义代理(如 127.0.0.1:7890), 检查和下载都走它

更新载荷:
- Windows = Inno Setup.exe(76MB, /DIR指定目标目录 + /VERYSILENT静默, 安装版/便携版通用)
- Linux = tar.gz(GitHub 直连 + 镜像)
- Docker/deb = manual只提示; 源码 = dev禁用

自替换流程: 后台下载 -> 生成PowerShell/sh脚本 -> 脚本等主进程退出 ->
(Win)静默安装覆盖+重启 / (Linux)解压覆盖+重启
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
from pydantic import BaseModel

from ..version import __version__

router = APIRouter(prefix='/api/update', tags=['update'])

GH_REPO = 'montrush/bilibili-charging-downloader'
GH_API = f'https://api.github.com/repos/{GH_REPO}/releases/latest'
JSD_URL = f'https://cdn.jsdelivr.net/gh/{GH_REPO}@master/server/version.py'
GH_PAGE = f'https://github.com/{GH_REPO}/releases/latest'
# 公共GitHub加速镜像(第三方, 可能失效, 轮询尝试; 前缀+完整github URL). 国内直连主力.
GH_MIRRORS = ['https://ghfast.top/', 'https://gh-proxy.com/', 'https://ghproxy.net/']

_state = {
    'cache': None,
    'checked_at': 0.0,
    'meta_channel': None,    # 上次检查成功的通道, 下次优先用它
    'stage': 'idle',         # idle/downloading/applying/restarting/error
    'percent': 0,
    'error': '',
    'version': '',
    'channel': '',           # 当前下载所用通道(展示给用户)
}
_lock = threading.Lock()


def _parse_ver(v: str) -> tuple:
    nums = [int(x) for x in re.findall(r'\d+', v or '')][:3]
    return tuple(nums + [0] * (3 - len(nums)))


def _proxies(proxy: str):
    if not proxy:
        return None
    p = proxy if '://' in proxy else f'http://{proxy}'
    return {'http': p, 'https': p}


def _app_dir():
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


def _asset_name(ver: str) -> str:
    if os.name == 'nt':
        return f'BiliDownloader-Setup-{ver}-win-x64.exe'
    return f'bili-downloader_{ver}_linux-x64.tar.gz'


def _asset_pat() -> str:
    return r'Setup-.*\.exe$' if os.name == 'nt' else r'linux-x64\.tar\.gz$'


def _norm_meta(rel: dict) -> dict:
    """GitHub release JSON 取字段."""
    latest = (rel.get('tag_name') or '').lstrip('v')
    assets = [a for a in (rel.get('assets') or []) if re.search(_asset_pat(), a.get('name', ''), re.I)]
    a = assets[0] if assets else {}
    return {
        'channel': 'github',
        'latest': latest,
        'notes': (rel.get('body') or '')[:4000],
        'page_url': rel.get('html_url') or GH_PAGE,
        'asset_name': a.get('name') or _asset_name(latest),
        'asset_url': a.get('browser_download_url'),
        'asset_size': a.get('size') or 0,
    }


def _fetch_meta(proxy: str) -> dict:
    r = requests.get(GH_API, timeout=10, proxies=_proxies(proxy),
                     headers={'Accept': 'application/vnd.github+json'})
    r.raise_for_status()
    return _norm_meta(r.json())


def _fetch_meta_jsd(proxy: str) -> dict:
    """jsDelivr优先通道: 读仓库version.py拿版本号(国内CDN直连), 无notes, 下载URL按规则构造."""
    r = requests.get(JSD_URL, timeout=10, proxies=_proxies(proxy))
    r.raise_for_status()
    m = re.search(r"__version__\s*=\s*'([\d.]+)'", r.text)
    if not m:
        raise RuntimeError('jsDelivr版本文件解析失败')
    ver = m.group(1)
    return {
        'channel': 'jsdelivr',
        'latest': ver,
        'notes': '',
        'page_url': GH_PAGE,
        'asset_name': _asset_name(ver),
        'asset_url': None,
        'asset_size': 0,
    }


def _do_check(proxy: str = '', force: bool = False) -> dict:
    now = time.time()
    if not force and _state['cache'] and now - _state['checked_at'] < 600:
        return _state['cache']
    # jsDelivr(CDN读version.py, 国内直连)优先 -> GitHub API兜底; 不依赖Gitee
    meta = None
    errors = []
    for ch, fn in [('jsdelivr', lambda: _fetch_meta_jsd(proxy)),
                   ('github', lambda: _fetch_meta(proxy))]:
        try:
            meta = fn()
            _state['meta_channel'] = ch
            break
        except Exception as e:
            errors.append(f'{ch}: {e}')
    if meta is None:
        raise RuntimeError('所有更新通道都不通(' + '; '.join(errors) + ')')
    cur = __version__.lstrip('v')
    res = {
        **meta,
        'current': cur,
        'has_update': _parse_ver(meta['latest']) > _parse_ver(cur),
        'mode': _mode(),
    }
    _state['cache'] = res
    _state['checked_at'] = now
    return res


@router.get('/check')
def check(force: bool = False, proxy: str = ''):
    try:
        return _do_check(proxy, force)
    except Exception as e:
        return {'error': str(e), 'current': __version__.lstrip('v'), 'mode': _mode(), 'page_url': GH_PAGE}


@router.get('/progress')
def progress():
    return {k: _state[k] for k in ('stage', 'percent', 'error', 'version', 'channel')}


class ApplyReq(BaseModel):
    proxy: str = ''


@router.post('/apply')
def apply(req: ApplyReq = ApplyReq()):
    if _mode() != 'auto':
        return {'ok': False, 'error': '当前安装方式不支持自动更新, 请前往发布页手动下载'}
    with _lock:
        if _state['stage'] in ('downloading', 'applying', 'restarting'):
            return {'ok': False, 'error': '更新已在进行中'}
        _state.update(stage='downloading', percent=0, error='')
    threading.Thread(target=_apply_worker, args=(req.proxy,), daemon=True).start()
    return {'ok': True}


def _apply_worker(proxy: str):
    try:
        info = _do_check(proxy)
        ver = info['latest']
        _state['version'] = ver
        pkg = _download_multi(info, proxy)
        _state.update(stage='applying', percent=96)
        _spawn_updater(pkg)
        _state.update(stage='restarting', percent=100)
        time.sleep(1.5)  # 让前端先拿到restarting状态
        os._exit(0)      # 本进程退出后, 外部脚本完成安装并重新拉起
    except Exception as e:
        _state.update(stage='error', error=str(e), percent=0)


def _download_candidates(info: dict) -> list:
    """下载URL候选: GitHub加速镜像(国内直连) -> GitHub直连; 不依赖Gitee(上传不稳常缺包)."""
    ver, name = info['latest'], info['asset_name']
    gh = f'https://github.com/{GH_REPO}/releases/download/v{ver}/{name}'
    urls = [m + gh for m in GH_MIRRORS]   # 国内加速镜像优先(代理GH release, GH有包即可下)
    if info.get('asset_url'):
        urls.append(info['asset_url'])     # GitHub API带回的直链(与镜像去重)
    urls.append(gh)                        # GitHub直连兜底
    seen, out = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def _channel_of(url: str) -> str:
    if url.startswith(tuple(GH_MIRRORS)):
        return '加速镜像'
    return 'GitHub'


def _download_multi(info: dict, proxy: str) -> Path:
    tmp = Path(tempfile.gettempdir()) / 'bili-update-pkg'
    tmp.mkdir(parents=True, exist_ok=True)
    fn = tmp / info['asset_name']
    errors = []
    for url in _download_candidates(info):
        ch = _channel_of(url)
        try:
            _state['channel'] = ch
            with requests.get(url, stream=True, timeout=(10, 30), proxies=_proxies(proxy)) as r:
                r.raise_for_status()
                total = info.get('asset_size') or int(r.headers.get('Content-Length') or 0)
                got = 0
                with open(fn, 'wb') as f:
                    for chunk in r.iter_content(1 << 20):
                        if not chunk:
                            continue
                        f.write(chunk)
                        got += len(chunk)
                        if total:
                            _state['percent'] = min(95, int(got * 95 / total))
            # 大小校验(meta有size时): 防镜像返回截断/篡改的包
            if info.get('asset_size') and fn.stat().st_size != info['asset_size']:
                raise RuntimeError(f'文件大小不符({fn.stat().st_size} != {info["asset_size"]})')
            return fn
        except Exception as e:
            errors.append(f'{ch}: {e}')
            _state['percent'] = 0
            continue
    raise RuntimeError('所有下载通道都失败(' + '; '.join(errors) + ')')


def _spawn_updater(pkg: Path):
    """生成独立更新脚本并隐藏窗口启动: 等本进程退出 -> 静默安装/覆盖 -> 重启exe."""
    app_dir = _app_dir()
    exe = app_dir / ('BiliDownloader.exe' if os.name == 'nt' else 'bili-downloader')
    pid = os.getpid()
    tmp = Path(tempfile.gettempdir()) / 'bili-update-pkg'
    tmp.mkdir(parents=True, exist_ok=True)

    if os.name == 'nt':
        # Inno静默安装到/DIR(安装版=原安装目录, 便携版=当前目录), 装完拉起
        script = tmp / 'bili-updater.ps1'
        script.write_text(
            "param([int]$ProcId, [string]$Pkg, [string]$Dest, [string]$Exe)\n"
            "$ErrorActionPreference = 'Stop'\n"
            "while (Get-Process -Id $ProcId -ErrorAction SilentlyContinue) { Start-Sleep -Milliseconds 500 }\n"
            "Start-Sleep 1\n"
            "Start-Process -FilePath $Pkg -ArgumentList '/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',\"/DIR=$Dest\" -Wait\n"
            "Remove-Item $Pkg -Force -ErrorAction SilentlyContinue\n"
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
