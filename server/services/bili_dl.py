# -*- coding: utf-8 -*-
"""B站视频解析+下载服务.

支持的链接类型:
- 视频: https://www.bilibili.com/video/BVxxx / avxxx
- 短链/微信分享: https://b23.tv/xxx (自动302解析)
- 合集:
  - https://space.bilibili.com/{mid}/channel/collectiondetail?sid={sid}
  - https://space.bilibili.com/{mid}/lists/{id}?type=series|season  (新版空间合集/列表页; type=series=视频列表走 /x/series, type=season=合集走 season API)
  - https://www.bilibili.com/video/BVxxx/?...&sid={sid}
- 文章: https://www.bilibili.com/read/cv{id}
- 图片/动态: https://t.bilibili.com/{id}, https://h.bilibili.com/{id}, https://www.bilibili.com/opus/{id}
"""
import os, re, json, subprocess, datetime

PROJ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BBDOWN = os.path.join(PROJ, 'BBDown.exe')  # Windows; Linux下用PATH中的BBDown
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
FILE_PATTERN = '<videoTitle>_<videoDate>'


def resolve_url(url):
    """短链/微信分享 -> 最终URL."""
    if not url:
        return url
    if not url.startswith('http'):
        url = 'https://' + url
    try:
        import requests
        r = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        return r.url
    except Exception:
        return url


def detect_link_type(url):
    """识别链接类型: video/collection/article/image/unknown."""
    if not url:
        return 'unknown'
    resolved = resolve_url(url)
    lo = resolved.lower()
    if re.search(r'/read/cv\d+', lo):
        return 'article'
    if re.search(r'/(t|h|opus)/\d+', lo) or re.search(r'\b[th]\.bilibili\.com\b', lo):
        return 'image'
    if (re.search(r'/channel/collectiondetail', lo)
            or re.search(r'[?&]sid=\d+', lo)
            or re.search(r'space\.bilibili\.com/\d+/lists/\d+', lo)):
        return 'collection'
    if re.search(r'/video/(av\d+|bv\w+)', lo):
        return 'video'
    return 'unknown'


def extract_bvid(url):
    m = re.search(r'(BV\w+)', url)
    return m.group(1) if m else None


def extract_aid(url):
    m = re.search(r'av(\d+)', url, re.I)
    return m.group(1) if m else None


def extract_sid(url):
    m = re.search(r'[?&]sid=(\d+)', url)
    if m:
        return m.group(1)
    # 新版空间合集/列表页: space.bilibili.com/{mid}/lists/{id}?type=series|season
    # ⚠️ type=series 时 {id} 是 series_id(视频列表), type=season 时是 season_id(合集).
    # 两种 id 都是纯数字且可能撞号, 必须按 type 选 API, 否则会查到别人的合集(假阳性).
    m = re.search(r'space\.bilibili\.com/\d+/lists/(\d+)', url)
    return m.group(1) if m else None


def extract_list_type(url):
    """新版 lists 页 ?type= 参数: series(视频列表) / season(合集). 无则 None."""
    m = re.search(r'[?&]type=(series|season)\b', url, re.I)
    return m.group(1).lower() if m else None


def extract_mid(url):
    m = re.search(r'space\.bilibili\.com/(\d+)', url)
    return m.group(1) if m else None


def extract_cv_id(url):
    m = re.search(r'/read/cv(\d+)', url)
    return m.group(1) if m else None


def extract_dynamic_id(url):
    m = re.search(r'/(t|h|opus)/(\d+)', url)
    return m.group(2) if m else None


def bvid_to_aid(bvid):
    import requests
    r = requests.get('https://api.bilibili.com/x/web-interface/view',
                     params={'bvid': bvid}, headers=HEADERS, timeout=15)
    d = r.json()
    if d.get('code') == 0:
        return str(d['data']['aid'])
    return None


