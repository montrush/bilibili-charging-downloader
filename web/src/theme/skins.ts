// 皮肤注册表 - 换肤接口的唯一真值.
// 未来新增皮肤: 在 SKINS 数组加一条配置即可, 无需改任何组件.
import type { ThemeConfig } from 'antd'

export interface Skin {
  id: string
  /** 显示名 */
  name: string
  /** 色系: 淡色 / 暗色 */
  mode: 'light' | 'dark'
  /** 切换器里的预览圆点 */
  preview: string
  /** 背景装饰类型 (默认orbs光斑; railgun=电磁炮电弧+金币) */
  deco?: 'orbs' | 'railgun'
  /** SD生成的背景图 (public/下的路径, 如 /skins/railgun/bg.webp) */
  bgImage?: string
  /** 背景图不透明度 (默认0.32) */
  bgImageOpacity?: number
  /** 背景图定位 (默认center, 竖版图用 'center 30%' 等) */
  bgPosition?: string
  /** 手机端专用背景图 (≤768px时替换bgImage, 适合竖版画) */
  bgImageMobile?: string
  /** 手机端背景不透明度 (默认沿用bgImageOpacity) */
  bgImageOpacityMobile?: number
  /** 手机端背景定位 (默认沿用bgPosition) */
  bgPositionMobile?: string
  /** SD生成的看板娘 (public/下的路径, 右下角立绘) */
  mascot?: string
  /** 注入到 :root 的 CSS 变量 */
  vars: Record<string, string>
  /** antd token 覆盖 (algorithm 由 mode 自动决定) */
  antd: ThemeConfig
}

