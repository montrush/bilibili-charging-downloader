# -*- coding: utf-8 -*-
"""B站视频解析+下载服务."""
import os, re, json, subprocess, datetime

PROJ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BBDOWN = os.path.join(PROJ, 'BBDown.exe')  # Windows; Linux下用PATH中的BBDown
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
FILE_PATTERN = '<videoTitle>_<videoDate>'


def resolve_url(url):
    """短链 -> 最终URL."""
    if not url.startswith('http'):
        url = 'https://' + url
    try:
        import requests
        r = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        return r.url
    except Exception:
        return url


def parse_aid(url):
    """从URL提取aid. 返回aid字符串或None."""
    resolved = resolve_url(url)
    m = re.search(r'av(\d+)', resolved)
    if m:
        return m.group(1)
    m = re.search(r'(BV\w+)', resolved)
    if m:
        import requests
        r = requests.get('https://api.bilibili.com/x/web-interface/view',
                         params={'bvid': m.group(1)}, headers=HEADERS, timeout=15)
        d = r.json()
        if d.get('code') == 0:
            return str(d['data']['aid'])
    return None


def get_video_info(aid, cookie=None):
    """查视频信息+合集. 返回 dict."""
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
    result = {
        'aid': str(aid),
        'title': data.get('title', ''),
        'pubdate': data.get('pubdate', 0),
        'date': datetime.datetime.fromtimestamp(data.get('pubdate', 0)).strftime('%Y-%m-%d') if data.get('pubdate') else '',
        'duration': data.get('duration', 0),
        'is_collection': False,
        'collection': None,
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
                    'title': ep['title'],
                    'date': datetime.datetime.fromtimestamp(pubdate).strftime('%Y-%m-%d') if pubdate else '',
                    'duration': arc.get('duration', 0),
                })
        result['is_collection'] = True
        result['collection'] = {
            'season_id': ugc.get('id'),
            'title': ugc.get('title', ''),
            'episodes': eps,
        }
    return result


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


def download_one(aid, download_dir, cookie=None):
    """下载单个视频. 返回 (success, error_msg)."""
    bbdown = find_bbdown()
    if not bbdown:
        return False, 'BBDown not found'
    os.makedirs(download_dir, exist_ok=True)
    cmd = [bbdown, f'av{aid}', '--work-dir', download_dir, '-F', FILE_PATTERN, '-p', 'ALL']
    if cookie:
        cmd += ['-c', cookie]
    try:
        r = subprocess.run(cmd, cwd=PROJ, capture_output=True, text=True, timeout=600)
        if r.returncode == 0:
            return True, None
        return False, f'exit={r.returncode}'
    except subprocess.TimeoutExpired:
        return False, 'timeout'
    except Exception as e:
        return False, str(e)
