import { useState, useEffect, useRef } from 'react'
import { App, Card, Input, Button, Table, Typography, Space, Tag, Grid, Image, Checkbox, Tooltip, Segmented } from 'antd'
import { DownloadOutlined, SearchOutlined, LinkOutlined, FolderOpenOutlined, UnorderedListOutlined, FileTextOutlined, PictureOutlined } from '@ant-design/icons'
import { parseApi, downloadApi, type DlTask } from '../api'
import { TaskItem } from '../components/TaskDrawer'
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

// 解析模式: 单集 / 整个合集 (开关式切换, 选择持久化)
type ParseMode = 'single' | 'collection'
const LS_PARSE_MODE = 'bili-parse-mode'
const loadParseMode = (): ParseMode =>
  localStorage.getItem(LS_PARSE_MODE) === 'collection' ? 'collection' : 'single'

// 分集表格每页条数 (持久化)
const LS_PAGE_SIZE = 'bili-page-size'
const loadPageSize = (): number => {
  const n = parseInt(localStorage.getItem(LS_PAGE_SIZE) || '', 10)
  return [20, 50, 100, 200].includes(n) ? n : 20
}

export default function DownloadPage() {
  const { message } = App.useApp()
  const screens = Grid.useBreakpoint()
  const isMobile = Boolean(screens.xs)

  const [url, setUrl] = useState('')
  const [parsing, setParsing] = useState(false)
  const [collecting, setCollecting] = useState(false)
  const [parseMode, setParseMode] = useState<ParseMode>(loadParseMode)
  const [info, setInfo] = useState<VideoInfo | null>(null)
  const [pageSize, setPageSize] = useState<number>(loadPageSize)
  const [selected, setSelected] = useState<string[]>([])
  const [settings, setSettings] = useState<DlSettings>(loadSettings)
  const [dirModalOpen, setDirModalOpen] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [progress, setProgress] = useState<{ done: number; total: number; current: string; failed: any[]; status: string } | null>(null)
  const [taskId, setTaskId] = useState('')
  const [starting, setStarting] = useState(false)          // 下载按钮瞬时loading(入队即复位, 不阻塞下一个)
  const [tasks, setTasks] = useState<DlTask[]>([])          // 页内全部任务列表
  const pollRef = useRef<ReturnType<typeof setInterval>>()
  const tasksPollRef = useRef<ReturnType<typeof setInterval>>()

  // 轮询进度: done=完成(含失败计数), paused=已暂停可继续
  const startPolling = (tid: string) => {
    if (pollRef.current) clearInterval(pollRef.current)
    pollRef.current = setInterval(async () => {
      try {
        const p = await downloadApi.progress(tid)
        if (!p.ok) return
        setProgress(p.data)
        if (p.data.status === 'done') {
          clearInterval(pollRef.current)
          setDownloading(false)
          const ok = p.data.done - p.data.failed.length
          message.success(`下载完成! ${ok}/${p.data.total}成功, ${p.data.failed.length}失败`)
        } else if (p.data.status === 'paused') {
          clearInterval(pollRef.current)
          setDownloading(false)
          message.info('已暂停, 点「继续下载」续传; 即使关掉应用, 下次相同链接+相同目录也会自动续传')
        }
      } catch { /* 网络抖动忽略, 下轮再试 */ }
    }, 2000)
  }

  useEffect(() => () => {
    if (pollRef.current) clearInterval(pollRef.current)
    if (tasksPollRef.current) clearInterval(tasksPollRef.current)
  }, [])

  // 页内任务列表: 轮询全部任务(合集名+集数进度), 多任务同时可见
  const refreshTasks = async () => {
    try { const r = await downloadApi.tasks(); if (r.ok) setTasks(r.data) } catch { /* 后端没起时静默 */ }
  }
  useEffect(() => {
    refreshTasks()
    tasksPollRef.current = setInterval(refreshTasks, 2500)
    return () => { if (tasksPollRef.current) clearInterval(tasksPollRef.current) }
  }, [])

  const updateSettings = (patch: Partial<DlSettings>) => {
    setSettings(prev => {
      const next = { ...prev, ...patch }
      localStorage.setItem(LS_SETTINGS, JSON.stringify(next))
      return next
    })
  }

  // 解析结果应用: 合集模式=默认全选; 单集模式=只选当前这一集
  const applyInfo = (data: VideoInfo, mode: ParseMode = parseMode) => {
    setInfo(data)
    if (mode === 'collection' && (data.link_type === 'video' || data.link_type === 'collection') && data.is_collection && data.collection) {
      setSelected(data.collection.episodes.map((e: Episode) => e.aid))
    } else if (data.aid) {
      // 单集模式: 注意合集成员视频的 link_type 是 'collection', 只看 aid
      setSelected([data.aid])
      if (mode === 'single' && data.is_collection) {
        message.info('单集模式: 仅选当前视频, 切到「整个合集」可展开全部')
      }
    }
  }

  // 开关切换: 持久化选择, 已有解析结果时即时重算勾选, 无需重新请求
  const changeParseMode = (mode: ParseMode) => {
    setParseMode(mode)
    localStorage.setItem(LS_PARSE_MODE, mode)
    if (info) applyInfo(info, mode)
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

  // 下载合集: 任意一集链接 -> 展开所属合集全部剧集(默认全选), 同时把开关拨到"整个合集"
  const handleParseCollection = async () => {
    if (!url.trim()) { message.warning('请输入B站视频链接'); return }
    setCollecting(true); setInfo(null); setProgress(null); setSelected([])
    try {
      const res = await parseApi.parseCollection(url.trim())
      if (!res.ok) { message.warning(res.error); return }
      changeParseMode('collection')
      applyInfo(res.data, 'collection')
      const n = res.data?.collection?.episodes?.length || 0
      message.success(`已展开合集「${res.data.collection?.title}」, 共 ${n} 集, 默认全选`)
    } catch (e: any) { message.error('解析失败: ' + e.message) }
    finally { setCollecting(false) }
  }

  const handleDownload = async () => {
    if (selected.length === 0) { message.warning('请至少选择一个视频'); return }
    setStarting(true)
    setDownloading(true)
    setProgress({ done: 0, total: selected.length, current: '', failed: [], status: 'running' })
    try {
      const res = await downloadApi.start(selected, settings.path, {
        auto_mkdir: settings.autoMkdir,
        mkdir_up: settings.mkdirUp,
        mkdir_collection: settings.mkdirCollection,
        up_name: info?.owner || '',
        collection_title: info?.is_collection ? (info.collection?.title || '') : '',
      }, info?.is_collection ? (info.collection?.title || '') : (info?.title || ''))
      if (!res.ok) { message.error(res.error); setDownloading(false); return }
      if (res.final_dir) message.success(`保存到: ${res.final_dir}`)
      if (res.existing) {
        message.info('该目录已有未完成任务, 已合并续传')
      } else if (res.resumed) {
        message.info(`检测到未完成任务, 自动续传: 跳过已完成 ${res.skipped} 个`)
      }
      message.success('已加入下载队列, 下方「下载任务」实时显示进度; 可继续粘贴下一个链接排队下载')
      setTaskId(res.task_id)
      startPolling(res.task_id)
      refreshTasks()
    } catch (e: any) { message.error('启动下载失败: ' + e.message); setDownloading(false) }
    finally { setStarting(false) }
  }

  const columns = [
    { title: '#', render: (_: any, __: any, i: number) => i + 1, width: 50 },
    { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
    { title: '发布日期', dataIndex: 'date', key: 'date', width: 110 },
    { title: '时长', key: 'duration', width: 80, render: (r: Episode) => r.duration ? `${Math.round(r.duration / 60)}分钟` : '-' },
  ]

  const isVideoType = info && (info.link_type === 'video' || info.link_type === 'collection')
  // 单集模式: 即使视频属于合集, 列表也只显示当前这一集 (从合集里捞它的时长/日期)
  const episodes: Episode[] = (() => {
    if (!info) return []
    if (parseMode === 'collection' && info.is_collection && info.collection) {
      return info.collection.episodes
    }
    if (info.aid) {
      const ep = info.collection?.episodes?.find(e => e.aid === info.aid)
      return [ep || { aid: info.aid, title: info.title || '', date: info.date || '', duration: 0, bvid: '' }]
    }
    return []
  })()

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
        {/* 解析模式开关: 单集=只选当前视频; 整个合集=展开全部并全选 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 14 }}>
          <Text type="secondary" style={{ fontSize: 13 }}>解析模式</Text>
          <Segmented
            value={parseMode}
            onChange={v => changeParseMode(v as ParseMode)}
            options={[
              { label: '单集', value: 'single' },
              { label: '整个合集', value: 'collection' },
            ]}
          />
          {info?.is_collection && parseMode === 'single' && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              该视频属于合集「{info.collection?.title}」, 切到「整个合集」可展开全部 {info.collection?.episodes.length} 集
            </Text>
          )}
        </div>
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
                pagination={{
                  pageSize,
                  showSizeChanger: true,
                  pageSizeOptions: [20, 50, 100, 200],
                  showTotal: t => `共 ${t} 集`,
                  onShowSizeChange: (_, size) => {
                    setPageSize(size)
                    localStorage.setItem(LS_PAGE_SIZE, String(size))
                  },
                }}
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
                  loading={starting}
                  disabled={selected.length === 0}
                  block={isMobile}
                >
                  下载 {selected.length} 集
                </Button>
              </div>
            </Card>

            {/* 下载任务: 全部任务(合集名+集数进度), 多任务同时可见, 可排队多个 */}
            {tasks.length > 0 && (
              <Card
                className="glass-card anim-enter anim-delay-4"
                title={
                  <Space>
                    <UnorderedListOutlined style={{ color: 'var(--accent)' }} />
                    <span>下载任务</span>
                    <Tag color="orange" style={{ borderRadius: 999 }}>{tasks.length}</Tag>
                  </Space>
                }
              >
                {tasks.map(t => <TaskItem key={t.task_id} t={t} onAction={refreshTasks} />)}
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
