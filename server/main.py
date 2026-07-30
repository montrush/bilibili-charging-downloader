# -*- coding: utf-8 -*-
"""B站充电视频下载器 - FastAPI后端."""
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from .routers import login, parse, download

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(title='B站充电视频下载器', version='1.0.0')

# CORS(开发时前端单独跑)
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])

# API路由
app.include_router(login.router)
app.include_router(parse.router)
app.include_router(download.router)


@app.get('/api/health')
def health():
    return {'ok': True, 'msg': 'B站下载器后端运行中'}


# 前端静态文件(构建后)
web_dist = os.path.join(PROJ, 'web', 'dist')
if os.path.exists(web_dist):
    app.mount('/', StaticFiles(directory=web_dist, html=True), name='web')
