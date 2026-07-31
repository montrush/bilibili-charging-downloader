# -*- coding: utf-8 -*-
"""下载API: 并行任务队列 + 选集路径 + 进度 + 设置."""
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
    title: str = ''              # 任务显示名(合集名/视频名)
    # 目录规则 (参考qBittorrent)
    auto_mkdir: bool = True        # 目录不存在时自动创建
    mkdir_up: bool = False         # 按UP主名字建子目录
    mkdir_collection: bool = False  # 按合集名称建子目录
    up_name: str = ''
    collection_title: str = ''


@router.post('')
def start_download(req: DownloadRequest):
    """启动下载任务(进并行队列). 同目录已有未完成任务时合并续传."""
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

    title = req.title or req.collection_title
    r = task_manager.start_download(req.aids, final_dir, title=title)
    return {'ok': True, 'final_dir': final_dir, **r}


class TaskAction(BaseModel):
    task_id: str


@router.post('/pause')
def pause_download(req: TaskAction):
    """暂停任务: 打断当前视频下载, 进度持久化(注册表+目录状态文件)."""
    return task_manager.pause_download(req.task_id)


@router.post('/resume')
def resume_download(req: TaskAction):
    """继续任务: 重新进入并行队列, 有槽位即开跑."""
    return task_manager.resume_download(req.task_id)


@router.post('/delete')
def delete_task(req: TaskAction):
    """删除任务记录(运行中先停). 不删已下载的视频文件."""
    return task_manager.delete_task(req.task_id)


@router.get('/progress')
def progress(task_id: str):
    """查单个任务进度(前端轮询)."""
    p = task_manager.get_progress(task_id)
    if not p:
        return {'ok': False, 'error': '任务不存在'}
    return {'ok': True, 'data': p}


@router.get('/tasks')
def list_tasks():
    """全部任务列表(任务面板用)."""
    return {'ok': True, 'data': task_manager.list_tasks()}


@router.get('/settings')
def get_settings():
    """队列设置: max_parallel(并行任务数) / auto_resume(启动自动续接)."""
    return {'ok': True, 'data': task_manager.get_settings()}


class SettingsPatch(BaseModel):
    max_parallel: int | None = None
    auto_resume: bool | None = None


@router.put('/settings')
def put_settings(req: SettingsPatch):
    patch = {k: v for k, v in req.model_dump().items() if v is not None}
    if not patch:
        return {'ok': False, 'error': '没有要修改的设置'}
    return task_manager.update_settings(patch)
