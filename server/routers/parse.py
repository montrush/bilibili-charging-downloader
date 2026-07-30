# -*- coding: utf-8 -*-
"""解析API: 链接 -> 合集/视频信息."""
from fastapi import APIRouter
from pydantic import BaseModel
from ..services import bili_dl, bili_auth

router = APIRouter(prefix='/api', tags=['parse'])


class ParseRequest(BaseModel):
    url: str


@router.post('/parse')
def parse_link(req: ParseRequest):
    """解析B站链接, 返回视频信息+合集结构(含可勾选视频列表)."""
    aid = bili_dl.parse_aid(req.url)
    if not aid:
        return {'ok': False, 'error': '无法解析链接, 请检查URL'}
    cookie = bili_auth.get_cookie_str()
    info = bili_dl.get_video_info(aid, cookie)
    if not info:
        return {'ok': False, 'error': '视频不存在或已删除'}
    return {'ok': True, 'data': info}
