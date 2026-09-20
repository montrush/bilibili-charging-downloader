# -*- coding: utf-8 -*-
"""B站 WBI 签名 (v1.0.11: 按UP主下载全部投稿).

x/space/wbi/* 系接口自2023起强制 w_rid+wts 签名, 算法为公开的 mixin key 置换:
  1) GET /x/web-interface/nav (带cookie) → data.wbi_img.img_url/sub_url → 各取末段文件名为 img_key/sub_key
  2) mixin_key = ''.join((img_key+sub_key)[i] for i in MIXIN_TAB)[:32]
  3) 参数表加 wts=unix秒, 过滤 value 中 !'()* 字符, 按key排序 urlencode 后 + mixin_key 取 md5 = w_rid
key 每日轮换, 进程内缓存1小时; 签名失败(-403)时调用方可调 invalidate_wbi_keys() 后重试一次.
"""
import hashlib
import time
import urllib.parse

MIXIN_TAB = [46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
             33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40, 61,
             26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20,
             34, 44, 52]

_cache = {'mixin_key': None, 'ts': 0.0}
_TTL = 3600  # key每日轮换, 缓存1小时足够


def invalidate_wbi_keys():
    _cache['mixin_key'] = None
    _cache['ts'] = 0.0


def _get_mixin_key(headers):
    key = _cache.get('mixin_key')
    if key and time.time() - _cache['ts'] < _TTL:
        return key
    import requests
    r = requests.get('https://api.bilibili.com/x/web-interface/nav', headers=headers, timeout=15)
    d = r.json()
    wbi = (d.get('data') or {}).get('wbi_img') or {}
    img = (wbi.get('img_url') or '').rsplit('/', 1)[-1].split('.')[0]
    sub = (wbi.get('sub_url') or '').rsplit('/', 1)[-1].split('.')[0]
    if not img or not sub:
        return None
    raw = img + sub
    key = ''.join(raw[i] for i in MIXIN_TAB if i < len(raw))[:32]
    _cache['mixin_key'] = key
    _cache['ts'] = time.time()
    return key


def sign_wbi(params: dict, headers: dict) -> dict:
    """给参数表加 w_rid/wts. 失败返回原表(调用方靠API错误码感知)."""
    try:
        mixin = _get_mixin_key(headers)
        if not mixin:
            return dict(params)
        p = {k: (''.join(ch for ch in str(v) if ch not in "!'()*")) for k, v in params.items()}
        p['wts'] = int(time.time())
        q = urllib.parse.urlencode(sorted(p.items()))
        p['w_rid'] = hashlib.md5((q + mixin).encode()).hexdigest()
        return p
    except Exception:
        return dict(params)
