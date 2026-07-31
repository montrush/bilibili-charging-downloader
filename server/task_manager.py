# -*- coding: utf-8 -*-
"""下载任务管理 - 并行任务队列 + 持久化注册表 + 暂停/继续 + 启动续接.

架构:
- 全局注册表 download_tasks.json (存配置目录): 所有任务的持久化状态
  {task_id, title, path, aids, done, failed, status, current, created_at, updated_at}
  status: queued(排队等槽位) / running / paused / done
- 调度器: running任务数 < max_parallel 时从queued拉起新worker线程
- 每个下载目录同时写 .bili_dl_task.json (v1.0.4起的目录级续传文件, 便携备份)
- 启动恢复 (init_on_startup): 上次running/queued的任务标记为paused;
  设置开启auto_resume时自动全部重新排队开跑
- 同目录去重: 对相同下载目录再发起 -> 合并进已有未完成任务, 不建重复任务
"""
import json
import os
import threading
import time
import uuid

from .services import bili_auth, bili_dl

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.environ.get('BILI_CONFIG_DIR', PROJ)

REGISTRY_FILE = os.path.join(CONFIG_DIR, 'download_tasks.json')
SETTINGS_FILE = os.path.join(CONFIG_DIR, 'download_settings.json')
DIR_STATE_FILENAME = '.bili_dl_task.json'

_lock = threading.RLock()
_registry = {'tasks': []}            # 持久化: 所有任务
_runtime = {}                        # 内存: task_id -> {pause_requested, proc}
_settings = {'max_parallel': 2, 'auto_resume': False}


# ---------- 持久化 ----------

def _load_json(path, default):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default


def _save_json(path, data):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def _save_registry():
    _save_json(REGISTRY_FILE, _registry)


def _save_settings():
    _save_json(SETTINGS_FILE, _settings)


def _dir_state_path(download_dir):
    return os.path.join(download_dir, DIR_STATE_FILENAME)


def _write_dir_state(task):
    """目录级续传文件(与注册表同源, 用户搬动下载目录也能看出没下完)."""
    try:
        _save_json(_dir_state_path(task['path']), {
            'title': task.get('title', ''),
            'aids': task['aids'],
            'done': task['done'],
            'failed': task['failed'],
        })
    except Exception:
        pass


def _clear_dir_state(download_dir):
    try:
        os.remove(_dir_state_path(download_dir))
    except OSError:
        pass


# ---------- 查询 ----------

def _find(task_id):
    for t in _registry['tasks']:
        if t['task_id'] == task_id:
            return t
    return None


def get_progress(task_id):
    with _lock:
        t = _find(task_id)
        if not t:
            return None
        return _public(t)


def list_tasks():
    """全部任务(新的在前)."""
    with _lock:
        return [_public(t) for t in reversed(_registry['tasks'])]


def _public(t):
    failed_n = len(t['failed'])
    return {
        'task_id': t['task_id'],
        'title': t.get('title', ''),
        'path': t['path'],
        'status': t['status'],
        'total': len(t['aids']),
        'done': len(t['done']) + failed_n,
        'success': len(t['done']),
        'failed': t['failed'],
        'current': t.get('current', ''),
        'created_at': t.get('created_at', 0),
        'updated_at': t.get('updated_at', 0),
    }


def get_settings():
    with _lock:
        return dict(_settings)


def update_settings(patch):
    with _lock:
        if 'max_parallel' in patch:
            _settings['max_parallel'] = max(1, min(5, int(patch['max_parallel'])))
        if 'auto_resume' in patch:
            _settings['auto_resume'] = bool(patch['auto_resume'])
        _save_settings()
    _maybe_schedule()  # 调大并行数后立即补位
    return {'ok': True, **_settings}


# ---------- 调度器 ----------

def _maybe_schedule():
    """有空闲并行槽位时拉起queued任务."""
    with _lock:
        active = sum(1 for t in _registry['tasks'] if t['status'] == 'running')
        for t in _registry['tasks']:
            if active >= _settings['max_parallel']:
                break
            if t['status'] == 'queued':
                t['status'] = 'running'
                t['updated_at'] = time.time()
                _runtime[t['task_id']] = {'pause_requested': False, 'proc': None}
                threading.Thread(target=_worker, args=(t['task_id'],), daemon=True).start()
                active += 1
        _save_registry()


# ---------- 任务操作 ----------

def start_download(aids, download_dir, title=''):
    """启动任务. 同目录有未完成任务 -> 合并续传; 否则新建并排队."""
    with _lock:
        for t in _registry['tasks']:
            if t['path'] == download_dir and t['status'] in ('running', 'queued', 'paused'):
                known = set(t['aids'])
                t['aids'] += [a for a in aids if a not in known]
                t['updated_at'] = time.time()
                _save_registry()
                _write_dir_state(t)
                return {'task_id': t['task_id'], 'existing': True, 'status': t['status'],
                        'title': t.get('title', '')}

        # v1.0.4遗留的目录级状态文件 -> 导入为已完成记录
        done_prev, failed_prev = [], []
        prev = _load_json(_dir_state_path(download_dir), None)
        if prev:
            done_prev = [a for a in prev.get('done', []) if a in aids]
            failed_prev = [f for f in prev.get('failed', []) if f.get('aid') in aids]
            _clear_dir_state(download_dir)

        task = {
            'task_id': str(uuid.uuid4())[:8],
            'title': title or (prev or {}).get('title', '') or '下载任务',
            'path': download_dir,
            'aids': list(aids),
            'done': [a for a in done_prev],
            'failed': failed_prev,
            'status': 'queued',
            'current': '',
            'created_at': time.time(),
            'updated_at': time.time(),
        }
        _registry['tasks'].append(task)
        _save_registry()
        _write_dir_state(task)
    _maybe_schedule()
    return {'task_id': task['task_id'], 'existing': False, 'status': task['status'],
            'resumed': bool(done_prev or failed_prev), 'skipped': len(done_prev),
            'title': task['title']}