export const SKINS: Skin[] = [
  {
    id: 'sunrise',
    name: '晨曦',
    mode: 'light',
    bgImageMobile: '/skins/sunrise/bg-mobile.webp',
    bgImageOpacityMobile: 0.2,
    bgPositionMobile: 'center 30%',
    preview: 'linear-gradient(135deg,#fbbf24,#f97316)',
    vars: {
      '--skin-bg': 'linear-gradient(155deg,#fff9f0 0%,#fdeed8 45%,#fef1e0 75%,#fff6ea 100%)',
      '--orb-1': 'radial-gradient(circle, rgba(251,146,60,.42), transparent 65%)',
      '--orb-2': 'radial-gradient(circle, rgba(252,211,77,.38), transparent 65%)',
      '--orb-3': 'radial-gradient(circle, rgba(251,113,133,.28), transparent 65%)',
      '--glass-bg': 'rgba(255,255,255,.90)',
      '--glass-border': 'rgba(255,255,255,.78)',
      '--glass-shadow': '0 8px 32px rgba(194,120,52,.14)',
      '--glass-hover-shadow': '0 12px 40px rgba(194,120,52,.20)',
      '--header-bg': 'rgba(255,250,242,.93)',
      '--table-header-bg': 'rgba(255,243,228,.85)',
      '--popup-bg': 'rgba(255,250,242,.96)',
      '--accent': '#f97316',
      '--accent-2': '#fbbf24',
      '--accent-gradient': 'linear-gradient(135deg,#fbbf24 0%,#f97316 55%,#ea580c 100%)',
      '--accent-glow': 'rgba(249,115,22,.35)',
      '--text-strong': '#3d2b1f',
    },
    antd: {
      token: {
        colorPrimary: '#f97316',
        colorInfo: '#f97316',
        colorLink: '#ea580c',
        colorTextBase: '#3d2b1f',
        colorBgBase: '#fdf3e3',
        borderRadius: 12,
      },
    },
  },
  {
    id: 'peach',
    name: '蜜桃',
    mode: 'light',
    bgImageMobile: '/skins/peach/bg-mobile.webp',
    bgImageOpacityMobile: 0.2,
    bgPositionMobile: 'center 30%',
    preview: 'linear-gradient(135deg,#fda4af,#f43f5e)',
    vars: {
      '--skin-bg': 'linear-gradient(155deg,#fff7f5 0%,#ffe9e4 50%,#fff1ec 100%)',
      '--orb-1': 'radial-gradient(circle, rgba(251,113,133,.36), transparent 65%)',
      '--orb-2': 'radial-gradient(circle, rgba(253,164,175,.34), transparent 65%)',
      '--orb-3': 'radial-gradient(circle, rgba(251,146,60,.26), transparent 65%)',
      '--glass-bg': 'rgba(255,255,255,.90)',
      '--glass-border': 'rgba(255,255,255,.78)',
      '--glass-shadow': '0 8px 32px rgba(210,90,90,.13)',
      '--glass-hover-shadow': '0 12px 40px rgba(210,90,90,.19)',
      '--header-bg': 'rgba(255,246,244,.93)',
      '--table-header-bg': 'rgba(255,236,232,.85)',
      '--popup-bg': 'rgba(255,246,244,.96)',
      '--accent': '#f43f5e',
      '--accent-2': '#fda4af',
      '--accent-gradient': 'linear-gradient(135deg,#fda4af 0%,#fb7185 50%,#f43f5e 100%)',
      '--accent-glow': 'rgba(244,63,94,.32)',
      '--text-strong': '#402022',
    },
    antd: {
      token: {
        colorPrimary: '#f43f5e',
        colorInfo: '#f43f5e',
        colorLink: '#e11d48',
        colorTextBase: '#402022',
        colorBgBase: '#fdecea',
        borderRadius: 12,
      },
    },
  },
  {
    id: 'dusk',
    name: '暮色',
    mode: 'dark',
    bgImageMobile: '/skins/dusk/bg-mobile.webp',
    bgImageOpacityMobile: 0.3,
    bgPositionMobile: 'center 30%',
    preview: 'linear-gradient(135deg,#fde68a,#b45309)',
    vars: {
      '--skin-bg': 'linear-gradient(155deg,#191009 0%,#231709 45%,#1b110b 100%)',
      '--orb-1': 'radial-gradient(circle, rgba(249,115,22,.22), transparent 65%)',
      '--orb-2': 'radial-gradient(circle, rgba(252,211,77,.13), transparent 65%)',
      '--orb-3': 'radial-gradient(circle, rgba(194,65,12,.18), transparent 65%)',
      '--glass-bg': 'rgba(43,30,18,.90)',
      '--glass-border': 'rgba(255,190,120,.14)',
      '--glass-shadow': '0 8px 32px rgba(0,0,0,.45)',
      '--glass-hover-shadow': '0 12px 40px rgba(0,0,0,.55)',
      '--header-bg': 'rgba(26,17,10,.93)',
      '--table-header-bg': 'rgba(62,44,26,.55)',
      '--popup-bg': 'rgba(36,24,14,.96)',
      '--accent': '#fbbf24',
      '--accent-2': '#fde68a',
      '--accent-gradient': 'linear-gradient(135deg,#fde68a 0%,#fbbf24 45%,#f59e0b 100%)',
      '--accent-glow': 'rgba(251,191,36,.30)',
      '--text-strong': '#f3e7d8',
    },
    antd: {
      token: {
        colorPrimary: '#fbbf24',
        colorInfo: '#fbbf24',
        colorLink: '#fcd34d',
        colorTextBase: '#f3e7d8',
        colorBgBase: '#1b120b',
        borderRadius: 12,
      },
    },
  },
  {
    id: 'ember',
    name: '熔岩',
    mode: 'dark',
    bgImageMobile: '/skins/ember/bg-mobile.webp',
    bgImageOpacityMobile: 0.25,
    bgPositionMobile: 'center 30%',
    preview: 'linear-gradient(135deg,#fdba74,#dc2626)',
    vars: {
      '--skin-bg': 'linear-gradient(155deg,#170c0a 0%,#241010 50%,#180d0b 100%)',
      '--orb-1': 'radial-gradient(circle, rgba(239,68,68,.20), transparent 65%)',
      '--orb-2': 'radial-gradient(circle, rgba(249,115,22,.20), transparent 65%)',
      '--orb-3': 'radial-gradient(circle, rgba(220,38,38,.14), transparent 65%)',
      '--glass-bg': 'rgba(38,20,14,.90)',
      '--glass-border': 'rgba(255,150,110,.14)',
      '--glass-shadow': '0 8px 32px rgba(0,0,0,.48)',
      '--glass-hover-shadow': '0 12px 40px rgba(0,0,0,.58)',
      '--header-bg': 'rgba(24,12,9,.93)',
      '--table-header-bg': 'rgba(66,32,22,.55)',
      '--popup-bg': 'rgba(34,18,12,.96)',
      '--accent': '#fb923c',
      '--accent-2': '#fdba74',
      '--accent-gradient': 'linear-gradient(135deg,#fdba74 0%,#fb923c 40%,#ef4444 100%)',
      '--accent-glow': 'rgba(249,115,22,.35)',
      '--text-strong': '#f6e4da',
    },
    antd: {
      token: {
        colorPrimary: '#f97316',
        colorInfo: '#f97316',
        colorLink: '#fb923c',
        colorTextBase: '#f6e4da',
        colorBgBase: '#1d100c',
        borderRadius: 12,
      },
    },
  },
  {
    id: 'sapphire',
    name: '曜蓝',
    mode: 'dark',
    bgImage: '/skins/sapphire/bg.webp',
    bgImageOpacity: 0.28,
    bgPosition: 'center 30%',
    preview: 'linear-gradient(135deg,#7aa5f8,#1e3a6e)',
    vars: {
      '--skin-bg': 'linear-gradient(160deg,#0a0f1d 0%,#0d1526 55%,#090e1a 100%)',
      '--orb-1': 'radial-gradient(circle, rgba(59,111,212,.14), transparent 65%)',
      '--orb-2': 'radial-gradient(circle, rgba(122,165,248,.08), transparent 65%)',
      '--orb-3': 'radial-gradient(circle, rgba(30,58,110,.16), transparent 65%)',
      '--glass-bg': 'rgba(17,25,44,.90)',
      '--glass-border': 'rgba(120,150,200,.14)',
      '--glass-shadow': '0 8px 28px rgba(0,0,0,.42)',
      '--glass-hover-shadow': '0 12px 36px rgba(0,0,0,.52)',
      '--header-bg': 'rgba(10,15,29,.93)',
      '--table-header-bg': 'rgba(24,34,58,.60)',
      '--popup-bg': 'rgba(15,22,40,.96)',
      '--accent': '#5b8def',
      '--accent-2': '#7aa5f8',
      '--accent-gradient': 'linear-gradient(135deg,#7aa5f8 0%,#5b8def 50%,#3b6fd4 100%)',
      '--accent-glow': 'rgba(91,141,239,.28)',
      '--text-strong': '#dbe4f0',
    },
    antd: {
      token: {
        colorPrimary: '#5b8def',
        colorInfo: '#5b8def',
        colorLink: '#7aa5f8',
        colorTextBase: '#dbe4f0',
        colorBgBase: '#0c1322',
        borderRadius: 10,
      },
    },
  },
]