def get_video_info(aid, cookie=None):
    """查视频信息+UGC合集. 返回 dict."""
    import requests
    headers = dict(HEADERS)
    if cookie:
        headers['Cookie'] = cookie
    r = requests.get('https://api.bilibili.com/x/web-interface/view',
                     params={'aid': aid}, headers=headers, timeout=15)
    d = r.json()
    if d.get('code') != 0:
        return None
    data = d['data']
    owner = data.get('owner', {})
    stat = data.get('stat', {})
    result = {
        'aid': str(aid),
        'bvid': data.get('bvid', ''),
        'title': data.get('title', ''),
        'pubdate': data.get('pubdate', 0),
        'date': datetime.datetime.fromtimestamp(data.get('pubdate', 0)).strftime('%Y-%m-%d') if data.get('pubdate') else '',
        'duration': data.get('duration', 0),
        'is_collection': False,
        'collection': None,
        # 状态窗口元数据
        'owner': owner.get('name', ''),
        'owner_mid': owner.get('mid', 0),
        'owner_face': owner.get('face', ''),
        'pic': (data.get('pic') or '').replace('http://', 'https://'),
        'desc': data.get('desc', ''),
        'tname': data.get('tname', '') or data.get('tname_v2', ''),
        'stat': {
            'view': stat.get('view', 0), 'danmaku': stat.get('danmaku', 0),
            'reply': stat.get('reply', 0), 'favorite': stat.get('favorite', 0),
            'coin': stat.get('coin', 0), 'share': stat.get('share', 0),
            'like': stat.get('like', 0),
        },
    }
    ugc = data.get('ugc_season')
    if ugc:
        eps = []
        for section in ugc.get('sections', []):
            for ep in section.get('episodes', []):
                arc = ep.get('arc', {})
                pubdate = arc.get('pubdate', 0)
                eps.append({
                    'aid': str(ep['aid']),
                    'bvid': ep.get('bvid', ''),
                    'title': ep['title'],
                    'date': datetime.datetime.fromtimestamp(pubdate).strftime('%Y-%m-%d') if pubdate else '',
                    'duration': arc.get('duration', 0),
                })
        ustat = ugc.get('stat', {})
        result['is_collection'] = True
        result['collection'] = {
            'season_id': ugc.get('id'),
            'title': ugc.get('title', ''),
            'episodes': eps,
            'cover': (ugc.get('cover') or '').replace('http://', 'https://'),
            'intro': ugc.get('intro', ''),
            'ep_count': ugc.get('ep_count', len(eps)),
            'stat': {
                'view': ustat.get('view', 0), 'danmaku': ustat.get('danmaku', 0),
                'reply': ustat.get('reply', 0), 'favorite': ustat.get('fav', 0),
                'coin': ustat.get('coin', 0), 'share': ustat.get('share', 0),
                'like': ustat.get('like', 0),
            },
        }
    return result


def fetch_collection_by_sid(sid, mid=None, cookie=None):
    """通过空间合集 sid 获取视频列表+合集元数据. 返回 {'archives': [...], 'meta': {...}}."""
    import requests
    headers = dict(HEADERS)
    if cookie:
        headers['Cookie'] = cookie

    meta = {}
    # 查 season 元数据 (封面/简介/UP主mid)
    r = requests.get(
        'https://api.bilibili.com/x/polymer/web-space/seasons_archives_list',
        params={'season_id': sid, 'page_num': 1, 'page_size': 1},
        headers=headers, timeout=15,
    )
    try:
        meta = r.json().get('data', {}).get('meta', {}) or {}
    except Exception:
        pass
    if not mid:
        mid = meta.get('mid')

    if not mid:
        return None

    archives = []
    page_num = 1
    while True:
        r = requests.get(
            'https://api.bilibili.com/x/polymer/web-space/seasons_archives_list',
            params={'mid': mid, 'season_id': sid, 'page_num': page_num, 'page_size': 30},
            headers=headers, timeout=15,
        )
        d = r.json()
        if d.get('code') != 0:
            break
        items = d.get('data', {}).get('archives', [])
        if not items:
            break
        for item in items:
            pubdate = item.get('pubdate', 0)
            archives.append({
                'aid': str(item['aid']),
                'bvid': item.get('bvid', ''),
                'title': item.get('title', ''),
                'date': datetime.datetime.fromtimestamp(pubdate).strftime('%Y-%m-%d') if pubdate else '',
                'duration': item.get('duration', 0),
            })
        if len(items) < 30:
            break
        page_num += 1

    return {'archives': archives, 'meta': meta}


