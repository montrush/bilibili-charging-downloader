import { Avatar } from 'antd'
import { GithubOutlined, PlayCircleOutlined, StockOutlined } from '@ant-design/icons'

// 作者信息
const AUTHOR = {
  name: '侯plus',
  avatar: '/avatar.png', // GitHub头像(本地化, 避免外网加载失败)
  links: [
    { key: 'github', label: 'GitHub', url: 'https://github.com/montrush', icon: <GithubOutlined /> },
    { key: 'bili', label: 'B站主页', url: 'https://space.bilibili.com/8792163', icon: <PlayCircleOutlined /> },
    { key: 'xueqiu', label: '雪球', url: 'https://xueqiu.com/u/2347043226', icon: <StockOutlined /> },
  ],
}

export default function AuthorFooter() {
  return (
    <footer className="author-footer">
      <div className="author-footer-inner">
        <Avatar size={44} src={AUTHOR.avatar} className="author-avatar" />
        <span className="author-name">{AUTHOR.name}</span>
        <span className="author-divider" />
        {AUTHOR.links.map(l => (
          <a key={l.key} href={l.url} target="_blank" rel="noopener noreferrer" className="author-link">
            {l.icon}
            <span>{l.label}</span>
          </a>
        ))}
      </div>
    </footer>
  )
}
