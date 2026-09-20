# -*- coding: utf-8 -*-
"""解析API: 链接 -> 合集/视频/文章/图片信息."""
from fastapi import APIRouter
from pydantic import BaseModel
from ..services import bili_dl, bili_auth

router = APIRouter(prefix='/api', tags=['parse'])


class ParseRequest(BaseModel):
    url: str


@router.post('/parse')
def parse_link(req: ParseRequest):
    """解析B站链接, 返回视频/合集/文章/图片信息."""
    cookie = bili_auth.get_cookie_str()
    data = bili_dl.parse_link(req.url, cookie)
    if not data:
        return {'ok': False, 'error': '无法解析链接, 请检查URL'}
    if data.get('link_type') in ('article', 'image'):
        return {'ok': True, 'data': data, 'message': data.get('message', '')}
    if data.get('link_type') == 'unknown':
        return {'ok': False, 'error': '无法识别的链接类型'}
    if not data.get('aid') and not data.get('is_collection'):
        return {'ok': False, 'error': '链接类型已识别，但无法获取详情'}
    return {'ok': True, 'data': data}


@router.post('/parse/collection')
def parse_collection(req: ParseRequest):
    """下载合集: 从任意一集视频链接展开所属合集(全部剧集).

    视频不属于任何合集时返回错误提示.
    """
    cookie = bili_auth.get_cookie_str()
    data = bili_dl.parse_link(req.url, cookie)
    if not data:
        return {'ok': False, 'error': '无法解析链接, 请检查URL'}
    if data.get('is_collection') and data.get('collection'):
        data['link_type'] = 'collection'
        n = len(data['collection'].get('episodes', []))
        return {'ok': True, 'data': data, 'message': f'已展开合集，共 {n} 集'}
    if data.get('link_type') in ('article', 'image', 'unknown'):
        return {'ok': False, 'error': '该链接不是视频，无法展开合集'}
    return {'ok': False, 'error': '该视频不属于任何合集'}


@router.post('/parse/space')
def parse_space(req: ParseRequest):
    """按UP主下载: space.bilibili.com/{mid}/upload/video -> 全部投稿(默认全选, 前端可取消勾选).

    v1.0.11用户令: 例如 https://space.bilibili.com/1039025435/upload/video
    """
    mid = bili_dl.extract_mid(req.url) or (req.url.strip() if req.url.strip().isdigit() else '')
    if not mid or not str(mid).isdigit():
        return {'ok': False, 'error': '无法识别UP主空间链接, 请粘贴形如 https://space.bilibili.com/{数字ID}/upload/video 的链接'}
    cookie = bili_auth.get_cookie_str()
    data = bili_dl.fetch_space_videos(mid, cookie)
    if not data:
        return {'ok': False, 'error': '获取UP主投稿列表失败(接口错误或无投稿); 未登录扫码后再试可提高成功率'}
    owner = data.get('owner') or {}
    return {'ok': True, 'data': {
        'link_type': 'space',
        'owner': owner.get('name', f'UP主{mid}'),
        'owner_mid': int(mid),
        'owner_face': owner.get('face', ''),
        'title': f'{owner.get("name", "")} 的全部投稿'.strip(),
        'pic': data.get('videos', [{}])[0].get('pic', '') if data.get('videos') else '',
        'desc': owner.get('sign', ''),
        'total': data.get('total', 0),
        'videos': data.get('videos', []),
        'raw_url': req.url,
        'resolved_url': f'https://space.bilibili.com/{mid}/upload/video',
    }, 'message': f'已展开UP主投稿, 共 {data.get("total", 0)} 个视频, 默认全选'}
