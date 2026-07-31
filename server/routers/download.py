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

    r = task_manager.start_download(req.aids, final_dir)
    if r.get('all_done'):
        return {'ok': True, 'all_done': True, 'skipped': r['skipped'], 'final_dir': final_dir,
                'msg': f'所选 {r["skipped"]} 个视频此前已全部下载完成'}
    return {'ok': True, 'task_id': r['task_id'], 'final_dir': final_dir,
            'resumed': r['resumed'], 'skipped': r['skipped']}


class TaskAction(BaseModel):
    task_id: str


@router.post('/pause')
def pause_download(req: TaskAction):
    """暂停任务: 打断当前视频下载, 进度写入目录里的续传状态文件."""
    return task_manager.pause_download(req.task_id)


@router.post('/resume')
def resume_download(req: TaskAction):
    """继续任务(仅本次运行内暂停的任务; 应用重启后直接重新发起下载即自动续传)."""
    return task_manager.resume_download(req.task_id)


@router.get('/progress')
def progress(task_id: str):
    """查下载进度(前端轮询)."""
    p = task_manager.get_progress(task_id)
    if not p:
        return {'ok': False, 'error': '任务不存在'}
    return {'ok': True, 'data': p}
