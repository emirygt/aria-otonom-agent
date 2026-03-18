import type { HealthScoreSummary } from '@/lib/types'

interface HealthScoreProps {
  data: HealthScoreSummary
}

function scoreConfig(score: number) {
  if (score >= 80) return { stroke: '#16a34a', color: '#16a34a', bg: '#f0fdf4', border: '#bbf7d0', label: 'Sağlıklı' }
  if (score >= 60) return { stroke: '#d97706', color: '#d97706', bg: '#fffbeb', border: '#fde68a', label: 'Orta' }
  return { stroke: '#dc2626', color: '#dc2626', bg: '#fef2f2', border: '#fecaca', label: 'Kritik' }
}

export default function HealthScore({ data }: HealthScoreProps) {
  const circumference = 2 * Math.PI * 36
  const progress = (data.score / 100) * circumference
  const cfg = scoreConfig(data.score)

  return (
    <div className="card" style={{ padding: '18px 20px', height: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
        <p style={{ fontSize: '13px', color: '#6a7890', fontWeight: 500 }}>Analytics Health</p>
        <span className="tag" style={{ fontSize: '12px', fontWeight: 600, color: cfg.color, background: cfg.bg, borderColor: cfg.border }}>
          {cfg.label}
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ position: 'relative', flexShrink: 0 }}>
          <svg width="86" height="86" viewBox="0 0 86 86">
            <circle cx="43" cy="43" r="36" fill="none" stroke="#e8ecf2" strokeWidth="5" />
            <circle
              cx="43" cy="43" r="36" fill="none"
              stroke={cfg.stroke} strokeWidth="5" strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={circumference - progress}
              transform="rotate(-90 43 43)"
              style={{ transition: 'stroke-dashoffset 0.9s ease' }}
            />
          </svg>
          <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ fontSize: '20px', fontWeight: 800, color: cfg.color, letterSpacing: '-0.04em', lineHeight: 1 }}>{data.score}</span>
            <span style={{ fontSize: '10px', color: '#6a7890', marginTop: '1px' }}>/100</span>
          </div>
        </div>

        <div style={{ flex: 1, minWidth: 0 }}>
          <p style={{ fontSize: '12px', color: '#6a7890', fontWeight: 500, marginBottom: '8px' }}>Öne çıkan sorunlar</p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {data.top_issues.slice(0, 3).map((issue, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: '7px' }}>
                <span style={{ flexShrink: 0, marginTop: '6px', width: '4px', height: '4px', borderRadius: '50%', background: '#dc2626' }} />
                <span style={{ fontSize: '12px', color: '#3f4b60', lineHeight: 1.55 }}>{issue}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
