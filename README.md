# B站充电视频下载器

下载B站**充电专属视频完整版**，支持 **UGC合集批量下载**，文件名自带发布日期。

> 解决 [BBDown](https://github.com/nilaoda/BBDown) 1.6.3 登录失效问题：B站改版后 `BBDown login` 假成功（SESSDATA 永远为空），本工具直接调用B站扫码登录 API，从 `Set-Cookie` 响应头提取 cookie，再用 BBDown 下载充电视频完整版。

## 背景

[BBDown](https://github.com/nilaoda/BBDown) 是优秀的B站下载工具，但 1.6.3（2024-08-14，已停更）存在登录 bug：

- B站扫码登录的 `poll` 接口返回 `code=0` 时，cookie 现在通过 **`Set-Cookie` 响应头**下发
- 而 `data.url` 里**不再包含** `SESSDATA` 等字段（只有 `ticket`）
- BBDown 1.6.3 只从 `data.url` 解析 cookie → 永远拿不到 SESSDATA → 报"登录成功"但实际未登录
- 未登录下载充电视频只能拿到 **5分钟试看片段**（720P），而非完整视频（1080P）

本工具绕过 BBDown 的 login，直接调B站 API 完成扫码登录，提取 cookie 后传给 BBDown 下载。

## 功能

- ✅ **充电视频完整下载**：扫码登录后下载充电专属视频的完整版（非5分钟试看）
- ✅ **UGC合集批量下载**：自动获取合集全部视频，逐个下载（BBDown 1.6.3 不认合集 URL，本工具用 API 取 aid 列表）
- ✅ **文件名带发布日期**：`视频标题_2026-07-29_20-16-56.mp4`
- ✅ **断点续传**：按 aid 记录已下载视频，中断后可接着跑
- ✅ **二维码登录**：生成二维码图片，手机扫码即可，无需手动复制 cookie

## 安装

### 1. 下载 BBDown

从 [BBDown Releases](https://github.com/nilaoda/BBDown/releases) 下载 `BBDown.exe`（Windows）或对应平台版本，放到本项目目录，或加入系统 PATH。

### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

需要 Python 3.8+，依赖：`requests`、`qrcode`、`Pillow`。

### 3. 确认 ffmpeg 可用（可选但推荐）

BBDown 合并视频/音频需要 ffmpeg。确认 `ffmpeg` 在 PATH 中：

```bash
ffmpeg -version
```

没有的话从 [ffmpeg.org](https://ffmpeg.org/download.html) 下载。

## 使用

### 第一步：扫码登录（一次性）

```bash
python bili_login.py
```

- 生成 `bilibili_qr.png` 二维码图片
- **双击打开**该图片，用**手机B站APP**扫码 → 点"确认登录"
- 登录成功后 cookie 自动保存到 `bili_cookie.txt`
- ⚠️ 二维码 3 分钟过期，过期重跑即可
- ⚠️ 必须用**已充电的B站账号**登录，否则充电视频仍只能下试看

### 第二步：下载视频

```bash
# 下载整个合集（自动获取全部集数，逐个下载）
python bili_download.py https://b23.tv/xxxxx

# 只看合集信息不下载（确认集数/清晰度）
python bili_download.py https://b23.tv/xxxxx --info

# 下载单视频指定集
python bili_download.py https://b23.tv/xxxxx -p 1,2,3

# 指定cookie文件
python bili_download.py https://b23.tv/xxxxx --cookie /path/to/cookie.txt
```

视频输出到 `downloads/` 目录，文件名格式：`视频标题_2026-07-29_20-16-56.mp4`

## 工作原理

### 登录流程（`bili_login.py`）

```
1. GET /x/passport-login/web/qrcode/generate  → 获取 qrcode_key + 二维码URL
2. qrcode 库生成二维码图片
3. 轮询 GET /x/passport-login/web/qrcode/poll?qrcode_key=xxx
   - code=86101 未扫码
   - code=86090 已扫码未确认
   - code=0    登录成功 ← cookie在Set-Cookie响应头!
4. 从 r.cookies 提取 SESSDATA/bili_jct/DedeUserID，保存为cookie字符串
```

关键点：B站改版后 `data.url` 只含 `ticket`，真正的 cookie 在 **`Set-Cookie` 响应头**里。本工具用 `requests` 的 `r.cookies` 自动解析响应头，这是 BBDown 1.6.3 没跟上的地方。

### 合集下载流程（`bili_download.py`）

```
1. 解析短链 → aid
2. GET /x/web-interface/view?aid=xxx → 获取视频信息 + ugc_season
3. 从 ugc_season.sections.episodes 提取全部 aid + pubdate
4. 逐个调用 BBDown av$aid -c cookie -F "<videoTitle>_<videoDate>"
5. 按 aid 记录已下载（断点续传）
```

BBDown 1.6.3 不认 `medialist/mlxxx` 合集 URL（报 `Arg_KeyNotFound`），也不认 UP主空间 URL，所以用 API 取 aid 列表逐个下载。

## 常见问题

**Q: 下载的充电视频只有5分钟？**
A: cookie 没生效。检查：1) `bili_cookie.txt` 是否存在且 `SESSDATA` 非空；2) 登录的B站账号是否已给UP主充电；3) 重新跑 `bili_login.py`。

**Q: `bili_login.py` 显示登录成功但 SESSDATA 为空？**
A: 不应该出现。本工具从 `Set-Cookie` 响应头提取（不依赖 `data.url`）。如果仍为空，检查网络或B站API是否再次变更。

**Q: 合集只下了1集？**
A: 用 `--info` 先确认合集结构。本工具会自动下载合集全部视频。

**Q: 文件名里的日期是什么？**
A: 视频发布日期时间，格式 `YYYY-MM-DD_HH-MM-SS`，由 BBDown 的 `<videoDate>` 占位符生成。

**Q: BBDown 报 "未登录B站账号"？**
A: 这是 BBDown 自己的 login 没成功（已知 bug），不影响下载。只要 `bili_cookie.txt` 有效，本工具会用 `-c` 参数传 cookie 给 BBDown，充电视频能正常下载。

## 文件说明

| 文件 | 说明 |
|------|------|
| `bili_login.py` | 扫码登录，生成 cookie（核心：从 Set-Cookie 提取） |
| `bili_download.py` | 下载视频/合集，调用 BBDown + cookie |
| `bili_cookie.txt` | 登录态（**gitignore，勿提交**） |
| `bilibili_qr.png` | 登录二维码（**gitignore**） |
| `downloads/` | 视频输出目录（**gitignore**） |
| `download_done.txt` | 已下载 aid 记录，断点续传（**gitignore**） |

## 致谢

- [BBDown](https://github.com/nilaoda/BBDown) - 强大的B站下载工具，本项目基于它下载视频
- B站扫码登录 API

## License

MIT
