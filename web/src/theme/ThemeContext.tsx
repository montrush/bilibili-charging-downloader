// 皮肤上下文: 当前皮肤状态 + localStorage持久化 + CSS变量注入 + antd主题注入.
import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { App as AntdApp, ConfigProvider, theme as antdTheme } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { SKINS, DEFAULT_SKIN } from './skins'
import type { Skin } from './skins'

const LS_KEY = 'bili-skin'

interface SkinCtx {
  skin: Skin
  setSkin: (id: string) => void
  /** 快速切换 淡/暗 色系 (记住各自最后用的皮肤) */
  toggleMode: () => void
}

const Ctx = createContext<SkinCtx>(null as unknown as SkinCtx)

export const useSkin = () => useContext(Ctx)

export function SkinProvider({ children }: { children: ReactNode }) {
  const [skinId, setSkinId] = useState(() => localStorage.getItem(LS_KEY) || DEFAULT_SKIN)
  const skin = useMemo(() => SKINS.find(s => s.id === skinId) || SKINS[0], [skinId])

  // 注入CSS变量 + 持久化
  useEffect(() => {
    const el = document.documentElement
    Object.entries(skin.vars).forEach(([k, v]) => el.style.setProperty(k, v))
    el.dataset.skinMode = skin.mode
    el.dataset.skinId = skin.id
    localStorage.setItem(LS_KEY, skin.id)
  }, [skin])

  const toggleMode = () => {
    const target = SKINS.find(s => s.mode !== skin.mode && s.id === localStorage.getItem(`bili-skin-last-${s.mode === 'light' ? 'dark' : 'light'}`))
      || SKINS.find(s => s.mode !== skin.mode)!
    setSkinId(target.id)
  }

  // 记住每个色系最后用的皮肤
  useEffect(() => {
    localStorage.setItem(`bili-skin-last-${skin.mode}`, skin.id)
  }, [skin])

  const algorithm = skin.mode === 'dark' ? antdTheme.darkAlgorithm : antdTheme.defaultAlgorithm

  return (
    <Ctx.Provider value={{ skin, setSkin: setSkinId, toggleMode }}>
      <ConfigProvider
        locale={zhCN}
        theme={{ ...skin.antd, algorithm, cssVar: true }}
      >
        <AntdApp>{children}</AntdApp>
      </ConfigProvider>
    </Ctx.Provider>
  )
}