def fetch_series_by_id(series_id, mid=None, cookie=None):
    """通过 视频列表(series) series_id 获取视频列表+元数据. 返回 {'archives':[...], 'meta':{}}.

    对应新版空间页 space.bilibili.com/{mid}/lists/{id}?type=series (老"视频列表").
    接口为旧的 /x/series/* (polymer/web-space 的 series 接口已下线返回HTML).
    """
    import requests
    headers = dict(HEADERS)
    if cookie:
        headers['Cookie'] = cookie
    if mid:
        headers['Referer'] = f'https://space.bilibili.com/{mid}/lists/{series_id}?type=series'

    meta = {}
    try:
        r = requests.get('https://api.bilibili.com/x/series/series',
                         params={'series_id': series_id}, headers=headers, timeout=15)
        meta = r.json().get('data', {}).get('meta', {}) or {}
    except Exception:
        pass
    if not mid:
        mid = meta.get('mid')
    if not mid:
        return None

    archives = []
    pn = 1
    while True:
        r = requests.get('https://api.bilibili.com/x/series/archives',
                         params={'mid': mid, 'series_id': series_id, 'pn': pn, 'ps': 30},
                         headers=headers, timeout=15)
        d = r.json()
        if d.get('code') != 0:
            break
        items = d.get('data', {}).get('archives', [])
        if not items:
            break
        for item in items:
            pubdate = item.get('pubdate', 0)
            archives.append({
                'aid': str(item['aid']),
                'bvid': item.get('bvid', ''),
                'title': item.get('title', ''),
                'date': datetime.datetime.fromtimestamp(pubdate).strftime('%Y-%m-%d') if pubdate else '',
                'duration': item.get('duration', 0),
            })
        if len(items) < 30:
            break
        pn += 1

    return {'archives': archives, 'meta': meta}


def fetch_article_info(cv_id):
    """获取专栏文章信息."""
    import requests
    r = requests.get('https://api.bilibili.com/x/article/viewinfo',
                     params={'id': cv_id}, headers=HEADERS, timeout=15)
    d = r.json()
    if d.get('code') != 0:
        return None
    data = d['data']
    stats = data.get('stats', {})
    return {
        'cv_id': cv_id,
        'title': data.get('title', ''),
        'author': data.get('author_name', ''),
        'banner_url': data.get('banner_url', ''),
        'summary': data.get('summary', ''),
        'words': data.get('words', 0),
        'view': stats.get('view', 0),
    }


def fetch_image_info(dynamic_id):
    """获取动态/图片信息."""
    import requests
    r = requests.get('https://api.bilibili.com/x/polymer/web-dynamic/v1/detail',
                     params={'id': dynamic_id}, headers=HEADERS, timeout=15)
    d = r.json()
    if d.get('code') != 0:
        return None
    item = d.get('data', {}).get('item', {})
    modules = item.get('modules', {})
    module_author = modules.get('module_author', {})
    module_dynamic = modules.get('module_dynamic', {})
    desc = module_dynamic.get('desc', {})
    major = module_dynamic.get('major', {})
    pics = []
    if major:
        if 'opus' in major:
            for pic in major.get('opus', {}).get('pics', []):
                pics.append(pic.get('url', ''))
        elif 'draw' in major:
            for pic in major.get('draw', {}).get('items', []):
                pics.append(pic.get('src', ''))
    return {
        'dynamic_id': dynamic_id,
        'author': module_author.get('name', ''),
        'content': desc.get('text', ''),
        'pictures': pics,
    }


