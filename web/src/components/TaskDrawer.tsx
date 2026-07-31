import { useEffect, useRef, useState } from 'react'
import { Badge, Button, Checkbox, Divider, Drawer, Empty, InputNumber, Popconfirm, Progress, Space, Tag, Tooltip, Typography, message } from 'antd'
import {
  CloudDownloadOutlined, PauseCircleOutlined, PlayCircleOutlined,
  DeleteOutlined, SettingOutlined,
} from '@ant-design/icons'
import { downloadApi, DlTask, DlSettings } from '../api'

const { Text } = Typography

const STATUS_META: Record<DlTask['status'], { label: string; color: string }> = {
  running: { label: '下载中', color: 'processing' },
  queued: { label: '排队中', color: 'default' },
  paused: { label: '已暂停', color: 'warning' },
  done: { label: '已完成', color: 'success' },
}

function TaskItem({ t, onAction }: { t: DlTask; onAction: () => void }) {
  const [busy, setBusy] = useState(false)
  const meta = STATUS_META[t.status]
  const percent = t.total ? Math.round((t.done / t.total) * 100) : 0
  const failN = t.failed.length

  const act = async (fn: () => Promise<{ ok: boolean; error?: string }>) => {
    setBusy(true)
    try {
      const r = await fn()
      if (!r.ok) message.warning(r.error || '操作失败')
    } finally {
      setBusy(false)
      onAction()
    }
  }

  return (
    <div className="glass-card" style={{ padding: '12px 16px', marginBottom: 12 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
        <Tag color={meta.color} style={{ marginInlineEnd: 0 }}>{meta.label}</Tag>
        <Text strong ellipsis style={{ flex: 1 }} title={t.title}>{t.title || t.path}</Text>
        <Space size={4}>
          {t.status === 'running' && (
            <Tooltip title="暂停">
              <Button size="small" type="text" loading={busy} icon={<PauseCircleOutlined />}
                onClick={() => act(() => downloadApi.pause(t.task_id))} />
            </Tooltip>
          )}
          {t.status === 'paused' && (
            <Tooltip title="继续下载">
              <Button size="small" type="text" loading={busy} icon={<PlayCircleOutlined style={{ color: '#52c41a' }} />}
                onClick={() => act(() => downloadApi.resume(t.task_id))} />
            </Tooltip>
          )}
          {t.status === 'queued' && (
            <Tooltip title="移出队列(暂停)">
              <Button size="small" type="text" loading={busy} icon={<PauseCircleOutlined />}
                onClick={() => act(() => downloadApi.pause(t.task_id))} />
            </Tooltip>
          )}
          <Popconfirm title="删除该任务记录?" description="已下载的视频文件不会被删除" onConfirm={() => act(() => downloadApi.remove(t.task_id))}>
            <Button size="small" type="text" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      </div>
      <Progress percent={percent} size="small"
        status={t.status === 'running' ? 'active' : failN && t.status === 'done' ? 'exception' : undefined}
        format={() => `${t.done}/${t.total}`} />
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 2 }}>
        <Text type="secondary" style={{ fontSize: 12 }} ellipsis title={t.path}>{t.path}</Text>
        {failN > 0 && <Text type="danger" style={{ fontSize: 12, flexShrink: 0, marginLeft: 8 }}>失败 {failN}</Text>}
      </div>
    </div>
  )
}

export default function TaskDrawer() {
  const [open, setOpen] = useState(false)
  const [tasks, setTasks] = useState<DlTask[]>([])
  const [settings, setSettings] = useState<DlSettings>({ max_parallel: 2, auto_resume: false })
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const activeN = tasks.filter(t => t.status === 'running' || t.status === 'queued').length

  const refresh = async () => {
    try {
      const [t, s] = await Promise.all([downloadApi.tasks(), downloadApi.settings()])
      if (t.ok) setTasks(t.data)
      if (s.ok) setSettings(s.data)
    } catch { /* 后端没起时静默 */ }
  }

  useEffect(() => { refresh() }, [])

  // 打开面板时3s轮询; 关闭时降到15s(只为header角标)
  useEffect(() => {
    if (pollRef.current) clearInterval(pollRef.current)
    pollRef.current = setInterval(refresh, open ? 3000 : 15000)
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [open])

  const saveSettings = async (patch: Partial<DlSettings>) => {
    const next = { ...settings, ...patch }
    setSettings(next)
    const r = await downloadApi.putSettings(patch)
    if (!r.ok) message.warning(r.error || '设置保存失败')
    refresh()
  }

  return (
    <>
      <Badge count={activeN} size="small" offset={[-4, 6]}>
        <Button icon={<CloudDownloadOutlined />} onClick={() => setOpen(true)}>任务</Button>
      </Badge>
      <Drawer title="下载任务" width={420} open={open} onClose={() => setOpen(false)}>
        <div className="glass-card" style={{ padding: '12px 16px', marginBottom: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
            <SettingOutlined />
            <Text strong>队列设置</Text>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
            <Text>并行任务数</Text>
            <InputNumber min={1} max={5} value={settings.max_parallel}
              onChange={v => v && saveSettings({ max_parallel: v })} />
          </div>
          <Checkbox checked={settings.auto_resume}
            onChange={e => saveSettings({ auto_resume: e.target.checked })}>
            启动后自动续接未完成的任务
          </Checkbox>
        </div>
        <Divider style={{ margin: '8px 0 16px' }} />
        {tasks.length === 0 ? (
          <Empty description="暂无下载任务" image={Empty.PRESENTED_IMAGE_SIMPLE} />
        ) : (
          tasks.map(t => <TaskItem key={t.task_id} t={t} onAction={refresh} />)
        )}
      </Drawer>
    </>
  )
}
