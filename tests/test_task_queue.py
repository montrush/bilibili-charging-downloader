# -*- coding: utf-8 -*-
"""并行任务队列状态机测试: mock download_one, 全场景验证.

场景:
1. 并行调度: 3任务max_parallel=2 -> 2跑1排队, 一个完成后补位
2. 暂停释放槽位: 暂停running -> 排队的顶上来
3. 注册表持久化: init_on_startup重载 -> running/queued转paused
4. 自动续接: auto_resume=True -> 启动直接排队开跑
5. 同目录去重: 同路径再发起 -> 合并不新建
6. 目录状态文件遗留导入: v1.0.4的.bili_dl_task.json -> 导入done
7. 删除任务: 注册表+目录文件清理
"""
import json, os, sys, tempfile, threading, time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['BILI_CONFIG_DIR'] = tempfile.mkdtemp(prefix='bili_test_cfg_')

from server import task_manager as tm

GATES = {}   # aid -> threading.Event: 不set则下载阻塞(模拟下载中)
FAIL_AIDS = set()


def fake_download(aid, path, cookie=None, on_proc=None):
    killed = {'v': False}

    class FakeProc:
        def poll(self): return None if not killed['v'] else 1
        def kill(self): killed['v'] = True
    if on_proc:
        on_proc(FakeProc())
    if aid in FAIL_AIDS:
        return False, '模拟失败'
    g = GATES.get(aid)
    if g is not None:
        # 轮询等待, 模拟真实kill能打断下载
        while not g.wait(timeout=0.05):
            if killed['v']:
                return False, '被杀'
        if GATES.get(aid) is g:  # 防跨测试僵尸线程误删新gate
            GATES.pop(aid)
    return True, ''


tm.bili_dl.download_one = fake_download
tm.bili_auth.get_cookie_str = lambda: 'fake'


def wait_for(cond, timeout=8, desc=''):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if cond():
            return True
        time.sleep(0.05)
    raise AssertionError(f'超时: {desc}')


def reset():
    with tm._lock:
        # 先杀掉残留worker的进程(僵尸线程随之退出)
        for rt in tm._runtime.values():
            rt['pause_requested'] = True
            p = rt.get('proc')
            if p:
                try:
                    p.kill()
                except Exception:
                    pass
        tm._registry = {'tasks': []}
        tm._runtime = {}
        tm._settings = {'max_parallel': 2, 'auto_resume': False}
    tm._save_registry()
    tm._save_settings()
    time.sleep(0.2)  # 等僵尸线程退出


results = []

def check(name, fn):
    reset()
    GATES.clear(); FAIL_AIDS.clear()
    try:
        fn()
        results.append((name, 'PASS', ''))
        print(f'  [PASS] {name}')
    except Exception as e:
        results.append((name, 'FAIL', str(e)))
        print(f'  [FAIL] {name}: {e}')


def status_of(tid):
    return tm.get_progress(tid)['status']


# ---------- 1. 并行调度 ----------
def t1():
    d1, d2, d3 = (tempfile.mkdtemp() for _ in range(3))
    GATES['a2'] = threading.Event()  # 卡住任务1的第二集
    GATES['b1'] = threading.Event()  # 卡住任务2
    r1 = tm.start_download(['a1', 'a2'], d1, title='任务A')
    r2 = tm.start_download(['b1'], d2, title='任务B')
    r3 = tm.start_download(['c1'], d3, title='任务C')
    wait_for(lambda: status_of(r3['task_id']) in ('queued', 'running'), desc='任务C进队列')
    # max_parallel=2: C应排队
    time.sleep(0.3)
    assert status_of(r1['task_id']) == 'running', f"A={status_of(r1['task_id'])}"
    assert status_of(r2['task_id']) == 'running', f"B={status_of(r2['task_id'])}"
    assert status_of(r3['task_id']) == 'queued', f"C={status_of(r3['task_id'])}"
    # 放行B -> B完成 -> C补位
    GATES['b1'].set()
    wait_for(lambda: status_of(r2['task_id']) == 'done', desc='B完成')
    wait_for(lambda: status_of(r3['task_id']) in ('running', 'done'), desc='C补位')
    # 收尾
    GATES.get('a2') and GATES['a2'].set()
    wait_for(lambda: status_of(r1['task_id']) == 'done', desc='A完成')
    wait_for(lambda: status_of(r3['task_id']) == 'done', desc='C完成')
    # 全成功: 目录状态文件应清理
    for d in (d1, d2, d3):
        assert not os.path.exists(os.path.join(d, '.bili_dl_task.json')), f'{d} 状态文件未清理'