def parse_link(url, cookie=None):
    """统一解析入口.

    返回包含 link_type 的 dict, 识别失败返回 None.
    """
    if not url:
        return None

    resolved = resolve_url(url)
    link_type = detect_link_type(resolved)
    result = {
        'link_type': link_type,
        'raw_url': url,
        'resolved_url': resolved,
    }

    if link_type == 'article':
        cv_id = extract_cv_id(resolved)
        info = fetch_article_info(cv_id) if cv_id else None
        result.update({
            'title': info.get('title', '') if info else '专栏文章',
            'article_info': info or {},
            'message': '识别为专栏文章，暂不支持下载',
        })
        return result

    if link_type == 'image':
        dynamic_id = extract_dynamic_id(resolved)
        info = fetch_image_info(dynamic_id) if dynamic_id else None
        content = (info or {}).get('content', '')
        result.update({
            'title': (content[:50] + '...') if len(content) > 50 else (content or '图片动态'),
            'image_info': info or {},
            'message': '识别为图片动态，暂不支持下载',
        })
        return result

    # 视频 / 合集
    sid = extract_sid(resolved)
    mid = extract_mid(resolved)
    bvid = extract_bvid(resolved)
    aid = extract_aid(resolved)

    if not aid and bvid:
        aid = bvid_to_aid(bvid)

    if sid:
        # /lists/{id}?type=series => 视频列表(series_id); 其余 => 合集(season_id)
        # ⚠️ series_id 与 season_id 都是纯数字可能撞号, 必须按 type 选 API.
        is_series = (extract_list_type(resolved) == 'series'
                     and re.search(r'space\.bilibili\.com/\d+/lists/\d+', resolved))
        if is_series:
            coll = fetch_series_by_id(sid, mid=mid, cookie=cookie)
            kind_label = '视频列表'
        else:
            coll = fetch_collection_by_sid(sid, mid=mid, cookie=cookie)
            kind_label = '空间合集'
        if coll and coll.get('archives'):
            episodes = coll['archives']
            meta = coll.get('meta') or {}
            coll_title = meta.get('name') or f'{kind_label} #{sid}'
            result.update({
                'aid': '',
                'bvid': bvid or '',
                'title': coll_title,
                'date': '',
                'duration': 0,
                'is_collection': True,
                'owner_mid': meta.get('mid', 0),
                'collection': {
                    'season_id': sid,
                    'title': coll_title,
                    'episodes': episodes,
                    'cover': (meta.get('cover') or '').replace('http://', 'https://'),
                    'intro': meta.get('description', ''),
                    'ep_count': meta.get('total', len(episodes)),
                    'stat': {},
                },
                'message': f'识别为{kind_label}，共 {len(episodes)} 个视频',
            })
            return result
        # sid 匹配但拿不到合集, 可能是过期/无效 sid, 降级为普通视频
        result['link_type'] = 'video'

    if aid:
        info = get_video_info(aid, cookie)
        if info:
            result.update(info)
            if info.get('is_collection'):
                result['link_type'] = 'collection'
                result['message'] = f"识别为UGC合集，共 {len(info.get('collection', {}).get('episodes', []))} 个视频"
            else:
                result['link_type'] = 'video'
                result['message'] = '识别为视频'
            return result

    # 能识别类型但拿不到详情, 返回基础信息
    result['message'] = '链接类型已识别，但无法获取详情'
    return result


# 兼容旧接口
parse_aid = lambda url: parse_link(url, cookie=None)


def find_bbdown():
    """找BBDown可执行文件."""
    if os.path.exists(BBDOWN):
        return BBDOWN
    import shutil
    for name in ['BBDown', 'BBDown.exe', 'bbdown']:
        p = shutil.which(name)
        if p:
            return p
    return None


def download_one(aid, download_dir, cookie=None, on_proc=None):
    """下载单个视频. 返回 (success, error_msg).

    on_proc: Popen创建后回调(任务管理器持有进程句柄, 暂停时kill).
    """
    bbdown = find_bbdown()
    if not bbdown:
        return False, 'BBDown not found'
    os.makedirs(download_dir, exist_ok=True)
    cmd = [bbdown, f'av{aid}', '--work-dir', download_dir, '-F', FILE_PATTERN, '-p', 'ALL']
    if cookie:
        cmd += ['-c', cookie]
    try:
        proc = subprocess.Popen(cmd, cwd=PROJ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if on_proc:
            on_proc(proc)
        # 超时放宽到1小时: 充电视频可能很长/断链慢速重试
        rc = proc.wait(timeout=3600)
        if rc == 0:
            return True, None
        return False, f'exit={rc}'
    except subprocess.TimeoutExpired:
        try:
            proc.kill()
        except Exception:
            pass
        return False, 'timeout'
    except Exception as e:
        return False, str(e)