def pause_download(task_id):
    """暂停: running杀进程打断; queued直接标记."""
    with _lock:
        t = _find(task_id)
        if not t:
            return {'ok': False, 'error': '任务不存在'}
        if t['status'] == 'queued':
            t['status'] = 'paused'
            t['updated_at'] = time.time()
            _save_registry()
            return {'ok': True}
        if t['status'] != 'running':
            return {'ok': False, 'error': f'任务当前状态不可暂停: {t["status"]}'}
        rt = _runtime.get(task_id)
        if rt:
            rt['pause_requested'] = True
            proc = rt.get('proc')
        else:
            proc = None
    if proc and proc.poll() is None:
        try:
            proc.kill()
        except Exception:
            pass
    return {'ok': True}


def resume_download(task_id):
    """继续: 重新排队, 调度器分配槽位后开跑."""
    with _lock:
        t = _find(task_id)
        if not t:
            return {'ok': False, 'error': '任务不存在'}
        if t['status'] != 'paused':
            return {'ok': False, 'error': f'任务当前状态不可继续: {t["status"]}'}
        t['status'] = 'queued'
        t['updated_at'] = time.time()
        _save_registry()
    _maybe_schedule()
    return {'ok': True}


def delete_task(task_id):
    """删除任务: 运行中的先杀; 清目录状态文件和注册表记录."""
    pause_download(task_id)
    time.sleep(0.3)  # 给worker一点落盘时间
    with _lock:
        t = _find(task_id)
        if not t:
            return {'ok': False, 'error': '任务不存在'}
        path = t['path']
        _registry['tasks'] = [x for x in _registry['tasks'] if x['task_id'] != task_id]
        _runtime.pop(task_id, None)
        _save_registry()
    _clear_dir_state(path)
    return {'ok': True}


def init_on_startup():
    """服务启动时调用: 加载注册表+设置; 中断任务转paused; 按设置自动续接."""
    global _registry, _settings
    with _lock:
        _runtime.clear()  # 进程重启后没有存活的worker(测试里残留线程变孤儿自行退出)
        _registry = _load_json(REGISTRY_FILE, {'tasks': []})
        _settings = {**_settings, **_load_json(SETTINGS_FILE, {})}
        for t in _registry['tasks']:
            if t['status'] in ('running', 'queued'):
                t['status'] = 'paused'
                t['current'] = ''
                t['updated_at'] = time.time()
        _save_registry()
        if _settings['auto_resume']:
            for t in _registry['tasks']:
                if t['status'] == 'paused':
                    t['status'] = 'queued'
            _save_registry()
    if _settings['auto_resume']:
        _maybe_schedule()


# ---------- worker ----------

def _worker(task_id):
    cookie = bili_auth.get_cookie_str()
    try:
        while True:
            with _lock:
                t = _find(task_id)
                if not t:
                    return
                rt = _runtime.get(task_id)
                if rt and rt['pause_requested']:
                    t['status'] = 'paused'
                    t['current'] = ''
                    t['updated_at'] = time.time()
                    _save_registry()
                    _write_dir_state(t)
                    return
                done_set = set(t['done'])
                failed_set = {f['aid'] for f in t['failed']}
                pending = [a for a in t['aids'] if a not in done_set and a not in failed_set]
                if not pending:
                    t['status'] = 'done'
                    t['current'] = ''
                    t['updated_at'] = time.time()
                    _save_registry()
                    if not t['failed']:
                        _clear_dir_state(t['path'])
                    else:
                        _write_dir_state(t)
                    return
                aid = pending[0]
                t['current'] = aid
                path = t['path']

            ok, err = bili_dl.download_one(aid, path, cookie,
                                           on_proc=lambda p: _set_proc(task_id, p))
            with _lock:
                t = _find(task_id)
                if not t:
                    return
                rt = _runtime.get(task_id)
                if rt is None:
                    # 运行时已被清空(应用重启/测试重置): 本worker是孤儿, 直接退出
                    return
                rt['proc'] = None
                if rt and rt['pause_requested']:
                    # 被暂停打断的当前集: 不记成功不记失败, 下次续传重下
                    t['status'] = 'paused'
                    t['current'] = ''
                    t['updated_at'] = time.time()
                    _save_registry()
                    _write_dir_state(t)
                    return
                if ok:
                    if aid not in t['done']:
                        t['done'].append(aid)
                else:
                    if aid not in {f['aid'] for f in t['failed']}:
                        t['failed'].append({'aid': aid, 'error': err})
                t['current'] = ''
                t['updated_at'] = time.time()
                _save_registry()
                _write_dir_state(t)
    finally:
        with _lock:
            _runtime.pop(task_id, None)
        _maybe_schedule()


def _set_proc(task_id, proc):
    with _lock:
        rt = _runtime.get(task_id)
        if rt is None:
            # worker已结束(罕见) -> 直接杀掉多余进程
            try:
                proc.kill()
            except Exception:
                pass
            return
        rt['proc'] = proc
        # 竞态: 进程启动前pause已经来过 -> 补杀
        if rt['pause_requested'] and proc.poll() is None:
            try:
                proc.kill()
            except Exception:
                pass
