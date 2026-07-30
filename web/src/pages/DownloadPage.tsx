import { useState } from 'react'
import { App, Card, Input, Button, Table, Progress, Typography, Space, Tag, Grid, Image, Checkbox, Tooltip } from 'antd'
import { DownloadOutlined, SearchOutlined, LinkOutlined, FolderOpenOutlined, UnorderedListOutlined, FileTextOutlined, PictureOutlined } from '@ant-design/icons'
import { parseApi, downloadApi } from '../api'
import InfoPanel from '../components/InfoPanel'
import type { StatInfo } from '../components/InfoPanel'
import DirBrowserModal from '../components/DirBrowserModal'

const { Title, Text } = Typography

interface Episode { aid: string; title: string; date: string; duration: number; bvid?: string }
interface VideoInfo {
  link_type: 'video' | 'collection' | 'article' | 'image' | 'unknown'
  aid?: string
  title?: string
  is_collection?: boolean
  collection: {
    title: string; episodes: Episode[]
    cover?: string; intro?: string; ep_count?: number; stat?: StatInfo
  } | null
  article_info?: any
  image_info?: any
  message?: string
  raw_url: string
  resolved_url: string
  // 状态窗口元数据
  owner?: string
  owner_mid?: number
  owner_face?: string
  pic?: string
  desc?: string
  tname?: string
  stat?: StatInfo
  date?: string
}

// 目录设置持久化
interface DlSettings {
  path: string
  autoMkdir: boolean
  mkdirUp: boolean
  mkdirCollection: boolean
}
const LS_SETTINGS = 'bili-dl-settings'
const DEFAULT_SETTINGS: DlSettings = {
  path: 'downloads',
  autoMkdir: true,
  mkdirUp: true,
  mkdirCollection: true,
}
function loadSettings(): DlSettings {
  try {
    const s = localStorage.getItem(LS_SETTINGS)
    if (s) return { ...DEFAULT_SETTINGS, ...JSON.parse(s) }
  } catch { /* ignore */ }
  return DEFAULT_SETTINGS
}

