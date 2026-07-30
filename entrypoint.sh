#!/bin/sh
# B站下载器 Docker入口
mkdir -p /config /downloads
cd /app
echo "=== B站充电视频下载器启动 ==="
echo "cookie目录: /config"
echo "下载目录: /downloads"
echo "访问: http://<服务器IP>:8000"
exec python -m uvicorn server.main:app --host 0.0.0.0 --port 8000
