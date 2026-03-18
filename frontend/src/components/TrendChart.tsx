'use client'

import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts'

interface TrendPoint {
  date: string
  revenue: number
  sessions: number
}

interface Props {
  data: TrendPoint[]
  metric: 'revenue' | 'sessions'
  color?: string
}

function formatY(value: number, metric: Props['metric']) {
  if (metric === 'revenue') {
    return value >= 1000 ? `₺${(value / 1000).toFixed(0)}K` : `₺${value}`
  }
  return value >= 1000 ? `${(value / 1000).toFixed(1)}K` : String(value)
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function CustomTooltip({ active, payload, label, metric }: any) {
  if (!active || !payload?.length) return null
  const val = payload[0].value
  return (
    <div style={{
      background: '#fff',
      border: '1px solid #d8dfea',
      borderRadius: '10px',
      padding: '10px 14px',
      boxShadow: '0 4px 16px rgba(16,23,38,0.1)',
      fontSize: '13px',
    }}>
      <p style={{ color: '#6a7890', marginBottom: '4px' }}>{label}</p>
      <p style={{ fontWeight: 700, color: '#101726' }}>
        {metric === 'revenue' ? `₺${val.toLocaleString('tr-TR')}` : val.toLocaleString('tr-TR')}
      </p>
    </div>
  )
}

export default function TrendChart({ data, metric, color = '#6c47ff' }: Props) {
  const gradientId = `grad-${metric}`

  return (
    <ResponsiveContainer width="100%" height={140}>
      <AreaChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.15} />
            <stop offset="100%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="#f0f2f5" strokeDasharray="3 3" vertical={false} />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 11, fill: '#6a7890' }}
          axisLine={false}
          tickLine={false}
          interval={2}
        />
        <YAxis
          tickFormatter={v => formatY(v, metric)}
          tick={{ fontSize: 11, fill: '#6a7890' }}
          axisLine={false}
          tickLine={false}
          width={48}
        />
        <Tooltip content={<CustomTooltip metric={metric} />} />
        <Area
          type="monotone"
          dataKey={metric}
          stroke={color}
          strokeWidth={2}
          fill={`url(#${gradientId})`}
          dot={false}
          activeDot={{ r: 4, fill: color, stroke: '#fff', strokeWidth: 2 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}
