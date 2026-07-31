# B站充电视频下载器

下载B站**充电专属视频完整版**，支持 **UGC合集批量下载**，带高颜值 **Web前端**（扫码登录 + 选集下载 + 7套皮肤），提供 **Windows安装包 / Linux安装包 / Docker**（Unraid兼容）三种使用方式。

**免代理国内友好**：应用内一键自动更新（GitHub / Gitee / 加速镜像多通道自动切换），安装包也可从 [Gitee 发布页](https://gitee.com/houplus/bilibili-charging-downloader/releases) 直接下载。

> 解决 [BBDown](https://github.com/nilaoda/BBDown) 1.6.3 登录失效问题：B站改版后 `BBDown login` 假成功（SESSDATA 永远为空），本工具直接调用B站扫码登录 API，从 `Set-Cookie` 响应头提取 cookie，再用 BBDown 下载充电视频完整版。

> 🇨🇳 国内镜像：[Gitee 仓库](https://gitee.com/houplus/bilibili-charging-downloader)（与 GitHub 自动同步）

![电磁炮皮肤](docs/screenshots/pc_railgun.png)

## 功能

- ✅ **充电视频完整下载**：扫码登录后下载充电专属视频完整版（非5分钟试看），1080P
- ✅ **UGC合集批量下载**：自动获取合集全部视频，表格复选（默认全选），单集/整合集两种解析模式
- ✅ **暂停/继续 + 断点续传**：下载中可随时暂停/继续；下载目录里的 `.bili_dl_task.json` 记录进度，断网、关闭应用后，相同链接+相同目录再次下载自动接着传
- ✅ **并行任务队列**：可同时下载多个合集，标题栏「任务」面板集中管理（暂停/继续/删除）；并行任务数可调（1-5）；应用重启后未完成任务保留，可手动续接或勾选"启动后自动续接"
- ✅ **应用内自动更新（免代理）**：标题栏「更新」按钮一键升级并自动重启。更新通道自动降级：GitHub → Gitee（国内）→ 加速镜像，无需代理；也可在弹窗里填自定义代理
- ✅ **高颜值Web前端**：7套皮肤（晨曦/蜜桃/常盘台/暮色/熔岩/电磁炮/曜蓝），玻璃拟态，手机端自适应
- ✅ **目录设置**：可视化目录浏览器，按 `UP主/合集名` 自动建子目录（qBittorrent风格）
- ✅ **实时进度**：状态窗口显示封面/UP主/统计数据/下载进度
- ✅ **文件名带发布日期**：`视频标题_2026-07-29_20-16-56.mp4`
- ✅ **端口自选**：启动时可改 Web 端口（默认 8000，被占用自动提醒），零命令行基础也能用

![解析合集](docs/screenshots/pc_parsed.png)

## 快速开始

### 方式一：Windows 安装包（推荐，开箱即用）

1. 下载 `BiliDownloader-Setup-x.x.x-win-x64.exe`：[GitHub Releases](https://github.com/montrush/bilibili-charging-downloader/releases/latest) | [Gitee 发布页（国内快）](https://gitee.com/houplus/bilibili-charging-downloader/releases)
2. 安装后从开始菜单启动，启动窗口会提示选择端口（默认 8000，直接回车即可；被占用时会提醒换一个），随后自动打开浏览器
3. 无需安装 Python/Node/ffmpeg/BBDown，安装包已全部内置

> 也有免安装便携版 `BiliDownloader-portable-x.x.x-win-x64.zip`，解压即用（仅 GitHub，文件超过 Gitee 100MB 附件上限）。

### 方式二：Linux 安装包

```bash
# Debian / Ubuntu 系
sudo dpkg -i bili-downloader_x.x.x_amd64.deb
bili-downloader        # 启动时会提示选端口(默认8000回车即可), 然后访问 http://127.0.0.1:8000
```

其他发行版下载 `bili-downloader_x.x.x_linux-x64.tar.gz` 解压运行，或用下面的 Docker。

### 方式三：Docker（NAS / 服务器）

```bash
docker run -d \
  --name bili-downloader \
  -p 8000:8000 \
  -v $(pwd)/config:/config \
  -v $(pwd)/downloads:/downloads \
  --restart unless-stopped \
  ghcr.io/montrush/bilibili-charging-downloader:latest
```

启动后访问 `http://localhost:8000`。也支持 `docker compose up -d`。

### 方式四：Unraid 部署

1. Unraid -> Apps -> 搜索 `bilibili-charging-downloader`（或手动添加模板）
2. 设置 WebUI端口、配置目录(`/mnt/user/appdata/bili-downloader`)、下载目录
3. 安装后访问 `http://<Unraid-IP>:8000`

> 模板文件：`unraid/bilibili-charging-downloader.xml`

## 使用说明

1. **扫码登录**：打开 WebUI，用手机B站APP扫描页面二维码并确认登录（cookie 有效期间下次启动自动跳过扫码）
   - ⚠️ 必须用**已充电的B站账号**，否则充电视频仍只能下试看
2. **粘贴链接**：支持 `b23.tv/xxx` 短链、BV号、合集链接、专栏、动态
3. **解析模式**：输入框下方开关 —「单集」只下当前集，「整个合集」展开全合集
4. **选集**：复选框选择（默认全选），分页大小 20/50/100/200 可调
5. **下载**：设置下载路径（默认 `下载目录/UP主/合集名/`），实时查看进度，可随时**暂停/继续**
6. **更新**：标题栏「更新」按钮，有新版本时显示红点，一键自动升级

![常盘台皮肤](docs/screenshots/pc_tokiwadai.png)

## 自动更新说明

| 安装方式 | 更新方式 |
|---|---|
| Windows 安装版 / 便携版 | ✅ 一键自动更新（下载→静默安装→自动重启） |
| Linux tar.gz | ✅ 一键自动更新 |
| Linux deb / Docker | 提示手动更新（deb 用新包重装；Docker 重新拉取镜像） |

更新通道（自动逐层降级，全部失败才提示手动）：

```
版本检查: GitHub API → Gitee API → jsDelivr CDN
下载包:   当前可用通道 → GitHub 直连 → Gitee 附件 → 加速镜像(ghfast.top / gh-proxy.com / ghproxy.net)
```

下载完成有文件大小校验防镜像篡改。代理用户可在更新弹窗中填写代理地址（如 `127.0.0.1:7890`），检查和下载都会走它。

## 环境变量（进阶）

| 变量 | 默认 | 说明 |
|---|---|---|
| `BILI_PORT` | `8000` | Web服务端口。设置后跳过启动时的交互选端口（脚本/CI场景） |
| `BILI_CONFIG_DIR` | 各平台配置目录 | cookie/登录态存放位置 |
| `BILI_DOWNLOAD_DIR` | 项目下 `downloads` | 默认下载目录 |
| `HTTPS_PROXY` | 无 | 标准代理变量，检查更新/下载更新包时会使用 |

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

### 断点续传

每个下载任务在目标目录维护 `.bili_dl_task.json`（原子写入），记录任务列表/已完成/失败。全部成功后自动删除；有失败则保留，下次相同链接+相同目录下载时自动跳过已完成、重试失败。

### 并行任务队列

配置目录下的 `download_tasks.json` 是所有任务的注册表（排队/下载中/已暂停/已完成），`download_settings.json` 存队列设置。调度器按"并行任务数"分配槽位：任务数超限时排队，有任务完成/暂停后自动补位。应用重启时，下载中/排队的任务标记为"已暂停"，在「任务」面板手动继续；勾选"启动后自动续接"则重启后自动全部开跑。对相同下载目录再次发起下载会合并进已有任务而不是新建。

## 项目结构

```
├── server/                 # FastAPI后端
│   ├── main.py            # API应用(静态托管前端dist)
│   ├── version.py         # 版本号(CI发布时用tag注入)
│   ├── routers/           # login/parse/download/fs/update路由
│   ├── services/          # bili_auth(登录) + bili_dl(解析下载)
│   └── task_manager.py    # 并行任务队列(注册表+调度器+暂停/继续+断点续传)
├── web/                    # React前端(Ant Design 5 + Vite)
│   ├── src/theme/skins.ts # 7套皮肤注册表
│   └── src/pages/         # LoginPage + DownloadPage
├── packaging/              # 安装包打包(PyInstaller spec/Inno Setup/deb/启动器)
├── Dockerfile             # Linux Docker(Unraid兼容)
├── docker-compose.yml
├── run_windows.bat        # Windows原生运行(开发用)
├── unraid/                # Unraid部署模板
├── .github/workflows/     # CI: Docker镜像(GHCR) + Release安装包 + Gitee同步
├── bili_login.py          # 命令行版登录(独立使用)
└── bili_download.py       # 命令行版下载(独立使用)
```

## 开发模式

```bash
# 后端
pip install -r server/requirements.txt
python -m uvicorn server.main:app --port 8000 --reload

# 前端(另一个终端)
cd web
npm install
npm run dev    # http://localhost:5173 (代理到8000)
```

## 常见问题

**Q: 下载的充电视频只有5分钟？**
A: cookie没生效。检查：1)是否扫码登录成功；2)登录的账号是否已给UP主充电；3)cookie是否过期（重新扫码）。

**Q: 国内没有代理，怎么下载安装包 / 更新？**
A: 安装包去 [Gitee 发布页](https://gitee.com/houplus/bilibili-charging-downloader/releases)（国内直连快）。应用内更新不用管——「更新」按钮会自动切到 Gitee 或加速镜像通道。

**Q: 下载到一半断网/手滑关了应用怎么办？**
A: 什么都不用做。重新打开应用，粘贴相同链接、选相同目录再下载，会自动跳过已完成的集接着传（进度存在下载目录的 `.bili_dl_task.json` 里）。

**Q: Docker里下载的视频在哪？**
A: 在挂载的 `/downloads` 目录（docker-compose.yml 里映射到 `./downloads`）。

**Q: 端口8000被占用？**
A: Windows/Linux 安装版启动时会先让你选端口，8000 被占用会直接提醒，输入别的端口（如 8001）回车即可。也可以提前设环境变量 `BILI_PORT=8001` 跳过询问。Docker 则改端口映射 `-p 8001:8000`。

**Q: 合集只下了1集？**
A: 不会，本工具自动获取合集全部视频。粘贴单集链接默认「单集」模式，点「整个合集」展开。

## 致谢

- [BBDown](https://github.com/nilaoda/BBDown) - B站下载引擎 (MIT)
- [ffmpeg](https://ffmpeg.org) - 音视频合成 (LGPL/GPL)
- [Ant Design](https://ant.design) - 前端UI组件
- 皮肤美术素材为 Stable Diffusion 生成及作者自绘

## License

MIT（第三方组件许可见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)）
