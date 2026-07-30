// 皮肤切换器: 淡/暗快速切换 + 全部皮肤下拉(带预览圆点).
import { Button, Dropdown, Tooltip } from 'antd'
import { SunOutlined, MoonOutlined, BgColorsOutlined, CheckOutlined } from '@ant-design/icons'
import { SKINS } from '../theme/skins'
import { useSkin } from '../theme/ThemeContext'

export default function SkinSwitcher() {
  const { skin, setSkin, toggleMode } = useSkin()

  const items = [
    {
      key: 'light-group',
      type: 'group' as const,
      label: '淡色系',
      children: SKINS.filter(s => s.mode === 'light').map(s => ({
        key: s.id,
        icon: <span className="skin-dot" style={{ background: s.preview }} />,
        label: (
          <span style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 16 }}>
            {s.name}
            {s.id === skin.id && <CheckOutlined style={{ color: 'var(--accent)' }} />}
          </span>
        ),
        onClick: () => setSkin(s.id),
      })),
    },
    {
      key: 'dark-group',
      type: 'group' as const,
      label: '暗色系',
      children: SKINS.filter(s => s.mode === 'dark').map(s => ({
        key: s.id,
        icon: <span className="skin-dot" style={{ background: s.preview }} />,
        label: (
          <span style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 16 }}>
            {s.name}
            {s.id === skin.id && <CheckOutlined style={{ color: 'var(--accent)' }} />}
          </span>
        ),
        onClick: () => setSkin(s.id),
      })),
    },
  ]

  return (
    <div style={{ display: 'flex', gap: 8 }}>
      <Tooltip title={skin.mode === 'light' ? '切换到暗色系' : '切换到淡色系'}>
        <Button
          className="icon-btn"
          icon={skin.mode === 'light' ? <MoonOutlined /> : <SunOutlined />}
          onClick={toggleMode}
        />
      </Tooltip>
      <Dropdown menu={{ items }} trigger={['click']} placement="bottomRight">
        <Button className="icon-btn" icon={<BgColorsOutlined />}>
          {skin.name}
        </Button>
      </Dropdown>
    </div>
  )
}
