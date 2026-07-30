# B站充电视频下载器 - Linux Docker (Unraid兼容)
FROM python:3.10-slim

# ffmpeg + 依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg curl unzip ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 下载 BBDown Linux版
ARG BBDOWN_VERSION=1.6.3
RUN curl -L -o /tmp/bbdown.zip \
    "https://github.com/nilaoda/BBDown/releases/download/v${BBDOWN_VERSION}/BBDown_${BBDOWN_VERSION}_linux_x64.zip" \
    && unzip /tmp/bbdown.zip -d /tmp/bbdown \
    && mv /tmp/bbdown/BBDown /usr/local/bin/BBDown \
    && chmod +x /usr/local/bin/BBDown \
    && rm -rf /tmp/bbdown /tmp/bbdown.zip \
    && BBDown --version

# Python依赖
COPY server/requirements.txt /app/server/requirements.txt
RUN pip install --no-cache-dir -r /app/server/requirements.txt

# 后端代码
COPY server/ /app/server/

# 前端构建产物(需先在web/跑 npm run build)
COPY web/dist/ /app/web/dist/

# BBDown.data 和 bili_cookie.txt 存到 /config (volume挂载)
ENV BILI_CONFIG_DIR=/config
ENV BILI_DOWNLOAD_DIR=/downloads

# 入口脚本
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

VOLUME ["/config", "/downloads"]

ENTRYPOINT ["/app/entrypoint.sh"]
