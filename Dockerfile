# B站充电视频下载器 - Linux Docker (Unraid兼容)
FROM python:3.10-slim

# ffmpeg + 依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg curl unzip ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 下载 BBDown Linux版 (多架构: amd64/arm64)
ARG TARGETARCH
ARG BBDOWN_VERSION=1.6.3
ARG BBDOWN_DATE=20240814
RUN set -eux; \
    case "$TARGETARCH" in \
      amd64) arch=x64 ;; \
      arm64) arch=arm64 ;; \
      *) echo "unsupported arch: $TARGETARCH"; exit 1 ;; \
    esac; \
    curl -fL -o /tmp/bbdown.zip \
      "https://github.com/nilaoda/BBDown/releases/download/${BBDOWN_VERSION}/BBDown_${BBDOWN_VERSION}_${BBDOWN_DATE}_linux-${arch}.zip" \
    && unzip /tmp/bbdown.zip -d /tmp/bbdown \
    && mv /tmp/bbdown/BBDown /usr/local/bin/BBDown \
    && chmod +x /usr/local/bin/BBDown \
    && rm -rf /tmp/bbdown /tmp/bbdown.zip \
    && ls -la /usr/local/bin/BBDown

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
