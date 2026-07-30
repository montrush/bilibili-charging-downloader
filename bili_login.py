# -*- coding: utf-8 -*-
"""B站扫码登录 - 直接调用B站API, 从Set-Cookie响应头提取cookie.

解决BBDown 1.6.3 login假成功bug: B站改版后cookie在Set-Cookie头里,
不在data.url里, BBDown(2024-08停更)只解析data.url -> SESSDATA永远为空.

用法:
  python bili_login.py              # 生成二维码图片, 轮询等待扫码
  python bili_login.py --qr q.png   # 指定二维码输出路径
  python bili_login.py --timeout 180  # 轮询超时(秒, 默认180)

登录成功后cookie保存到 bili_cookie.txt, 供 bili_download.py 使用.
首次使用: pip install qrcode Pillow requests
"""
import os, sys, time, urllib.parse, argparse

PROJ = os.path.dirname(os.path.abspath(__file__))
DEFAULT_QR = os.path.join(PROJ, 'bilibili_qr.png')
DEFAULT_COOKIE = os.path.join(PROJ, 'bili_cookie.txt')

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
GENERATE_URL = 'https://passport.bilibili.com/x/passport-login/web/qrcode/generate'
POLL_URL = 'https://passport.bilibili.com/x/passport-login/web/qrcode/poll'


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def generate_qr():
    """调用B站API生成扫码登录二维码, 返回 (qrcode_key, qr_url)."""
    import requests
    r = requests.get(GENERATE_URL, headers=HEADERS, timeout=15)
    d = r.json()
    if d.get('code') != 0:
        raise RuntimeError(f"生成二维码失败: {d}")
    return d['data']['qrcode_key'], d['data']['url']


def save_qr_image(qr_url, out_path):
    """把二维码URL内容生成PNG图片."""
    import qrcode
    qrcode.make(qr_url).save(out_path)


def poll_login(qrcode_key, timeout=180):
    """轮询扫码状态. 返回cookie字典或None.

    登录成功时cookie在响应的Set-Cookie头里(r.cookies), 不在data.url.
    """
    import requests
    session = requests.Session()
    session.headers.update(HEADERS)
    last_code = None
    for _ in range(timeout // 2):
        r = session.get(POLL_URL, params={'qrcode_key': qrcode_key}, timeout=15)
        d = r.json()
        code = d.get('data', {}).get('code', -1)
        if code != last_code:
            msg = d.get('data', {}).get('message', '')
            log(f"状态: code={code} {msg}")
            last_code = code
        if code == 0:
            # cookie在Set-Cookie响应头, 不在data.url
            return dict(r.cookies)
        if code == 86038:
            log("二维码过期")
            return None
        time.sleep(2)
    log("轮询超时")
    return None


def save_cookie(cookies, out_path):
    """把cookie字典保存为BBDown -c 可用的字符串格式."""
    keys = ['SESSDATA', 'bili_jct', 'DedeUserID', 'DedeUserID__ckMd5']
    parts = [f"{k}={cookies[k]}" for k in keys if k in cookies and cookies[k]]
    cookie_str = '; '.join(parts)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(cookie_str)
    return cookie_str


def main():
    ap = argparse.ArgumentParser(description='B站扫码登录(直接API, 绕过BBDown bug)')
    ap.add_argument('--qr', default=DEFAULT_QR, help=f'二维码图片输出路径(默认: {os.path.basename(DEFAULT_QR)})')
    ap.add_argument('--cookie', default=DEFAULT_COOKIE, help='cookie输出路径')
    ap.add_argument('--timeout', type=int, default=180, help='轮询超时秒数(默认180)')
    args = ap.parse_args()

    log("=== B站扫码登录 ===")
    qrcode_key, qr_url = generate_qr()
    save_qr_image(qr_url, args.qr)
    log(f"二维码已保存: {args.qr}")
    log(f"请用手机B站APP扫码并确认登录 (二维码内容: {qr_url[:60]}...)")

    cookies = poll_login(qrcode_key, args.timeout)
    if not cookies or 'SESSDATA' not in cookies:
        log("登录失败或超时, 未获取到SESSDATA")
        sys.exit(1)

    cookie_str = save_cookie(cookies, args.cookie)
    log(f"登录成功! SESSDATA长度={len(cookies.get('SESSDATA', ''))}")
    log(f"DedeUserID={cookies.get('DedeUserID', '?')}")
    log(f"cookie已保存: {args.cookie}")
    log("现在可以用 bili_download.py 下载充电视频了")


if __name__ == '__main__':
    main()
