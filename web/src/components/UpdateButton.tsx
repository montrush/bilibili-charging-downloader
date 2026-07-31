import { useEffect, useRef, useState } from 'react'
import { Badge, Button, Input, Modal, Progress, Spin, Tag, message } from 'antd'
import { CloudDownloadOutlined, SyncOutlined } from '@ant-design/icons'
import { updateApi, type UpdateInfo } from '../api'

type Phase = 'idle' | 'checking' | 'updating' | 'restarting' | 'done'
const LS_PROXY = 'bili-update-proxy'

export default function UpdateButton() {
  const [info, setInfo] = useState<UpdateInfo | null>(null)
  const [open, setOpen] = useState(false)
  const [phase, setPhase] = useState<Phase>('idle')
  const [percent, setPercent] = useState(0)
  const [channel, setChannel] = useState('')
  const [error, setError] = useState('')
  const [proxy, setProxy] = useState(() => localStorage.getItem(LS_PROXY) || '')
  const pollRef = useRef<ReturnType<typeof setInterval>>()

  // 启动时静默检查一次, 有新版本在按钮上显示红点
  useEffect(() => {
    updateApi.check(false, localStorage.getItem(LS_PROXY) || '').then(r => setInfo(r)).catch(() => {})
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [])

  const saveProxy = (v: string) => {
    setProxy(v)
    localStorage.setItem(LS_PROXY, v.trim())
  }

  const openModal = async () => {
    setOpen(true)
    setError('')
    if (phase === 'updating' || phase === 'restarting') return
    setPhase('checking')
    try {
      const r = await updateApi.check(true, proxy.trim())
      setInfo(r)
      if (r.error) setError(r.error)
    } catch (e: any) {
      setError(e?.message || '检查更新失败')
    } finally {
      setPhase('idle')
    }
  }

  const startUpdate = async () => {
    const r = await updateApi.apply(proxy.trim())
    if (!r.ok) { setError(r.error || '无法启动更新'); return }
    setPhase('updating')
    setError('')
    pollRef.current = setInterval(async () => {
      try {
        const p = await updateApi.progress()
        setPercent(p.percent)
        setChannel(p.channel || '')
        if (p.stage === 'error') {
          clearInterval(pollRef.current)
          setPhase('idle')
          setError(p.error || '更新失败')
        } else if (p.stage === 'restarting') {
          clearInterval(pollRef.current)
          setPhase('restarting')
          waitRestart()
        }
      } catch { /* 进程即将退出, 请求失败属正常 */ }
    }, 1000)
  }

  // 后端os._exit后轮询health, 起来后刷新页面
  const waitRestart = () => {
    let tries = 0
    const t = setInterval(async () => {
      tries++
      try {
        await updateApi.health()
        clearInterval(t)
        setPhase('done')
        message.success(`已更新到 v${info?.latest || ''}, 即将刷新页面`)
        setTimeout(() => window.location.reload(), 1500)
      } catch {
        if (tries > 90) {
          clearInterval(t)
          setPhase('idle')
          setError('等待重启超时, 请手动重新启动程序')
        }
      }
    }, 2000)
  }

  const updating = phase === 'updating' || phase === 'restarting' || phase === 'done'

  return (
    <>
      <Badge dot={!!info?.has_update} offset={[-4, 4]}>
        <Button
          icon={<SyncOutlined />}
          onClick={openModal}
          size="middle"
        >
          更新
        </Button>
      </Badge>

      <Modal
        title="检查更新"
        open={open}
        onCancel={() => !updating && setOpen(false)}
        footer={null}
        maskClosable={!updating}
        width={480}
      >
        {phase === 'checking' ? (
          <div style={{ textAlign: 'center', padding: '24px 0' }}><Spin /> 正在检查新版本…</div>
        ) : (
          <>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 12 }}>
              <span>当前版本 <Tag>v{info?.current || '…'}</Tag></span>
              {info?.latest && <span>最新版本 <Tag color={info.has_update ? 'green' : 'default'}>v{info.latest}</Tag></span>}
              {info?.channel && !error && (
                <span style={{ fontSize: 12, opacity: .65 }}>
                  来源: {info.channel === 'gitee' ? 'Gitee(国内)' : info.channel === 'jsdelivr' ? 'CDN' : 'GitHub'}
                </span>
              )}
            </div>

            <Input
              size="small"
              placeholder="连不上可填代理, 如 127.0.0.1:7890 (留空=直连)"
              value={proxy}
              onChange={e => saveProxy(e.target.value)}
              style={{ marginBottom: 12, fontSize: 12 }}
              disabled={updating}
            />

            {error && <div style={{ color: 'var(--ant-colorError, #ff4d4f)', marginBottom: 12 }}>⚠ {error}</div>}

            {!error && info && !info.has_update && !updating && (
              <div style={{ marginBottom: 12 }}>✅ 已是最新版本</div>
            )}

            {info?.has_update && !updating && (
              <>
                {info.notes && (
                  <pre style={{
                    maxHeight: 200, overflow: 'auto', whiteSpace: 'pre-wrap',
                    background: 'rgba(127,127,127,.08)', padding: 10, borderRadius: 8,
                    fontSize: 12, marginBottom: 12,
                  }}>{info.notes}</pre>
                )}
                {info.mode === 'auto' ? (
                  <Button type="primary" icon={<CloudDownloadOutlined />} onClick={startUpdate} block>
                    立即更新{info.asset_size ? `（约 ${Math.round(info.asset_size / 1048576)} MB）` : ''}
                  </Button>
                ) : (
                  <>
                    <div style={{ marginBottom: 8, fontSize: 13 }}>
                      {info.mode === 'dev'
                        ? '源码运行模式不支持自动更新, 请 git pull'
                        : '当前安装方式(Docker/deb)请手动更新: docker 重新拉取镜像, 或到发布页下载新版'}
                    </div>
                    <Button type="primary" href={info.page_url} target="_blank" block>
                      前往发布页
                    </Button>
                  </>
                )}
              </>
            )}

            {phase === 'updating' && (
              <div>
                <div style={{ marginBottom: 8 }}>正在下载更新包{channel ? `（通道: ${channel}）` : ''}…</div>
                <Progress percent={percent} status="active" />
              </div>
            )}
            {phase === 'restarting' && (
              <div style={{ textAlign: 'center', padding: '12px 0' }}>
                <Spin /> 正在安装并重启程序, 页面将自动刷新…
              </div>
            )}
          </>
        )}
      </Modal>
    </>
  )
}
