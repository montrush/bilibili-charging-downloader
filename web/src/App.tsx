import { useState, useEffect } from 'react'
import { Spin } from 'antd'
import { loginApi } from './api'
import LoginPage from './pages/LoginPage'
import DownloadPage from './pages/DownloadPage'
import SkinSwitcher from './components/SkinSwitcher'
import Logo from './components/Logo'

export default function App() {
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
      <div className="bg-orbs">
        <div className="bg-orb bg-orb-1" />
        <div className="bg-orb bg-orb-2" />
        <div className="bg-orb bg-orb-3" />
      </div>

      <header className="app-header">
        <div className="app-header-brand">
          <Logo size={34} />
          <span className="app-header-title gradient-text">B站充电视频下载器</span>
        </div>
        <SkinSwitcher />
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
    </>
  )
}
