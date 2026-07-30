# -*- coding: utf-8 -*-
"""文件系统浏览API: 目录选择对话框用(参考qBittorrent WebUI)."""
import os
from fastapi import APIRouter

router = APIRouter(prefix='/api/fs', tags=['fs'])

PROJ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@router.get('/browse')
def browse(path: str = ''):
    """浏览服务器目录. 只列子目录(下载目标用, 不列文件).

    path为空: Windows列盘符 / Linux列根目录.
    """
    if not path:
        if os.name == 'nt':
            import string
            drives = [f'{d}:\\' for d in string.ascii_uppercase if os.path.exists(f'{d}:\\')]
            return {'ok': True, 'path': '', 'parent': '', 'dirs': drives, 'home': PROJ}
        path = '/'

    path = os.path.abspath(path)
    if not os.path.isdir(path):
        return {'ok': False, 'error': f'目录不存在: {path}'}

    parent = os.path.dirname(path)
    if parent == path:
        parent = ''  # 已在根

    try:
        dirs = sorted(
            e.name for e in os.scandir(path)
            if e.is_dir() and not e.name.startswith('.') and e.name not in ('node_modules', '__pycache__', '$Recycle.Bin', 'System Volume Information')
        )
    except PermissionError:
        return {'ok': False, 'error': f'无权限访问: {path}'}

    return {'ok': True, 'path': path, 'parent': parent, 'dirs': dirs, 'home': PROJ}


@router.get('/default')
def default_dir():
    """默认下载目录(项目下 downloads)."""
    d = os.path.join(PROJ, 'downloads')
    return {'ok': True, 'path': d}
