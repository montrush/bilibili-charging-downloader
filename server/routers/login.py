# -*- coding: utf-8 -*-
"""登录API: 扫码登录."""
from fastapi import APIRouter
from ..services import bili_auth

router = APIRouter(prefix='/api/login', tags=['login'])


@router.get('/check')
def check_login():
    """检查是否已登录."""
    return {'logged_in': bili_auth.is_logged_in()}


@router.post('/qrcode')
def gen_qrcode():
    """生成扫码登录二维码."""
    data = bili_auth.generate_qrcode()
    return data


@router.get('/status')
def login_status(qrcode_key: str):
    """查扫码状态(前端轮询)."""
    return bili_auth.poll_login_status(qrcode_key)
