import type { MetricValue } from '@/lib/types'

interface MetricCardProps {
  title: string
  metric: MetricValue
  format?: 'currency' | 'number' | 'percent' | 'multiplier'
}

function formatValue(value: number, format: MetricCardProps['format']): string {
  switch (format) {
    case 'currency': return '₺' + value.toLocaleString('tr-TR', { maximumFractionDigits: 0 })
    case 'percent':  return '%' + value.toFixed(1)
    case 'multiplier': return value.toFixed(1) + 'x'
    default: return value.toLocaleString('tr-TR', { maximumFractionDigits: 0 })
  }
}

export default function MetricCard({ title, metric, format = 'number' }: MetricCardProps) {
  const isPositive = metric.change_pct > 0
  const isNeutral  = metric.change_pct === 0

  const changeStyle = isNeutral
    ? { color: '#6a7890', bg: '#f3f5f8', border: '#d8dfea' }
    : isPositive
    ? { color: '#16a34a', bg: '#f0fdf4', border: '#bbf7d0' }
    : { color: '#dc2626', bg: '#fef2f2', border: '#fecaca' }

  return (
    <div className="card" style={{ padding: '18px 20px' }}>
      <p style={{ fontSize: '13px', color: '#6a7890', fontWeight: 500, marginBottom: '8px' }}>{title}</p>
      <p style={{ fontSize: '24px', fontWeight: 700, color: '#101726', letterSpacing: '-0.03em', lineHeight: 1.15, marginBottom: '10px' }}>
        {formatValue(metric.value, format)}
      </p>
      <span
        className="tag"
        style={{ fontSize: '12px', color: changeStyle.color, background: changeStyle.bg, borderColor: changeStyle.border }}
      >
        {isNeutral ? '—' : isPositive ? '↑' : '↓'} {isNeutral ? '0%' : `%${Math.abs(metric.change_pct).toFixed(1)}`}
        <span style={{ color: '#6a7890', fontWeight: 400 }}>önceki</span>
      </span>
    </div>
  )
}
