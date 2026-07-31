# -*- coding: utf-8 -*-
"""下载任务管理 - 后台线程执行; 暂停/继续; 目录内状态文件实现断点续传.

断点续传设计:
- 每个下载任务在目标目录维护 `.bili_dl_task.json` (原子写入: tmp+replace)
- 记录: 全部aid列表 / 已完成done / 失败failed / 更新时间
- 暂停 = 杀当前BBDown子进程 + 状态落盘; 继续 = 内存任务接着pending跑
- 应用退出/断网后: 用户对相同链接+相同目录再次发起下载, start_download读到
  状态文件 -> 跳过done里的aid, 自动重试failed, 只下剩下的 -> 续传完成
- 全部成功才删除状态文件; 有失败则保留供下次重试
"""
import json
import os
import threading
import time
import uuid

from .services import bili_auth, bili_dl

_tasks = {}  # task_id -> task dict
_lock = threading.Lock()

STATE_FILENAME = '.bili_dl_task.json'


# ---------- 状态文件 ----------

def _state_path(download_dir):
    return os.path.join(download_dir, STATE_FILENAME)


def load_state(download_dir):
    """读目录里的续传状态文件, 没有/损坏返回None."""
    try:
        with open(_state_path(download_dir), encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def _save_state(download_dir, state):
    state['updated_at'] = time.time()
    tmp = _state_path(download_dir) + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=1)
    os.replace(tmp, _state_path(download_dir))


def _clear_state(download_dir):
    try:
        os.remove(_state_path(download_dir))
    except OSError:
        pass


# ---------- 任务生命周期 ----------

def start_download(aids, download_dir):
    """启动下载任务.

    目录里有上次未完成的状态文件 -> 自动续传: 跳过已完成的aid(failed自然会被
    重新排队, 因为它们不在done里).
    返回 {'task_id', 'resumed', 'skipped'} 或 {'all_done': True, 'skipped'}.
    """
    prev = load_state(download_dir)
    done_prev = set(prev.get('done', [])) if prev else set()

    queue = [a for a in aids if a not in done_prev]
    skipped = len(aids) - len(queue)
    if not queue:
        _clear_state(download_dir)  # 全都完成了, 清掉残留状态
        return {'all_done': True, 'skipped': skipped, 'resumed': bool(prev)}

    _save_state(download_dir, {
        'aids': list(dict.fromkeys((prev.get('aids', []) if prev else []) + list(aids))),
        'done': sorted(done_prev),
        'failed': prev.get('failed', []) if prev else [],
    })

    task_id = str(uuid.uuid4())[:8]
    with _lock:
        _tasks[task_id] = {
            'task_id': task_id,
            'status': 'running',       # running / paused / done
            'total': len(aids),
            'done': skipped,           # 含续传跳过的, 进度条反映整体
            'failed': [],
            'current': '',
            'pending': list(queue),
            'pause_requested': False,
            'proc': None,
            'path': download_dir,
            'resumed': skipped > 0,
            'start_time': time.time(),
        }
    t = threading.Thread(target=_run_download, args=(task_id,), daemon=True)
    t.start()
    return {'task_id': task_id, 'resumed': skipped > 0, 'skipped': skipped}


def pause_download(task_id):
    """暂停: 打断当前视频(杀BBDown进程), 状态落盘后停在线程自然退出."""
    with _lock:
        t = _tasks.get(task_id)
        if not t:
            return {'ok': False, 'error': '任务不存在'}
        if t['status'] != 'running':
            return {'ok': False, 'error': f'任务当前状态不可暂停: {t["status"]}'}
        t['pause_requested'] = True
        proc = t.get('proc')
    if proc and proc.poll() is None:
        try:
            proc.kill()
        except Exception:
            pass
    return {'ok': True}


def resume_download(task_id):
    """继续: 内存中的paused任务接着pending列表跑."""
    with _lock:
        t = _tasks.get(task_id)
        if not t:
            return {'ok': False, 'error': '任务不存在(应用重启后请重新发起下载, 会自动续传)'}
        if t['status'] != 'paused':
            return {'ok': False, 'error': f'任务当前状态不可继续: {t["status"]}'}
        t['status'] = 'running'
        t['pause_requested'] = False
    th = threading.Thread(target=_run_download, args=(task_id,), daemon=True)
    th.start()
    return {'ok': True}


def _run_download(task_id):
    cookie = bili_auth.get_cookie_str()
    while True:
        with _lock:
            t = _tasks.get(task_id)
            if not t:
                return
            if t['pause_requested']:
                t['status'] = 'paused'
                t['current'] = ''
                t['proc'] = None
                _persist(t)
                return
            if not t['pending']:
                t['status'] = 'done'
                t['current'] = ''
                _finish(t)
                return
            aid = t['pending'][0]
            t['current'] = aid

        ok, err = bili_dl.download_one(aid, t['path'], cookie,
                                       on_proc=lambda p: _set_proc(task_id, p))

        with _lock:
            t = _tasks.get(task_id)
            if not t:
                return
            t['proc'] = None
            if t['pause_requested']:
                # 被暂停打断的当前集: 不算成功也不算失败, 放回队首下次续传
                t['status'] = 'paused'
                t['current'] = ''
                _persist(t)
                return
            t['pending'].pop(0)
            if ok:
                t['done'] += 1
                _mark_done(t, aid)
            else:
                t['failed'].append({'aid': aid, 'error': err})
                t['done'] += 1
                _mark_failed(t, aid, err)


def _set_proc(task_id, proc):
    with _lock:
        t = _tasks.get(task_id)
        if t:
            t['proc'] = proc
            # 竞态: 进程启动前pause已经来过 -> 补杀
            if t['pause_requested'] and proc.poll() is None:
                try:
                    proc.kill()
                except Exception:
                    pass


def _persist(t):
    """把内存进度写进目录状态文件(暂停/每集完成时调用)."""
    state = load_state(t['path']) or {'aids': [], 'done': [], 'failed': []}
    _save_state(t['path'], {
        'aids': state.get('aids', []),
        'done': state.get('done', []),
        'failed': [{'aid': f['aid'], 'error': f['error']} for f in t['failed']],
    })


def _mark_done(t, aid):
    state = load_state(t['path']) or {'aids': [], 'done': [], 'failed': []}
    done = set(state.get('done', []))
    done.add(aid)
    _save_state(t['path'], {
        'aids': state.get('aids', []),
        'done': sorted(done),
        'failed': [f for f in state.get('failed', []) if f.get('aid') != aid],
    })


def _mark_failed(t, aid, err):
    state = load_state(t['path']) or {'aids': [], 'done': [], 'failed': []}
    failed = [f for f in state.get('failed', []) if f.get('aid') != aid]
    failed.append({'aid': aid, 'error': err})
    _save_state(t['path'], {
        'aids': state.get('aids', []),
        'done': state.get('done', []),
        'failed': failed,
    })


def _finish(t):
    """任务结束: 全部成功删状态文件; 有失败保留供下次重试."""
    if t['failed']:
        _persist(t)
    else:
        _clear_state(t['path'])


def get_progress(task_id):
    """查任务进度(字段浅拷贝, proc不可序列化单独剔除)."""
    with _lock:
        t = _tasks.get(task_id)
        if not t:
            return None
        return {k: v for k, v in t.items() if k not in ('proc', 'pending')}