check('1.并行调度2槽位+补位', t1)


# ---------- 2. 暂停释放槽位 ----------
def t2():
    d1, d2, d3 = (tempfile.mkdtemp() for _ in range(3))
    GATES['a1'] = threading.Event()
    GATES['b1'] = threading.Event()
    GATES['c1'] = threading.Event()  # C也要占住槽位
    r1 = tm.start_download(['a1'], d1, title='A')
    r2 = tm.start_download(['b1'], d2, title='B')
    r3 = tm.start_download(['c1'], d3, title='C')
    time.sleep(0.3)
    assert status_of(r3['task_id']) == 'queued'
    tm.pause_download(r1['task_id'])
    wait_for(lambda: status_of(r1['task_id']) == 'paused', desc='A暂停')
    wait_for(lambda: status_of(r3['task_id']) == 'running', desc='C顶上槽位')
    assert status_of(r2['task_id']) == 'running'
    # A在paused, 继续 -> 排队(槽位被B/C占着)
    tm.resume_download(r1['task_id'])
    time.sleep(0.3)
    assert status_of(r1['task_id']) == 'queued', f"A={status_of(r1['task_id'])}"
    GATES['b1'].set()
    wait_for(lambda: status_of(r1['task_id']) == 'running', desc='A补位')
    # A续传重下a1: gate在kill路径下未消费, 仍挡着 -> 放行
    GATES['a1'].set()
    GATES['c1'].set()
    wait_for(lambda: status_of(r1['task_id']) == 'done', desc='A完成')
    wait_for(lambda: status_of(r3['task_id']) == 'done', desc='C完成')

check('2.暂停释放槽位+继续重排队', t2)


# ---------- 3. 注册表持久化+启动恢复 ----------
def t3():
    d1 = tempfile.mkdtemp()
    GATES['a1'] = threading.Event()
    r1 = tm.start_download(['a1', 'a2'], d1, title='A')
    time.sleep(0.3)
    assert status_of(r1['task_id']) == 'running'
    # 模拟应用退出: 不调pause直接"重启"(真实重启时进程死掉, 测试里旧线程变孤儿)
    GATES.pop('a1', None)  # 死掉的进程连同gate一起消失
    tm.init_on_startup()
    p = tm.get_progress(r1['task_id'])
    assert p['status'] == 'paused', f"重启后={p['status']}"
    assert p['current'] == '', 'current应清空'
    # 注册表文件真实存在
    assert os.path.exists(tm.REGISTRY_FILE)
    data = json.load(open(tm.REGISTRY_FILE, encoding='utf-8'))
    assert data['tasks'][0]['status'] == 'paused'
    # 手动续接
    tm.resume_download(r1['task_id'])
    wait_for(lambda: status_of(r1['task_id']) == 'done', desc='续接后完成')
    assert tm.get_progress(r1['task_id'])['success'] == 2

check('3.注册表持久化+启动转paused+手动续接', t3)


# ---------- 4. 自动续接 ----------
def t4():
    d1 = tempfile.mkdtemp()
    r1 = tm.start_download(['a1'], d1, title='A')
    time.sleep(0.3)
    tm.update_settings({'auto_resume': True})
    tm.init_on_startup()
    wait_for(lambda: status_of(r1['task_id']) == 'done', desc='自动续接完成')
    assert tm.get_progress(r1['task_id'])['success'] == 1