// 目录名清洗(与后端一致)
const sanitizeDirName = (s: string) => s.replace(/[\\/:*?"<>|\r\n]+/g, '_').trim().replace(/\.+$/, '').slice(0, 80)

export default function DownloadPage() {
  const { message } = App.useApp()
  const screens = Grid.useBreakpoint()
  const isMobile = Boolean(screens.xs)

  const [url, setUrl] = useState('')
  const [parsing, setParsing] = useState(false)
  const [collecting, setCollecting] = useState(false)
  const [info, setInfo] = useState<VideoInfo | null>(null)
  const [selected, setSelected] = useState<string[]>([])
  const [settings, setSettings] = useState<DlSettings>(loadSettings)
  const [dirModalOpen, setDirModalOpen] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [progress, setProgress] = useState<{ done: number; total: number; current: string; failed: any[]; status: string } | null>(null)

  const updateSettings = (patch: Partial<DlSettings>) => {
    setSettings(prev => {
      const next = { ...prev, ...patch }
      localStorage.setItem(LS_SETTINGS, JSON.stringify(next))
      return next
    })
  }

  // 解析结果应用: 合集默认全选, 需要再手动取消勾选
  const applyInfo = (data: VideoInfo) => {
    setInfo(data)
    if ((data.link_type === 'video' || data.link_type === 'collection') && data.is_collection && data.collection) {
      setSelected(data.collection.episodes.map((e: Episode) => e.aid))
    } else if (data.link_type === 'video' && data.aid) {
      setSelected([data.aid])
    }
  }

  const handleParse = async () => {
    if (!url.trim()) { message.warning('请输入B站链接'); return }
    setParsing(true); setInfo(null); setProgress(null); setSelected([])
    try {
      const res = await parseApi.parse(url.trim())
      if (!res.ok) { message.error(res.error); return }
      applyInfo(res.data)
    } catch (e: any) { message.error('解析失败: ' + e.message) }
    finally { setParsing(false) }
  }

  // 下载合集: 任意一集链接 -> 展开所属合集全部剧集(默认全选)
  const handleParseCollection = async () => {
    if (!url.trim()) { message.warning('请输入B站视频链接'); return }
    setCollecting(true); setInfo(null); setProgress(null); setSelected([])
    try {
      const res = await parseApi.parseCollection(url.trim())
      if (!res.ok) { message.warning(res.error); return }
      applyInfo(res.data)
      const n = res.data?.collection?.episodes?.length || 0
      message.success(`已展开合集「${res.data.collection?.title}」, 共 ${n} 集, 默认全选`)
    } catch (e: any) { message.error('解析失败: ' + e.message) }
    finally { setCollecting(false) }
  }

  const handleDownload = async () => {
    if (selected.length === 0) { message.warning('请至少选择一个视频'); return }
    setDownloading(true)
    setProgress({ done: 0, total: selected.length, current: '', failed: [], status: 'running' })
    try {
      const res = await downloadApi.start(selected, settings.path, {
        auto_mkdir: settings.autoMkdir,
        mkdir_up: settings.mkdirUp,
        mkdir_collection: settings.mkdirCollection,
        up_name: info?.owner || '',
        collection_title: info?.is_collection ? (info.collection?.title || '') : '',
      })
      if (!res.ok) { message.error(res.error); setDownloading(false); return }
      if (res.final_dir) message.success(`保存到: ${res.final_dir}`)
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
    { title: '发布日期', dataIndex: 'date', key: 'date', width: 110 },
    { title: '时长', key: 'duration', width: 80, render: (r: Episode) => r.duration ? `${Math.round(r.duration / 60)}分钟` : '-' },
  ]

  const isVideoType = info && (info.link_type === 'video' || info.link_type === 'collection')
  const episodes = info?.is_collection
    ? info.collection!.episodes
    : (info?.aid ? [{ aid: info.aid, title: info.title || '', date: info.date || '', duration: 0, bvid: '' }] : [])

  // 最终保存路径预览 (与后端拼接规则一致)
  const finalDirPreview = [
    settings.path,
    settings.mkdirUp && info?.owner ? sanitizeDirName(info.owner) : '',
    settings.mkdirCollection && info?.is_collection && info.collection?.title ? sanitizeDirName(info.collection.title) : '',
  ].filter(Boolean).join(' / ') + ' /'

  const renderArticleOrImage = () => {
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
    return null
  }

  return (
    <main className="app-main app-main-wide" style={isMobile ? { padding: '20px 12px 48px' } : undefined}>
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
            disabled={parsing || collecting}
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
          <Tooltip title="粘贴任意一集链接, 展开所属合集全部剧集(默认全选)">
            <Button
              size="large"
              icon={<UnorderedListOutlined />}
              onClick={handleParseCollection}
              loading={collecting}
            >
              下载合集
            </Button>
          </Tooltip>
        </Space.Compact>
      </Card>

      {info && (info.link_type === 'article' || info.link_type === 'image') && renderArticleOrImage()}

      {/* 视频/合集: PC双栏 (左状态窗口, 右分集列表+下载) */}
      {isVideoType && (
        <div className="content-grid">
          {/* 状态窗口 */}
          <aside className="info-panel-col anim-enter anim-delay-2">
            <InfoPanel
              info={info!}
              selectedCount={selected.length}
              episodeCount={episodes.length}
              downloading={downloading}
              progress={progress}
            />
          </aside>

          <div className="main-col">
            {/* 分集列表 */}
            <Card
              className="glass-card anim-enter anim-delay-2"
              style={{ marginBottom: 20 }}
              title={
                <Space>
                  <UnorderedListOutlined style={{ color: 'var(--accent)' }} />
                  <span>分集列表</span>
                  <Tag color="orange" style={{ borderRadius: 999 }}>{episodes.length}集</Tag>
                </Space>
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

            {/* 下载设置 */}
            <Card
              className="glass-card anim-enter anim-delay-3"
              style={{ marginBottom: 20 }}
              title={<Space><FolderOpenOutlined style={{ color: 'var(--accent)' }} /><span>下载设置</span></Space>}
            >
              {/* 目录选择 */}
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 14 }}>
                <Input
                  value={settings.path}
                  onChange={e => updateSettings({ path: e.target.value })}
                  style={{ flex: 1, minWidth: 220 }}
                  placeholder="下载目录"
                  prefix={<FolderOpenOutlined style={{ color: 'var(--accent)' }} />}
                />
                <Button onClick={() => setDirModalOpen(true)}>浏览…</Button>
              </div>

              {/* 目录规则 (参考qBittorrent) */}
              <Space wrap size="large" style={{ marginBottom: 12 }}>
                <Tooltip title="目标目录不存在时自动创建">
                  <Checkbox
                    checked={settings.autoMkdir}
                    onChange={e => updateSettings({ autoMkdir: e.target.checked })}
                  >
                    自动创建目录
                  </Checkbox>
                </Tooltip>
                <Tooltip title="在下载目录下按UP主名字建子目录">
                  <Checkbox
                    checked={settings.mkdirUp}
                    onChange={e => updateSettings({ mkdirUp: e.target.checked })}
                  >
                    按UP主名字建子目录
                  </Checkbox>
                </Tooltip>
                <Tooltip title="在下载目录下按合集名称建子目录">
                  <Checkbox
                    checked={settings.mkdirCollection}
                    onChange={e => updateSettings({ mkdirCollection: e.target.checked })}
                  >
                    按合集名称建子目录
                  </Checkbox>
                </Tooltip>
              </Space>

              {/* 最终路径预览 + 下载按钮 */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
                <Text type="secondary" style={{ fontSize: 13, wordBreak: 'break-all' }}>
                  保存到: <Text code style={{ fontSize: 13 }}>{finalDirPreview}</Text>
                </Text>
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
              </div>
            </Card>

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
          </div>
        </div>
      )}

      {/* 目录浏览对话框 */}
      <DirBrowserModal
        open={dirModalOpen}
        initialPath={settings.path}
        onSelect={p => { updateSettings({ path: p }); setDirModalOpen(false) }}
        onCancel={() => setDirModalOpen(false)}
      />
    </main>
  )
}
