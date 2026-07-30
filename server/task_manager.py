# -*- coding: utf-8 -*-
"""下载任务管理 - 后台线程执行, 内存状态."""
import threading, uuid, time
from .services import bili_auth, bili_dl

_tasks = {}  # task_id -> {status, total, done, failed, current, aids, path}
_lock = threading.Lock()


def start_download(aids, download_dir):
    """启动下载任务. 返回 task_id."""
    task_id = str(uuid.uuid4())[:8]
    with _lock:
        _tasks[task_id] = {
            'task_id': task_id,
            'status': 'running',
            'total': len(aids),
            'done': 0,
            'failed': [],
            'current': '',
            'aids': aids,
            'path': download_dir,
            'start_time': time.time(),
        }
    t = threading.Thread(target=_run_download, args=(task_id, aids, download_dir), daemon=True)
    t.start()
    return task_id


def _run_download(task_id, aids, download_dir):
    cookie = bili_auth.get_cookie_str()
    for aid in aids:
        with _lock:
            _tasks[task_id]['current'] = aid
        ok, err = bili_dl.download_one(aid, download_dir, cookie)
        with _lock:
            if ok:
                _tasks[task_id]['done'] += 1
            else:
                _tasks[task_id]['failed'].append({'aid': aid, 'error': err})
                _tasks[task_id]['done'] += 1
    with _lock:
        _tasks[task_id]['status'] = 'done'
        _tasks[task_id]['current'] = ''


def get_progress(task_id):
    """查任务进度."""
    with _lock:
        t = _tasks.get(task_id)
        if not t:
            return None
        return dict(t)