check('4.auto_resume启动自动续接', t4)


# ---------- 5. 同目录去重 ----------
def t5():
    d1 = tempfile.mkdtemp()
    GATES['a1'] = threading.Event()
    r1 = tm.start_download(['a1'], d1, title='A')
    time.sleep(0.3)
    r2 = tm.start_download(['a1', 'a2'], d1, title='A')
    assert r2['existing'] is True, '应识别已有任务'
    assert r2['task_id'] == r1['task_id'], '应复用task_id'
    p = tm.get_progress(r1['task_id'])
    assert p['total'] == 2, f"应合并新aid, total={p['total']}"
    GATES['a1'].set()
    wait_for(lambda: status_of(r1['task_id']) == 'done', desc='合并后完成')
    assert tm.get_progress(r1['task_id'])['success'] == 2

check('5.同目录去重合并', t5)


# ---------- 6. 目录状态文件遗留导入 ----------
def t6():
    d1 = tempfile.mkdtemp()
    # 模拟v1.0.4留下的状态文件
    with open(os.path.join(d1, '.bili_dl_task.json'), 'w', encoding='utf-8') as f:
        json.dump({'aids': ['a1', 'a2', 'a3'], 'done': ['a1'], 'failed': [{'aid': 'a2', 'error': 'x'}]}, f)
    r1 = tm.start_download(['a1', 'a2', 'a3'], d1, title='A')
    assert r1['resumed'] is True and r1['skipped'] == 1, f"{r1}"
    wait_for(lambda: status_of(r1['task_id']) == 'done', desc='导入后完成')
    p = tm.get_progress(r1['task_id'])
    assert p['success'] == 2, f"success={p['success']}"  # a1导入 + a3新下; a2保持失败
    assert len(p['failed']) == 1, 'a2应保持失败记录'
    # 有失败: 目录文件保留
    assert os.path.exists(os.path.join(d1, '.bili_dl_task.json'))

check('6.遗留目录状态文件导入', t6)


# ---------- 7. 删除任务 ----------
def t7():
    d1 = tempfile.mkdtemp()
    GATES['a1'] = threading.Event()
    r1 = tm.start_download(['a1'], d1, title='A')
    time.sleep(0.3)
    tm.delete_task(r1['task_id'])
    assert tm.get_progress(r1['task_id']) is None, '注册表应无此任务'
    assert not os.path.exists(os.path.join(d1, '.bili_dl_task.json')), '目录文件应清理'
    data = json.load(open(tm.REGISTRY_FILE, encoding='utf-8'))
    assert len(data['tasks']) == 0
    GATES['a1'].set()  # 放行残余线程

check('7.删除任务清理', t7)


# ---------- 8. 并行数动态调大立即补位 ----------
def t8():
    d1, d2 = tempfile.mkdtemp(), tempfile.mkdtemp()
    tm.update_settings({'max_parallel': 1})
    GATES['a1'] = threading.Event()
    r1 = tm.start_download(['a1'], d1, title='A')
    r2 = tm.start_download(['b1'], d2, title='B')
    time.sleep(0.3)
    assert status_of(r1['task_id']) == 'running'
    assert status_of(r2['task_id']) == 'queued'
    tm.update_settings({'max_parallel': 3})
    time.sleep(0.3)
    assert status_of(r2['task_id']) in ('running', 'done'), f"B={status_of(r2['task_id'])}"
    GATES['a1'].set()
    wait_for(lambda: status_of(r1['task_id']) == 'done', desc='A完成')

check('8.调大并行数立即补位', t8)


print('\n========== 汇总 ==========')
passed = sum(1 for _, s, _ in results if s == 'PASS')
print(f'{passed}/{len(results)} PASS')
sys.exit(0 if passed == len(results) else 1)
