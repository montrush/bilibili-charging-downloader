import { useState, useEffect } from 'react'
import { Spin } from 'antd'
import { loginApi } from './api'
import LoginPage from './pages/LoginPage'
import DownloadPage from './pages/DownloadPage'
import SkinSwitcher from './components/SkinSwitcher'
import UpdateButton from './components/UpdateButton'
import TaskDrawer from './components/TaskDrawer'
import Logo from './components/Logo'
import RailgunDeco from './components/RailgunDeco'
import AuthorFooter from './components/AuthorFooter'
import { useSkin } from './theme/ThemeContext'

export default function App() {
  const { skin } = useSkin()
  const [loggedIn, setLoggedIn] = useState<boolean | null>(null)

  const checkLogin = async () => {
    try {
      const r = await loginApi.check()
      setLoggedIn(r.logged_in)
    } catch {
      setLoggedIn(false)
    }
  }

  useEffect(() => { checkLogin() }, [])

  return (
    <>
      {skin.bgImage && (
        <div
          className={`skin-bg-img${skin.bgImageMobile ? ' has-mobile' : ''}`}
          style={{
            backgroundImage: `url(${skin.bgImage})`,
            opacity: skin.bgImageOpacity ?? 0.32,
            backgroundPosition: skin.bgPosition ?? 'center',
          }}
        />
      )}
      {skin.bgImageMobile && (
        <div
          className="skin-bg-img-mobile"
          style={{
            backgroundImage: `url(${skin.bgImageMobile})`,
            opacity: skin.bgImageOpacityMobile ?? skin.bgImageOpacity ?? 0.32,
            backgroundPosition: skin.bgPositionMobile ?? skin.bgPosition ?? 'center',
          }}
        />
      )}
      <div className="bg-orbs">
        <div className="bg-orb bg-orb-1" />
        <div className="bg-orb bg-orb-2" />
        <div className="bg-orb bg-orb-3" />
      </div>
      {(skin.deco === 'railgun') && <RailgunDeco arcs={skin.decoArcs ?? true} />}
      {skin.mascot && <img className="skin-mascot" src={skin.mascot} alt="" draggable={false} />}

      <header className="app-header">
        <div className="app-header-brand">
          <Logo size={34} />
          <span className="app-header-title gradient-text">B站充电视频下载器</span>
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <TaskDrawer />
          <UpdateButton />
          <SkinSwitcher />
        </div>
      </header>

      {loggedIn === null ? (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '70vh', position: 'relative', zIndex: 1 }}>
          <Spin size="large" />
        </div>
      ) : loggedIn ? (
        <DownloadPage />
      ) : (
        <LoginPage onLogin={() => setLoggedIn(true)} />
      )}

      <AuthorFooter />
    </>
  )
}
