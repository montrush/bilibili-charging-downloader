import { useState } from 'react'
import { App, Card, Input, Button, Table, Progress, Typography, Space, Tag, Grid, Image } from 'antd'
import { DownloadOutlined, SearchOutlined, LinkOutlined, FolderOpenOutlined, UnorderedListOutlined, FileTextOutlined, PictureOutlined } from '@ant-design/icons'
import { parseApi, downloadApi } from '../api'

const { Title, Text } = Typography

interface Episode { aid: string; title: string; date: string; duration: number; bvid?: string }
interface VideoInfo {
  link_type: 'video' | 'collection' | 'article' | 'image' | 'unknown'
  aid?: string
  title?: string
  is_collection?: boolean
  collection: { title: string; episodes: Episode[] } | null
  article_info?: any
  image_info?: any
  message?: string
  raw_url: string
  resolved_url: string
}

export default function DownloadPage() {
  const { message } = App.useApp()
  const screens = Grid.useBreakpoint()
  const isMobile = Boolean(screens.xs)

  const [url, setUrl] = useState('')
  const [parsing, setParsing] = useState(false)
  const [info, setInfo] = useState<VideoInfo | null>(null)
  const [selected, setSelected] = useState<string[]>([])
  const [path, setPath] = useState('downloads')
  const [downloading, setDownloading] = useState(false)
  const [progress, setProgress] = useState<{ done: number; total: number; current: string; failed: any[]; status: string } | null>(null)

  const handleParse = async () => {
    if (!url.trim()) { message.warning('请输入B站链接'); return }
    setParsing(true); setInfo(null); setProgress(null); setSelected([])
    try {
      const res = await parseApi.parse(url.trim())
      if (!res.ok) { message.error(res.error); return }
      const data: VideoInfo = res.data
      setInfo(data)
      if ((data.link_type === 'video' || data.link_type === 'collection') && data.is_collection && data.collection) {
        setSelected(data.collection.episodes.map((e: Episode) => e.aid))
      } else if (data.link_type === 'video' && data.aid) {
        setSelected([data.aid])
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

  const columns = [
    { title: '#', render: (_: any, __: any, i: number) => i + 1, width: 50 },
    { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
    { title: '发布日期', dataIndex: 'date', key: 'date', width: 120 },
    { title: '时长', key: 'duration', width: 80, render: (r: Episode) => r.duration ? `${Math.round(r.duration / 60)}分钟` : '-' },
  ]

  const renderInfo = () => {
    if (!info) return null

    if (info.link_type === 'article') {
      const art = info.article_info || {}
      return (
        <Card
          className="glass-card anim-enter anim-delay-2"
          style={{ marginBottom: 20 }}
          title={<Space><FileTextOutlined style={{ color: 'var(--accent)' }} /><span>专栏文章</span></Space>}
          extra={<Tag color="orange" style={{ borderRadius: 999 }}>暂不支持下载</Tag>}
        >
          <Title level={4} style={{ fontSize: isMobile ? 18 : 24, marginTop: 0 }}>{art.title || info.title}</Title>
          {art.banner_url && (
            <Image src={art.banner_url} style={{ maxWidth: '100%', marginBottom: 12, borderRadius: 12 }} />
          )}
          <Space direction="vertical" style={{ width: '100%' }}>
            <Text type="secondary">作者: {art.author || '-'}</Text>
            <Text>摘要: {art.summary || '-'}</Text>
            <Text type="secondary">字数: {art.words || 0} | 阅读: {art.view || 0}</Text>
          </Space>
        </Card>
      )
    }

    if (info.link_type === 'image') {
      const img = info.image_info || {}
      return (
        <Card
          className="glass-card anim-enter anim-delay-2"
          style={{ marginBottom: 20 }}
          title={<Space><PictureOutlined style={{ color: 'var(--accent)' }} /><span>图片动态</span></Space>}
          extra={<Tag color="orange" style={{ borderRadius: 999 }}>暂不支持下载</Tag>}
        >
          <Text strong>{img.author || '-'}</Text>
          <div style={{ marginTop: 8, marginBottom: 12, whiteSpace: 'pre-wrap' }}>{img.content || info.title}</div>
          {img.pictures && img.pictures.length > 0 && (
            <Image.PreviewGroup>
              <Space wrap>
                {img.pictures.slice(0, 6).map((src: string, i: number) => (
                  <Image key={i} src={src} width={isMobile ? 100 : 140} style={{ borderRadius: 12 }} />
                ))}
              </Space>
            </Image.PreviewGroup>
          )}
        </Card>
      )
    }

    // video / collection
    const episodes = info.is_collection
      ? info.collection!.episodes
      : (info.aid ? [{ aid: info.aid, title: info.title || '', date: '', duration: 0, bvid: '' }] : [])

    return (
      <Card
        className="glass-card anim-enter anim-delay-2"
        style={{ marginBottom: 20 }}
        title={
          <Space>
            <UnorderedListOutlined style={{ color: 'var(--accent)' }} />
            <span>{info.is_collection ? info.collection!.title : info.title}</span>
          </Space>
        }
        extra={
          <Tag color={info.is_collection ? 'orange' : 'green'} style={{ borderRadius: 999 }}>
            {info.is_collection ? `合集 · ${episodes.length}集` : '单视频'}
          </Tag>
        }
      >
        <Table
          dataSource={episodes}
          columns={columns}
          rowKey="aid"
          size="middle"
          pagination={{ pageSize: 20, showSizeChanger: false }}
          scroll={{ x: 'max-content' }}
          rowSelection={{
            selectedRowKeys: selected,
            onChange: keys => setSelected(keys as string[]),
          }}
          footer={() => (
            <Space wrap>
              <Text>已选 <Text strong style={{ color: 'var(--accent)' }}>{selected.length}</Text>/{episodes.length} 集</Text>
              <Button size="small" onClick={() => setSelected(episodes.map(e => e.aid))}>全选</Button>
              <Button size="small" onClick={() => setSelected([])}>全不选</Button>
            </Space>
          )}
        />
      </Card>
    )
  }

  return (
    <main className="app-main" style={isMobile ? { padding: '20px 12px 48px' } : undefined}>
      {/* Hero */}
      <div className="hero anim-enter">
        <span className="hero-badge">充电专属 · 完整版下载</span>
        <h1 className="hero-title gradient-text" style={{ fontSize: isMobile ? 30 : 40 }}>B站视频下载器</h1>
        <p className="hero-subtitle">粘贴链接, 解析合集, 勾选下载 — 支持 短链 / BV号 / 合集 / 专栏 / 动态</p>
      </div>

      {/* 链接输入 */}
      <Card className="glass-card anim-enter anim-delay-1" style={{ marginBottom: 20 }}>
        <Space.Compact style={{ width: '100%' }}>
          <Input
            size="large"
            placeholder="粘贴B站链接 (b23.tv/xxx, BV号, 合集, 专栏, 动态)"
            value={url}
            onChange={e => setUrl(e.target.value)}
            onPressEnter={handleParse}
            prefix={<LinkOutlined style={{ color: 'var(--accent)' }} />}
            disabled={parsing}
          />
          <Button
            type="primary"
            size="large"
            className="btn-glow"
            icon={<SearchOutlined />}
            onClick={handleParse}
            loading={parsing}
          >
            解析
          </Button>
        </Space.Compact>
      </Card>

      {info && renderInfo()}

      {/* 下载设置 */}
      {info && (info.link_type === 'video' || info.link_type === 'collection') && (
        <Card className="glass-card anim-enter anim-delay-3" style={{ marginBottom: 20 }}>
          <Space
            direction={isMobile ? 'vertical' : 'horizontal'}
            style={{ width: '100%', justifyContent: 'space-between' }}
            size={isMobile ? 'middle' : 'small'}
          >
            <Space style={{ width: isMobile ? '100%' : 'auto' }}>
              <FolderOpenOutlined style={{ color: 'var(--accent)', fontSize: 18 }} />
              <Text>下载路径</Text>
              <Input
                value={path}
                onChange={e => setPath(e.target.value)}
                style={{ width: isMobile ? 200 : 340 }}
                placeholder="下载目录"
              />
            </Space>
            <Button
              type="primary"
              size="large"
              className="btn-glow"
              icon={<DownloadOutlined />}
              onClick={handleDownload}
              loading={downloading}
              disabled={selected.length === 0}
              block={isMobile}
            >
              下载 {selected.length} 集
            </Button>
          </Space>
        </Card>
      )}

      {/* 下载进度 */}
      {progress && (
        <Card className="glass-card anim-enter anim-delay-4" title="下载进度">
          <Progress
            percent={Math.round(progress.done / progress.total * 100)}
            status={downloading ? 'active' : 'normal'}
            strokeColor={{ from: '#fbbf24', to: '#f97316' }}
          />
          <div style={{ marginTop: 10 }}>
            <Text>{progress.done}/{progress.total}</Text>
            {progress.current && <Tag color="processing" style={{ marginLeft: 8, borderRadius: 999 }}>正在下载: {progress.current}</Tag>}
          </div>
          {progress.failed.length > 0 && (
            <div style={{ marginTop: 8 }}>
              <Text type="danger">失败 {progress.failed.length} 个:</Text>
              {progress.failed.map((f, i) => (
                <Tag key={i} color="error" style={{ borderRadius: 999 }}>{f.aid}: {f.error}</Tag>
              ))}
            </div>
          )}
        </Card>
      )}
    </main>
  )
}
