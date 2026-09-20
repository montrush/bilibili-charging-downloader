# -*- coding: utf-8 -*-
"""B站充电视频下载器 - FastAPI后端."""
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from .routers import login, parse, download, fs, update
from .version import __version__

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(title='B站充电视频下载器', version=__version__)

# CORS(开发时前端单独跑)
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])


# ⭐v1.0.12(0920): index.html 禁缓存 — 应用更新后浏览器沿用旧页面(启发式缓存无过期头)导致
# "装了新版还是旧UI"(1.0.11实测: 安装包正确, 缓存旧JS). 哈希资源文件不受影响仍可长缓存.
@app.middleware('http')
async def _no_cache_html(request, call_next):
    resp = await call_next(request)
    ct = resp.headers.get('content-type', '')
    if 'text/html' in ct:
        resp.headers['Cache-Control'] = 'no-cache'
    return resp

# API路由
app.include_router(login.router)
app.include_router(parse.router)
app.include_router(download.router)
app.include_router(fs.router)
app.include_router(update.router)


@app.on_event('startup')
def _startup():
    # 加载任务注册表: 上次中断的任务转"已暂停"等待续接; 设置了自动续接则直接开跑
    from . import task_manager
    task_manager.init_on_startup()


@app.get('/api/health')
def health():
    return {'ok': True, 'msg': 'B站下载器后端运行中'}


# 前端静态文件(构建后; PyInstaller打包时由 BILI_WEB_DIST 指向内置目录)
web_dist = os.environ.get('BILI_WEB_DIST', os.path.join(PROJ, 'web', 'dist'))
if os.path.exists(web_dist):
    app.mount('/', StaticFiles(directory=web_dist, html=True), name='web')
