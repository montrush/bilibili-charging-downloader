import { useState, useEffect, useRef } from 'react'
import { Card, Typography, Alert, Spin } from 'antd'
import { loginApi } from '../api'
import Logo from '../components/Logo'

const { Text } = Typography

export default function LoginPage({ onLogin }: { onLogin: () => void }) {
  const [qr, setQr] = useState<{ qr_base64: string; qrcode_key: string } | null>(null)
  const [msg, setMsg] = useState('请用手机B站APP扫码登录')
  const [loading, setLoading] = useState(true)
  const timerRef = useRef<ReturnType<typeof setInterval>>()

  useEffect(() => {
    loginApi.qrcode().then(data => {
      setQr(data)
      setLoading(false)
      timerRef.current = setInterval(async () => {
        const st = await loginApi.status(data.qrcode_key)
        if (st.logged_in) {
          clearInterval(timerRef.current)
          setMsg('登录成功!')
          setTimeout(onLogin, 500)
        } else if (st.code === 86038) {
          clearInterval(timerRef.current)
          setMsg('二维码过期, 正在刷新...')
          setLoading(true)
          loginApi.qrcode().then(d => { setQr(d); setLoading(false); setMsg('请用手机B站APP扫码登录') })
        } else if (st.code === 86090) {
          setMsg('已扫码, 请在手机上确认登录')
        }
      }, 2000)
    })
    return () => { if (timerRef.current) clearInterval(timerRef.current) }
  }, [])

  return (
    <main className="app-main" style={{ display: 'flex', justifyContent: 'center', paddingTop: 64 }}>
      <Card className="glass-card anim-enter" style={{ width: 400, textAlign: 'center' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8, marginBottom: 8 }}>
          <Logo size={56} />
          <h2 className="gradient-text" style={{ margin: '8px 0 0', fontSize: 22, fontWeight: 800 }}>扫码登录</h2>
          <Text type="secondary">{msg}</Text>
        </div>
        <div style={{ margin: '20px 0' }}>
          {loading || !qr ? <Spin size="large" /> : (
            <div style={{
              display: 'inline-block', padding: 12, borderRadius: 16,
              background: '#fff', boxShadow: '0 4px 20px var(--accent-glow)',
            }}>
              <img src={qr.qr_base64} alt="二维码" style={{ width: 220, height: 220, display: 'block' }} />
            </div>
          )}
        </div>
        <Alert type="info" showIcon message="扫码登录后可下载充电专属视频完整版" style={{ borderRadius: 12 }} />
      </Card>
    </main>
  )
}
