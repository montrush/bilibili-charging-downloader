// 超电磁炮风格背景装饰 - 原创SVG手绘(无版权素材):
// 御坂金币(翻转动画). 用户定稿: 只保留金币, 去掉电弧和火花粒子.
// 仅当皮肤 deco='railgun' 时渲染.

function Coin() {
  return (
    <svg className="railgun-coin" viewBox="0 0 100 100" fill="none">
      <defs>
        <radialGradient id="coin-face" cx="38%" cy="32%" r="80%">
          <stop offset="0%" stopColor="#fde68a" />
          <stop offset="55%" stopColor="#fbbf24" />
          <stop offset="100%" stopColor="#d97706" />
        </radialGradient>
      </defs>
      <circle cx="50" cy="50" r="46" fill="url(#coin-face)" stroke="#b45309" strokeWidth="2.5" />
      <circle cx="50" cy="50" r="38" fill="none" stroke="#92400e" strokeWidth="1.5" opacity="0.55" />
      {/* 闪电刻印 */}
      <path
        d="M54 22 L38 52 L48 52 L44 78 L64 44 L53 44 L60 22 Z"
        fill="#fff7ed" stroke="#92400e" strokeWidth="2" strokeLinejoin="round"
      />
    </svg>
  )
}

export default function RailgunDeco() {
  return (
    <div className="railgun-deco">
      {/* 翻转金币 */}
      <Coin />
    </div>
  )
}
