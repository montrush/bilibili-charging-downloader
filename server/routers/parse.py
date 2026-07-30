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
