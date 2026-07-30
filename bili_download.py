# -*- coding: utf-8 -*-
"""B站视频下载 - 支持单视频/UGC合集全下/充电视频.

用 bili_login.py 登录获取cookie后, 用BBDown + cookie下载充电视频完整版.
合集下载: B站API取ugc_season全部episode aid, 逐个下载(BBDown 1.6.3不认合集URL).
文件名格式: <标题>_<发布日期_时间>.mp4

用法:
  python bili_download.py <链接>                    # 下载(合集自动全下)
  python bili_download.py <链接> --info             # 仅查信息(合集结构/清晰度)
  python bili_download.py <链接> -p 1,2             # 指定集
  python bili_download.py <链接> --cookie c.txt     # 指定cookie文件(下充电视频)

首次使用:
  1. 下载 BBDown.exe (https://github.com/nilaoda/BBDown/releases) 放到本目录或PATH
  2. pip install qrcode Pillow requests
  3. python bili_login.py  # 扫码登录, 生成bili_cookie.txt
"""
import os, sys, json, subprocess, argparse, datetime, re

PROJ = os.path.dirname(os.path.abspath(__file__))
BBDOWN = os.path.join(PROJ, 'BBDown.exe')
DEFAULT_COOKIE = os.path.join(PROJ, 'bili_cookie.txt')
DOWNLOADS = os.path.join(PROJ, 'downloads')
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
FILE_PATTERN = '<videoTitle>_<videoDate>'  # 文件名带发布日期


def resolve_url(url):
    """短链 -> 最终URL."""
    if not url.startswith('http'):
        url = 'https://' + url
    try:
        import requests
        opener = requests.Session()
        opener.headers.update(HEADERS)
        r = opener.get(url, timeout=15, allow_redirects=True)
        return r.url
    except Exception:
        return url


def get_video_info(aid, cookie=None):
    """用B站API查视频信息. 返回 (title, ugc_season_or_None)."""
    import requests
    headers = dict(HEADERS)
    if cookie:
        headers['Cookie'] = cookie
    r = requests.get('https://api.bilibili.com/x/web-interface/view',
                     params={'aid': aid}, headers=headers, timeout=15)
    d = r.json()
    if d.get('code') != 0:
        return None, None
    return d['data'].get('title'), d['data'].get('ugc_season')


def extract_collection_episodes(ugc_season):
    """从ugc_season提取所有episode的(aid, title, pubdate)."""
    eps = []
    for section in ugc_season.get('sections', []):
        for ep in section.get('episodes', []):
            arc = ep.get('arc', {})
            pubdate = arc.get('pubdate', 0)
            eps.append({
                'aid': ep['aid'],
                'title': ep['title'],
                'pubdate': pubdate,
                'date': datetime.datetime.fromtimestamp(pubdate).strftime('%Y-%m-%d') if pubdate else '',
                'duration': arc.get('duration', 0),
            })
    return eps


def parse_aid_from_url(url):
    """从URL提取aid (支持短链/BV/av)."""
    resolved = resolve_url(url)
    # av号
    m = re.search(r'av(\d+)', resolved)
    if m:
        return m.group(1)
    # BV号 -> 通过API转aid
    m = re.search(r'(BV\w+)', resolved)
    if m:
        import requests
        r = requests.get('https://api.bilibili.com/x/web-interface/view',
                         params={'bvid': m.group(1)}, headers=HEADERS, timeout=15)
        d = r.json()
        if d.get('code') == 0:
            return str(d['data']['aid'])
    return None


def run_bbdown(aid, cookie=None, page='ALL', info_only=False):
    """调用BBDown下载单个视频."""
    if not os.path.exists(BBDOWN):
        # 尝试PATH中找
        import shutil
        bb = shutil.which('BBDown') or shutil.which('BBDown.exe')
        if not bb:
            print(f"错误: 找不到BBDown.exe, 请从 https://github.com/nilaoda/BBDown/releases 下载放到 {PROJ}")
            sys.exit(1)
        bbdown = bb
    else:
        bbdown = BBDOWN

    os.makedirs(DOWNLOADS, exist_ok=True)
    cmd = [bbdown, f'av{aid}', '--work-dir', DOWNLOADS, '-F', FILE_PATTERN, '-p', page]
    if cookie:
        if os.path.exists(cookie):
            with open(cookie, 'r', encoding='utf-8') as f:
                cmd += ['-c', f.read().strip()]
        else:
            cmd += ['-c', cookie]
    if info_only:
        cmd += ['-info', '--show-all']
    subprocess.run(cmd, cwd=PROJ)


def main():
    ap = argparse.ArgumentParser(description='B站视频下载(支持充电视频/UGC合集)')
    ap.add_argument('url', help='B站链接(短链/BV/av/合集)')
    ap.add_argument('--info', action='store_true', help='仅查信息不下载')
    ap.add_argument('-p', '--page', default='ALL', help='选集(ALL/1,2/3-5)')
    ap.add_argument('--cookie', default=DEFAULT_COOKIE, help=f'cookie文件(默认: {os.path.basename(DEFAULT_COOKIE)})')
    args = ap.parse_args()

    aid = parse_aid_from_url(args.url)
    if not aid:
        print(f"无法解析链接: {args.url}")
        sys.exit(1)

    print(f"链接: {args.url}")
    print(f"aid: {aid}")

    cookie_str = None
    if os.path.exists(args.cookie):
        with open(args.cookie, 'r', encoding='utf-8') as f:
            cookie_str = f.read().strip()
        print(f"cookie: {args.cookie} (len={len(cookie_str)})")
    else:
        print(f"cookie文件不存在: {args.cookie} (充电视频将只能下试看片段)")

    title, ugc_season = get_video_info(aid, cookie_str)

    if args.info:
        print(f"\n标题: {title}")
        if ugc_season:
            eps = extract_collection_episodes(ugc_season)
            print(f"合集: {ugc_season.get('title')} (season_id={ugc_season.get('id')})")
            print(f"共 {len(eps)} 集")
            for i, ep in enumerate(eps[:10], 1):
                print(f"  P{i}: [{ep['aid']}] {ep['date']} {ep['title'][:40]}")
            if len(eps) > 10:
                print(f"  ... (共{len(eps)}集)")
        else:
            print("非合集视频(单P或多P)")
        run_bbdown(aid, args.cookie, args.page, info_only=True)
        return

    if ugc_season:
        eps = extract_collection_episodes(ugc_season)
        print(f"\n合集: {ugc_season.get('title')} 共 {len(eps)} 集")
        print(f"下载到: {DOWNLOADS}")
        print(f"文件名: <标题>_<发布日期>.mp4\n")
        done_file = os.path.join(PROJ, 'download_done.txt')
        done = set()
        if os.path.exists(done_file):
            with open(done_file, 'r') as f:
                done = set(l.strip() for l in f if l.strip())
        for i, ep in enumerate(eps, 1):
            if str(ep['aid']) in done:
                print(f"[{i}/{len(eps)}] 跳过(已下载) aid={ep['aid']}")
                continue
            print(f"[{i}/{len(eps)}] aid={ep['aid']} {ep['title'][:40]}")
            run_bbdown(ep['aid'], args.cookie)
            with open(done_file, 'a', encoding='utf-8') as f:
                f.write(str(ep['aid']) + '\n')
        print(f"\n合集下载完成! 共 {len(eps)} 集")
    else:
        print(f"\n标题: {title}")
        run_bbdown(aid, args.cookie, args.page)


if __name__ == '__main__':
    main()
