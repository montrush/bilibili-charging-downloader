# -*- coding: utf-8 -*-
"""下载API: 选集+路径+目录规则+进度."""
import os, re
from fastapi import APIRouter
from pydantic import BaseModel
from .. import task_manager

router = APIRouter(prefix='/api/download', tags=['download'])

ILLEGAL = re.compile(r'[\\/:*?"<>|\r\n]+')


def sanitize_dir_name(name: str) -> str:
    """目录名清洗: 去掉Windows非法字符."""
    return ILLEGAL.sub('_', name).strip().strip('.')[:80]


class DownloadRequest(BaseModel):
    aids: list[str]
    path: str
    # 目录规则 (参考qBittorrent)
    auto_mkdir: bool = True        # 目录不存在时自动创建
    mkdir_up: bool = False         # 按UP主名字建子目录
    mkdir_collection: bool = False  # 按合集名称建子目录
    up_name: str = ''
    collection_title: str = ''


@router.post('')
def start_download(req: DownloadRequest):
    """启动下载任务. 返回task_id + 实际下载目录."""
    if not req.aids:
        return {'ok': False, 'error': '请至少选择一个视频'}

    # 按规则拼最终目录: path / [UP主] / [合集]
    final_dir = req.path
    if req.mkdir_up and req.up_name:
        final_dir = os.path.join(final_dir, sanitize_dir_name(req.up_name))
    if req.mkdir_collection and req.collection_title:
        final_dir = os.path.join(final_dir, sanitize_dir_name(req.collection_title))

    if not os.path.isdir(final_dir):
        if not req.auto_mkdir:
            return {'ok': False, 'error': f'目录不存在且未开启自动创建: {final_dir}'}
        try:
            os.makedirs(final_dir, exist_ok=True)
        except OSError as e:
            return {'ok': False, 'error': f'创建目录失败: {e}'}

    task_id = task_manager.start_download(req.aids, final_dir)
    return {'ok': True, 'task_id': task_id, 'final_dir': final_dir}


@router.get('/progress')
def progress(task_id: str):
    """查下载进度(前端轮询)."""
    p = task_manager.get_progress(task_id)
    if not p:
        return {'ok': False, 'error': '任务不存在'}
    return {'ok': True, 'data': p}
