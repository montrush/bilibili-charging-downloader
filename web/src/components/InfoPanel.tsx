// 状态窗口: 封面/UP主/合集信息/数据统计/简介/下载状态 (PC左栏sticky).
import { Avatar, Tag, Typography } from 'antd'
import {
  PlayCircleOutlined, MessageOutlined, LikeOutlined,
  DollarOutlined, StarOutlined, ShareAltOutlined,
  CheckCircleFilled, SyncOutlined, ClockCircleOutlined,
} from '@ant-design/icons'

const { Text, Paragraph } = Typography

export interface StatInfo {
  view: number; danmaku: number; reply: number
  favorite: number; coin: number; share: number; like: number
}

export interface PanelInfo {
  is_collection?: boolean
  title?: string
  owner?: string
  owner_face?: string
  owner_mid?: number
  pic?: string
  desc?: string
  tname?: string
  stat?: StatInfo
  date?: string
  collection: {
    title: string; cover?: string; intro?: string
    ep_count?: number; stat?: StatInfo; episodes: { duration: number; date: string }[]
  } | null
}

export function fmtNum(n?: number): string {
  if (!n) return '0'
  if (n >= 1e8) return (n / 1e8).toFixed(1) + '亿'
  if (n >= 1e4) return (n / 1e4).toFixed(1) + '万'
  return String(n)
}

function fmtDuration(totalSec: number): string {
  const h = Math.floor(totalSec / 3600)
  const m = Math.round((totalSec % 3600) / 60)
  if (h > 0) return `${h}小时${m > 0 ? m + '分' : ''}`
  return `${m}分钟`
}

interface Props {
  info: PanelInfo
  selectedCount: number
  episodeCount: number
  downloading: boolean
  progress: { done: number; total: number; status: string } | null
}

export default function InfoPanel({ info, selectedCount, episodeCount, downloading, progress }: Props) {
  const isColl = Boolean(info.is_collection && info.collection)
  const cover = isColl ? (info.collection!.cover || info.pic) : info.pic
  const title = isColl ? info.collection!.title : (info.title || '')
  const desc = isColl ? (info.collection!.intro || info.desc) : info.desc
  const stat = (isColl && info.collection!.stat && info.collection!.stat!.view)
    ? info.collection!.stat! : (info.stat || {} as StatInfo)
  const episodes = isColl ? info.collection!.episodes : []
  const totalSec = episodes.reduce((s, e) => s + (e.duration || 0), 0)
  const dateRange = isColl && episodes.length > 1
    ? `${episodes[0].date} ~ ${episodes[episodes.length - 1].date}` : (info.date || '')

  const status = progress?.status === 'done' ? 'done' : downloading ? 'downloading' : 'idle'

  const stats: { icon: React.ReactNode; label: string; value?: number }[] = [
    { icon: <PlayCircleOutlined />, label: '播放', value: stat.view },
    { icon: <MessageOutlined />, label: '弹幕', value: stat.danmaku },
    { icon: <LikeOutlined />, label: '点赞', value: stat.like },
    { icon: <DollarOutlined />, label: '投币', value: stat.coin },
    { icon: <StarOutlined />, label: '收藏', value: stat.favorite },
    { icon: <ShareAltOutlined />, label: '分享', value: stat.share },
  ]

  return (
    <div className="info-panel">
      {cover && (
        <div className="info-cover-wrap">
          <img className="info-cover" src={cover} alt={title} referrerPolicy="no-referrer" />
          <span className="info-cover-badge">{isColl ? `合集 · ${episodeCount}集` : '单视频'}</span>
        </div>
      )}

      <h3 className="info-title">{title}</h3>

      {info.owner && (
        <div className="info-owner">
          <Avatar size={26} src={info.owner_face}>
            {info.owner[0]}
          </Avatar>
          <span>{info.owner}</span>
          {info.tname && <Tag className="info-tag">{info.tname}</Tag>}
        </div>
      )}

      <div className="stat-grid">
        {stats.map(s => (
          <div className="stat-item" key={s.label}>
            <span className="stat-icon">{s.icon}</span>
            <span className="stat-value">{fmtNum(s.value)}</span>
            <span className="stat-label">{s.label}</span>
          </div>
        ))}
      </div>

      <div className="info-meta">
        {totalSec > 0 && (
          <div className="info-meta-row">
            <ClockCircleOutlined /><span>总时长 {fmtDuration(totalSec)}</span>
          </div>
        )}
        {dateRange && (
          <div className="info-meta-row">
            <span className="meta-label">发布时间</span><span>{dateRange}</span>
          </div>
        )}
      </div>

      {desc && (
        <Paragraph className="info-desc" ellipsis={{ rows: 3, expandable: true, symbol: '展开' }}>
          {desc}
        </Paragraph>
      )}

      {/* 下载状态 */}
      <div className="dl-status">
        {status === 'done' ? (
          <><CheckCircleFilled style={{ color: '#22c55e' }} /><span>下载完成 {progress!.done}/{progress!.total}</span></>
        ) : status === 'downloading' ? (
          <><SyncOutlined spin style={{ color: 'var(--accent)' }} /><span>下载中 {progress!.done}/{progress!.total}</span></>
        ) : (
          <><span className="dl-dot" /><span>已选 <b className="gradient-text">{selectedCount}</b> / {episodeCount} 集</span></>
        )}
      </div>
    </div>
  )
}