export const DEFAULT_SKIN = 'sunrise'

// ========== 超电磁炮主题 (二次元) ==========
SKINS.push(
  {
    id: 'railgun',
    name: '电磁炮',
    mode: 'dark',
    deco: 'railgun',
    bgImage: '/skins/railgun/bg.webp',
    bgImageOpacity: 0.35,
    mascot: '/skins/railgun/mascot.webp',
    preview: 'linear-gradient(135deg,#38bdf8,#fbbf24)',
    vars: {
      '--skin-bg': 'linear-gradient(155deg,#070d1a 0%,#0b1730 45%,#0a1020 100%)',
      '--orb-1': 'radial-gradient(circle, rgba(56,189,248,.20), transparent 65%)',
      '--orb-2': 'radial-gradient(circle, rgba(251,191,36,.13), transparent 65%)',
      '--orb-3': 'radial-gradient(circle, rgba(14,165,233,.16), transparent 65%)',
      '--glass-bg': 'rgba(13,25,48,.90)',
      '--glass-border': 'rgba(125,211,252,.16)',
      '--glass-shadow': '0 8px 32px rgba(0,0,0,.5)',
      '--glass-hover-shadow': '0 12px 40px rgba(2,12,30,.65)',
      '--header-bg': 'rgba(8,14,28,.93)',
      '--table-header-bg': 'rgba(24,44,78,.55)',
      '--popup-bg': 'rgba(14,26,50,.96)',
      '--accent': '#38bdf8',
      '--accent-2': '#fbbf24',
      '--accent-gradient': 'linear-gradient(135deg,#7dd3fc 0%,#38bdf8 50%,#0284c7 100%)',
      '--accent-glow': 'rgba(56,189,248,.35)',
      '--text-strong': '#e3eefb',
    },
    antd: {
      token: {
        colorPrimary: '#38bdf8',
        colorInfo: '#38bdf8',
        colorLink: '#7dd3fc',
        colorTextBase: '#e3eefb',
        colorBgBase: '#0b1426',
        borderRadius: 12,
      },
    },
  },
  {
    id: 'tokiwadai',
    name: '常盘台',
    mode: 'light',
    deco: 'railgun',
    bgImage: '/skins/tokiwadai/bg.webp',
    bgImageOpacity: 0.3,
    mascot: '/skins/tokiwadai/mascot.webp',
    bgImageMobile: '/skins/tokiwadai/bg-mobile.webp',
    bgImageOpacityMobile: 0.2,
    bgPositionMobile: 'center 30%',
    preview: 'linear-gradient(135deg,#d97706,#38bdf8)',
    vars: {
      '--skin-bg': 'linear-gradient(155deg,#fbf4e6 0%,#f5e8d2 50%,#f9efe0 100%)',
      '--orb-1': 'radial-gradient(circle, rgba(217,119,6,.28), transparent 65%)',
      '--orb-2': 'radial-gradient(circle, rgba(56,189,248,.22), transparent 65%)',
      '--orb-3': 'radial-gradient(circle, rgba(251,191,36,.30), transparent 65%)',
      '--glass-bg': 'rgba(255,253,248,.90)',
      '--glass-border': 'rgba(255,255,255,.8)',
      '--glass-shadow': '0 8px 32px rgba(146,99,32,.14)',
      '--glass-hover-shadow': '0 12px 40px rgba(146,99,32,.20)',
      '--header-bg': 'rgba(251,244,230,.93)',
      '--table-header-bg': 'rgba(247,233,208,.85)',
      '--popup-bg': 'rgba(255,251,244,.96)',
      '--accent': '#d97706',
      '--accent-2': '#38bdf8',
      '--accent-gradient': 'linear-gradient(135deg,#fbbf24 0%,#d97706 55%,#b45309 100%)',
      '--accent-glow': 'rgba(217,119,6,.32)',
      '--text-strong': '#3f2a12',
    },
    antd: {
      token: {
        colorPrimary: '#d97706',
        colorInfo: '#d97706',
        colorLink: '#b45309',
        colorTextBase: '#3f2a12',
        colorBgBase: '#f8eeda',
        borderRadius: 12,
      },
    },
  },
)
