# 前端皮肤系统文档

> 2026-07-30 定稿 | React + antd v5 + Vite

## 皮肤清单 (6套, 已定稿)

| ID | 名称 | 色系 | 色调 |
|---|---|---|---|
| `sunrise` | 晨曦 | 淡色 | 琥珀橙 (默认) |
| `peach` | 蜜桃 | 淡色 | 玫瑰粉 |
| `tokiwadai` | 常盘台 | 淡色 | 校服米棕 (二次元, 带电磁炮装饰) |
| `dusk` | 暮色 | 暗色 | 暖棕琥珀 |
| `ember` | 熔岩 | 暗色 | 橙红 |
| `railgun` | 电磁炮 | 暗色 | 电光蓝+金币 (二次元, 带电磁炮装饰) |

## 如何新增皮肤

只需在 `web/src/theme/skins.ts` 的 `SKINS` 数组追加一条配置, 无需改任何组件:

```ts
{
  id: 'myskin',           // 唯一ID
  name: '我的皮肤',        // 切换器显示名
  mode: 'light',          // 'light' | 'dark' (决定antd algorithm)
  preview: 'linear-gradient(135deg,#aaa,#bbb)',  // 切换器预览圆点
  deco: 'orbs',           // 背景装饰: 'orbs'(光斑) | 'railgun'(电磁炮电弧+金币)
  vars: { /* CSS变量: --skin-bg/--glass-bg/--accent/--accent-gradient 等, 参考现有皮肤 */ },
  antd: { token: { colorPrimary: '#xxx', ... } },
}
```

皮肤选择自动持久化 (localStorage `bili-skin`), 淡/暗快速切换会记住各色系最后用的皮肤.

## 架构

```
web/src/
├── theme/
│   ├── skins.ts           # ⭐皮肤注册表 (唯一真值)
│   └── ThemeContext.tsx   # Provider: CSS变量注入 + antd ConfigProvider + localStorage
├── components/
│   ├── SkinSwitcher.tsx   # 右上角切换器 (日月快速切换 + 皮肤下拉)
│   ├── RailgunDeco.tsx    # 电磁炮装饰 (原创SVG电弧/金币/火花, 无版权素材)
│   ├── InfoPanel.tsx      # 状态窗口 (封面/UP主/统计/下载状态)
│   └── DirBrowserModal.tsx # 服务器目录浏览对话框
```

## SD绘画素材 (已接入, 2026-07-30)

本机秋葉SD WebUI (`D:\Drawing\sd-webui-aki-v4.7`) 生成, 启动API:
```
cd D:\Drawing\sd-webui-aki-v4.7 && python\python.exe launch.py --api --port 7860
```
- 生成脚本: `tools/sd_gen_assets.py` (模型animagineXLV3, **SDXL必须设 `[XL]sdxl_vae.safetensors`, 否则花屏**)
- 素材: `web/public/skins/<skin-id>/{bg,mascot}.png` (+ .meta.json 存prompt/seed可复现)
- 皮肤配置: `bgImage`(背景, `bgImageOpacity`调不透明度) + `mascot`(右下角立绘, <1100px隐藏)
- 已生成: railgun(夜空都市电弧+Q版茶发少女) / tokiwadai(银杏长廊+Q版校服少女)
- 角色为原创设计, 无版权素材, 可发GitHub

### 用户画作素材 (2026-07-30晚, 替换部分SD素材)

用户自己的画放 `pic/`(不提交git), 挑选后转webp进 `web/public/skins/`:
- railgun/mascot = ca9cb1a9 光翼美琴指前方(深蓝夜空+金光翼, 和电弧配色一体)
- tokiwadai/mascot = 835275ee 冷脸校服美琴(城市背景, 成熟画风)
- sapphire/bg = du_q90_hm.jpeg 青蓝巨浪灯塔(注意同名 .jfif 是帆船峡谷, 别搞混)
- `bgPosition` 字段控制背景定位(竖版图用 'center 30%')
- ⚠️本session教训: Read工具多次把图片显示错位/张冠李戴, 看大图挑素材必须用"文件名烧进画面"的contact sheet(`shots/pic_contact_sheet.jpg`), 或MSE对拍验证 webp==源文件

## 截图工具

`tools/ui_screenshot.py` — Edge headless + CDP, 支持注入JS/设localStorage/整页截图:

```bash
python tools/ui_screenshot.py "http://127.0.0.1:8001" out.png \
  --js tools/_shot_parse_action.js --wait 3 --fullpage --set-ls bili-skin=railgun
```
