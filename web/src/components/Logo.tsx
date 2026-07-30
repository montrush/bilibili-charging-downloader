// 应用Logo: 渐变圆角方块 + 播放三角.
export default function Logo({ size = 36 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" fill="none">
      <defs>
        <linearGradient id="logo-grad" x1="0" y1="0" x2="48" y2="48" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#fbbf24" />
          <stop offset="55%" stopColor="#f97316" />
          <stop offset="100%" stopColor="#ef4444" />
        </linearGradient>
      </defs>
      <rect x="2" y="2" width="44" height="44" rx="13" fill="url(#logo-grad)" />
      <rect x="2" y="2" width="44" height="44" rx="13" fill="white" opacity="0.08" />
      <path d="M19 15.5v17c0 1.8 2 2.9 3.6 2L36 26.6c1.6-.9 1.6-3.2 0-4.1L22.6 13.4c-1.6-.9-3.6.2-3.6 2.1z" fill="white" />
      <path d="M14 38.5h20" stroke="white" strokeWidth="2.6" strokeLinecap="round" opacity="0.85" />
    </svg>
  )
}
