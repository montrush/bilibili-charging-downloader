# -*- coding: utf-8 -*-
"""下载API: 选集+路径+进度."""
from fastapi import APIRouter
from pydantic import BaseModel
from .. import task_manager

router = APIRouter(prefix='/api/download', tags=['download'])


class DownloadRequest(BaseModel):
    aids: list[str]
    path: str


@router.post('')
def start_download(req: DownloadRequest):
    """启动下载任务. 返回task_id."""
    if not req.aids:
        return {'ok': False, 'error': '请至少选择一个视频'}
    task_id = task_manager.start_download(req.aids, req.path)
    return {'ok': True, 'task_id': task_id}


@router.get('/progress')
def progress(task_id: str):
    """查下载进度(前端轮询)."""
    p = task_manager.get_progress(task_id)
    if not p:
        return {'ok': False, 'error': '任务不存在'}
    return {'ok': True, 'data': p}
