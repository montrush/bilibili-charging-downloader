// 超电磁炮风格背景装饰 - 原创SVG手绘(无版权素材):
// 电弧(biribiri) + 御坂金币(翻转动画) + 火花粒子.
// 仅当皮肤 deco='railgun' 时渲染. arcs=false 时只渲染金币(常盘台定稿).

function Arc({ d, branches, className }: { d: string; branches?: string[]; className: string }) {
  return (
    <svg className={`railgun-arc ${className}`} viewBox="0 0 480 260" fill="none">
      <path d={d} stroke="currentColor" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round" />
      {(branches || []).map((b, i) => (
        <path key={i} d={b} stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.75" />
      ))}
    </svg>
  )
}

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

export default function RailgunDeco({ arcs = true }: { arcs?: boolean }) {
  return (
    <div className="railgun-deco">
      {arcs && (
        <>
          {/* 左上电弧 */}
          <Arc
            className="arc-tl"
            d="M0,190 L58,150 L82,178 L138,128 L166,162 L226,112 L254,142 L318,92 L348,124 L414,72 L440,100 L480,60"
            branches={[
              'M138,128 L158,96 L178,104',
              'M254,142 L276,170 L300,158',
              'M348,124 L372,148',
            ]}
          />
          {/* 右下电弧 */}
          <Arc
            className="arc-br"
            d="M480,80 L420,116 L396,90 L340,140 L312,108 L252,158 L224,128 L160,178 L132,148 L66,198 L40,170 L0,210"
            branches={[
              'M340,140 L320,172 L298,164',
              'M224,128 L202,100 L180,110',
              'M132,148 L108,124',
            ]}
          />
          {/* 火花粒子 */}
          <span className="railgun-spark spark-1" />
          <span className="railgun-spark spark-2" />
          <span className="railgun-spark spark-3" />
          <span className="railgun-spark spark-4" />
          <span className="railgun-spark spark-5" />
        </>
      )}
      {/* 翻转金币 */}
      <Coin />
    </div>
  )
}
