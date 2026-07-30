# -*- coding: utf-8 -*-
"""B站扫码登录服务 - 直接调API, 从Set-Cookie提取cookie."""
import os

PROJ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_DIR = os.environ.get('BILI_CONFIG_DIR', PROJ)
COOKIE_FILE = os.path.join(CONFIG_DIR, 'bili_cookie.txt')

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
GENERATE_URL = 'https://passport.bilibili.com/x/passport-login/web/qrcode/generate'
POLL_URL = 'https://passport.bilibili.com/x/passport-login/web/qrcode/poll'


def generate_qrcode():
    """生成扫码登录二维码. 返回 {qrcode_key, qr_base64}."""
    import requests, qrcode, io, base64
    r = requests.get(GENERATE_URL, headers=HEADERS, timeout=15)
    d = r.json()
    if d.get('code') != 0:
        raise RuntimeError(f"生成二维码失败: {d}")
    qrcode_key = d['data']['qrcode_key']
    qr_url = d['data']['url']
    buf = io.BytesIO()
    qrcode.make(qr_url).save(buf, format='PNG')
    qr_b64 = base64.b64encode(buf.getvalue()).decode()
    return {'qrcode_key': qrcode_key, 'qr_base64': f'data:image/png;base64,{qr_b64}'}


def poll_login_status(qrcode_key):
    """查扫码状态(单次). 返回 {code, logged_in, message, dede_user_id}."""
    import requests
    r = requests.get(POLL_URL, params={'qrcode_key': qrcode_key}, headers=HEADERS, timeout=15)
    d = r.json()
    code = d.get('data', {}).get('code', -1)
    msg = d.get('data', {}).get('message', '')
    if code == 0:
        cookies = dict(r.cookies)
        if 'SESSDATA' in cookies:
            save_cookie(cookies)
            return {'code': 0, 'logged_in': True, 'message': '登录成功',
                    'dede_user_id': cookies.get('DedeUserID', '')}
        return {'code': 0, 'logged_in': False, 'message': 'cookie提取失败'}
    return {'code': code, 'logged_in': False, 'message': msg}


def save_cookie(cookies):
    """保存cookie到文件."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    keys = ['SESSDATA', 'bili_jct', 'DedeUserID', 'DedeUserID__ckMd5']
    parts = [f"{k}={cookies[k]}" for k in keys if k in cookies and cookies[k]]
    with open(COOKIE_FILE, 'w', encoding='utf-8') as f:
        f.write('; '.join(parts))


def get_cookie_str():
    """读取已保存的cookie字符串, 没有返回None."""
    if os.path.exists(COOKIE_FILE):
        with open(COOKIE_FILE, 'r', encoding='utf-8') as f:
            c = f.read().strip()
            return c if c else None
    return None


def is_logged_in():
    """是否已登录(cookie存在且含SESSDATA)."""
    c = get_cookie_str()
    return bool(c and 'SESSDATA=' in c and len(c) > 50)
