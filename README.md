# B站充电视频下载器

下载B站**充电专属视频完整版**，支持 **UGC合集批量下载**，带 **Web前端**（扫码登录 + 选集下载 + 实时进度），可 **Docker部署**（Unraid兼容）。

> 解决 [BBDown](https://github.com/nilaoda/BBDown) 1.6.3 登录失效问题：B站改版后 `BBDown login` 假成功（SESSDATA 永远为空），本工具直接调用B站扫码登录 API，从 `Set-Cookie` 响应头提取 cookie，再用 BBDown 下载充电视频完整版。

## 功能

- ✅ **充电视频完整下载**：扫码登录后下载充电专属视频完整版（非5分钟试看），1080P
- ✅ **UGC合集批量下载**：自动获取合集全部视频，逐个下载
- ✅ **Web前端**：浏览器操作，扫码登录 + 链接解析 + 复选框选集（默认全选）+ 路径选择 + 实时进度
- ✅ **Docker部署**：一键容器化，Unraid 模板支持
- ✅ **文件名带发布日期**：`视频标题_2026-07-29_20-16-56.mp4`
- ✅ **断点续传**：按 aid 记录已下载视频

## 快速开始

### 方式一：Docker（推荐）

```bash
docker run -d \
  --name bili-downloader \
  -p 8000:8000 \
  -v $(pwd)/config:/config \
  -v $(pwd)/downloads:/downloads \
  --restart unless-stopped \
  ghcr.io/montrush/bilibili-charging-downloader:latest
```

或用 docker-compose：
```bash
docker compose up -d
```

启动后访问 `http://localhost:8000`。

### 方式二：Unraid 部署

1. Unraid -> Apps -> 搜索 `bilibili-charging-downloader`（或手动添加模板）
2. 设置 WebUI端口、配置目录(`/mnt/user/appdata/bili-downloader`)、下载目录
3. 安装后访问 `http://<Unraid-IP>:8000`

> 模板文件：`unraid/bilibili-charging-downloader.xml`

### 方式三：Windows 原生运行（无需Docker）

1. 安装 [Python 3.8+](https://python.org)、[Node.js 20+](https://nodejs.org)、[ffmpeg](https://ffmpeg.org)
2. 下载 [BBDown.exe](https://github.com/nilaoda/BBDown/releases) 放到项目根目录
3. 双击运行 `run_windows.bat`

### 方式四：开发模式

```bash
# 后端
pip install -r server/requirements.txt
python -m uvicorn server.main:app --port 8000 --reload

# 前端(另一个终端)
cd web
npm install
npm run dev    # http://localhost:5173 (代理到8000)
```

## 使用说明

1. **扫码登录**：打开 WebUI，用手机B站APP扫描页面二维码并确认登录
   - ⚠️ 必须用**已充电的B站账号**，否则充电视频仍只能下试看
2. **粘贴链接**：在输入框粘贴B站链接（`b23.tv/xxx`、BV号、合集链接）
3. **解析**：点击解析按钮，自动列出合集所有视频
4. **选集**：复选框选择要下载的视频（默认全选），可全选/全不选
5. **下载**：设置下载路径，点击下载按钮，实时查看进度

## 工作原理

### 登录（解决BBDown bug）

```
B站扫码登录 poll API 返回 code=0 时:
  data.url  -> 只含 ticket (BBDown 1.6.3 从这里解析, 永远空)
  Set-Cookie -> 含 SESSDATA等cookie (本工具从这里提取)
```

本工具用 Python `requests` 的 `r.cookies`（自动解析 Set-Cookie 响应头）提取 cookie，这是 BBDown 1.6.3 没跟上的地方。

### 合集下载

BBDown 1.6.3 不认合集 URL，本工具用 B站 API `ugc_season` 获取全部 aid + pubdate，逐个调用 BBDown 下载。

## 项目结构

```
├── server/                 # FastAPI后端
│   ├── main.py            # API应用
│   ├── routers/           # login/parse/download路由
│   ├── services/          # bili_auth(登录) + bili_dl(解析下载)
│   └── task_manager.py    # 下载任务管理(后台线程+进度)
├── web/                    # React前端(Ant Design)
│   ├── src/pages/         # LoginPage + DownloadPage
│   └── dist/              # 构建产物
├── Dockerfile             # Linux Docker(Unraid兼容)
├── docker-compose.yml
├── run_windows.bat        # Windows原生运行
├── unraid/                # Unraid部署模板
├── .github/workflows/     # CI: 自动构建Docker镜像到GHCR
├── bili_login.py          # 命令行版登录(独立使用)
├── bili_download.py       # 命令行版下载(独立使用)
└── requirements.txt       # 命令行版依赖
```

## 常见问题

**Q: 下载的充电视频只有5分钟？**
A: cookie没生效。检查：1)是否扫码登录成功；2)登录的账号是否已给UP主充电；3)cookie是否过期（重新扫码）。

**Q: Docker里下载的视频在哪？**
A: 在挂载的 `/downloads` 目录（docker-compose.yml 里映射到 `./downloads`）。

**Q: Unraid上BBDown/ffmpeg需要单独装吗？**
A: 不需要，Docker镜像已内置。

**Q: 合集只下了1集？**
A: 不会，本工具自动获取合集全部视频。用"解析"按钮先看合集结构。

## 致谢

- [BBDown](https://github.com/nilaoda/BBDown) - B站下载引擎
- [Ant Design](https://ant.design) - 前端UI组件

## License

MIT
