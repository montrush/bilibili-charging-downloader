import { useState, useEffect } from 'react'
import { Spin } from 'antd'
import { loginApi } from './api'
import LoginPage from './pages/LoginPage'
import DownloadPage from './pages/DownloadPage'

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

  if (loggedIn === null) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Spin size="large" />
      </div>
    )
  }
  if (!loggedIn) return <LoginPage onLogin={() => setLoggedIn(true)} />
  return <DownloadPage />
}
