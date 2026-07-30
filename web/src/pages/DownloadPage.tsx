import { useState } from 'react'
import { Card, Input, Button, Table, Progress, Typography, Space, message, Tag } from 'antd'
import { DownloadOutlined, SearchOutlined } from '@ant-design/icons'
import { parseApi, downloadApi } from '../api'

const { Title, Text } = Typography

interface Episode { aid: string; title: string; date: string; duration: number }
interface VideoInfo {
  aid: string; title: string; is_collection: boolean
  collection: { title: string; episodes: Episode[] } | null
}

export default function DownloadPage() {
  const [url, setUrl] = useState('')
  const [parsing, setParsing] = useState(false)
  const [info, setInfo] = useState<VideoInfo | null>(null)
  const [selected, setSelected] = useState<string[]>([])
  const [path, setPath] = useState('downloads')
  const [downloading, setDownloading] = useState(false)
  const [progress, setProgress] = useState<{ done: number; total: number; current: string; failed: any[]; status: string } | null>(null)

  const handleParse = async () => {
    if (!url.trim()) { message.warning('请输入B站链接'); return }
    setParsing(true); setInfo(null); setProgress(null)
    try {
      const res = await parseApi.parse(url.trim())
      if (!res.ok) { message.error(res.error); return }
      setInfo(res.data)
      if (res.data.is_collection && res.data.collection) {
        setSelected(res.data.collection.episodes.map((e: Episode) => e.aid))
      } else {
        setSelected([res.data.aid])
      }
    } catch (e: any) { message.error('解析失败: ' + e.message) }
    finally { setParsing(false) }
  }

  const handleDownload = async () => {
    if (selected.length === 0) { message.warning('请至少选择一个视频'); return }
    setDownloading(true)
    setProgress({ done: 0, total: selected.length, current: '', failed: [], status: 'running' })
    try {
      const res = await downloadApi.start(selected, path)
      if (!res.ok) { message.error(res.error); setDownloading(false); return }
      const tid = res.task_id
      const timer = setInterval(async () => {
        const p = await downloadApi.progress(tid)
        if (p.ok) {
          setProgress(p.data)
          if (p.data.status === 'done') {
            clearInterval(timer)
            setDownloading(false)
            const ok = p.data.done - p.data.failed.length
            message.success(`下载完成! ${ok}/${p.data.total}成功, ${p.data.failed.length}失败`)
          }
        }
      }, 2000)
    } catch (e: any) { message.error('启动下载失败: ' + e.message); setDownloading(false) }
  }

  const episodes = info?.is_collection
    ? info.collection!.episodes
    : (info ? [{ aid: info.aid, title: info.title, date: '', duration: 0 }] : [])

  const columns = [
    { title: '#', render: (_: any, __: any, i: number) => i + 1, width: 50 },
    { title: '标题', dataIndex: 'title', key: 'title' },
    { title: '发布日期', dataIndex: 'date', key: 'date', width: 120 },
    { title: '时长', key: 'duration', width: 80, render: (r: Episode) => r.duration ? `${Math.round(r.duration / 60)}分钟` : '-' },
  ]

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto', padding: 24 }}>
      <Title level={3}>B站充电视频下载器</Title>

      <Card style={{ marginBottom: 16 }}>
        <Space.Compact style={{ width: '100%' }}>
          <Input
            size="large"
            placeholder="粘贴B站链接 (b23.tv/xxx, BV号, 合集链接)"
            value={url}
            onChange={e => setUrl(e.target.value)}
            onPressEnter={handleParse}
            prefix={<SearchOutlined />}
            disabled={parsing}
          />
          <Button type="primary" size="large" onClick={handleParse} loading={parsing}>解析</Button>
        </Space.Compact>
      </Card>

      {info && (
        <Card
          title={info.is_collection
            ? `合集: ${info.collection!.title} (${episodes.length}集)`
            : `视频: ${info.title}`}
          style={{ marginBottom: 16 }}
        >
          <Table
            dataSource={episodes}
            columns={columns}
            rowKey="aid"
            size="small"
            pagination={{ pageSize: 20 }}
            rowSelection={{
              selectedRowKeys: selected,
              onChange: keys => setSelected(keys as string[]),
            }}
            footer={() => (
              <Space>
                <Text>已选 {selected.length}/{episodes.length} 集</Text>
                <Button size="small" onClick={() => setSelected(episodes.map(e => e.aid))}>全选</Button>
                <Button size="small" onClick={() => setSelected([])}>全不选</Button>
              </Space>
            )}
          />
        </Card>
      )}

      {info && (
        <Card>
          <Space style={{ width: '100%', justifyContent: 'space-between' }}>
            <Space>
              <Text>下载路径:</Text>
              <Input
                value={path}
                onChange={e => setPath(e.target.value)}
                style={{ width: 350 }}
                placeholder="下载目录"
              />
            </Space>
            <Button
              type="primary"
              size="large"
              icon={<DownloadOutlined />}
              onClick={handleDownload}
              loading={downloading}
              disabled={selected.length === 0}
            >
              下载 {selected.length} 集
            </Button>
          </Space>
        </Card>
      )}

      {progress && (
        <Card title="下载进度" style={{ marginTop: 16 }}>
          <Progress
            percent={Math.round(progress.done / progress.total * 100)}
            status={downloading ? 'active' : 'normal'}
          />
          <div style={{ marginTop: 8 }}>
            <Text>{progress.done}/{progress.total}</Text>
            {progress.current && <Tag color="processing" style={{ marginLeft: 8 }}>正在下载: {progress.current}</Tag>}
          </div>
          {progress.failed.length > 0 && (
            <div style={{ marginTop: 8 }}>
              <Text type="danger">失败 {progress.failed.length} 个:</Text>
              {progress.failed.map((f, i) => (
                <Tag key={i} color="error">{f.aid}: {f.error}</Tag>
              ))}
            </div>
          )}
        </Card>
      )}
    </div>
  )
}
