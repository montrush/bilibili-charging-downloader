// 服务器目录浏览对话框 (参考qBittorrent WebUI的目录选择).
import { useState, useEffect } from 'react'
import { Modal, Button, List, Input, Spin, Typography } from 'antd'
import { FolderOutlined, ArrowUpOutlined, HomeOutlined, ReloadOutlined } from '@ant-design/icons'
import { fsApi } from '../api'

const { Text } = Typography

interface Props {
  open: boolean
  initialPath?: string
  onSelect: (path: string) => void
  onCancel: () => void
}

export default function DirBrowserModal({ open, initialPath, onSelect, onCancel }: Props) {
  const [cur, setCur] = useState('')
  const [parent, setParent] = useState('')
  const [dirs, setDirs] = useState<string[]>([])
  const [home, setHome] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const apply = (r: any) => {
    setCur(r.path); setParent(r.parent); setDirs(r.dirs); setHome(r.home || '')
  }

  const load = async (path: string) => {
    setLoading(true); setError('')
    try {
      const r = await fsApi.browse(path)
      if (!r.ok) { setError(r.error || '浏览失败'); return }
      apply(r)
    } catch (e: any) {
      setError('浏览失败: ' + e.message)
    } finally { setLoading(false) }
  }

  useEffect(() => {
    if (!open) return
    ;(async () => {
      setLoading(true); setError('')
      try {
        if (initialPath) {
          const r = await fsApi.browse(initialPath)
          if (r.ok) { apply(r); return }
          // 初始路径不存在/相对路径 -> 回退到项目目录
          const d = await fsApi.browse('')
          if (d.ok && d.home) {
            const h = await fsApi.browse(d.home)
            if (h.ok) { apply(h); return }
            apply(d)
            return
          }
        }
        await load('')
      } finally { setLoading(false) }
    })()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open])

  const join = (base: string, name: string) =>
    base.endsWith('\\') || base.endsWith('/') ? base + name : base + (base.includes('\\') ? '\\' : '/') + name

  return (
    <Modal
      title="选择下载目录"
      open={open}
      onCancel={onCancel}
      width={520}
      footer={[
        <Button key="cancel" onClick={onCancel}>取消</Button>,
        <Button key="ok" type="primary" className="btn-glow" disabled={!cur} onClick={() => onSelect(cur)}>
          选择此目录
        </Button>,
      ]}
    >
      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        <Button icon={<ArrowUpOutlined />} onClick={() => load(parent)} disabled={!parent && cur !== ''} title="上一级" />
        <Button icon={<HomeOutlined />} onClick={() => load(home)} disabled={!home} title="项目目录" />
        <Button icon={<ReloadOutlined />} onClick={() => load(cur)} title="刷新" />
        <Input value={cur} placeholder="输入路径后回车" onPressEnter={e => load((e.target as HTMLInputElement).value)} onChange={e => setCur(e.target.value)} />
      </div>
      {error && <Text type="danger">{error}</Text>}
      <div style={{ height: 320, overflowY: 'auto', border: '1px solid var(--glass-border)', borderRadius: 12 }}>
        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 120 }}><Spin /></div>
        ) : (
          <List
            dataSource={dirs}
            locale={{ emptyText: '此目录下没有子目录' }}
            renderItem={d => (
              <List.Item
                style={{ padding: '8px 16px', cursor: 'pointer' }}
                onDoubleClick={() => load(cur ? join(cur, d) : d)}
                onClick={() => load(cur ? join(cur, d) : d)}
              >
                <FolderOutlined style={{ color: 'var(--accent)', marginRight: 8 }} />
                {d}
              </List.Item>
            )}
          />
        )}
      </div>
      <Text type="secondary" style={{ fontSize: 12, marginTop: 8, display: 'block' }}>
        单击进入目录, 然后点"选择此目录"确认
      </Text>
    </Modal>
  )
}
