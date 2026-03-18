'use client'

import { useState } from 'react'
import type { Insight } from '@/lib/types'
import { dismissInsight } from '@/lib/api'

interface InsightCardProps {
  insight: Insight
  onDismiss?: (id: string) => void
}

const severityConfig = {
  critical:    { label: 'Kritik',  color: '#dc2626', bg: '#fef2f2', border: '#fecaca', dot: '#dc2626' },
  warning:     { label: 'Uyarı',   color: '#d97706', bg: '#fffbeb', border: '#fde68a', dot: '#d97706' },
  opportunity: { label: 'Fırsat',  color: '#6c47ff', bg: '#f0ecff', border: '#c4b5fd', dot: '#6c47ff' },
}

const categoryLabels: Record<string, string> = {
  revenue: 'Gelir', traffic: 'Trafik', funnel: 'Dönüşüm', campaign: 'Kampanya', product: 'Ürün',
}

export default function InsightCard({ insight, onDismiss }: InsightCardProps) {
  const [expanded, setExpanded] = useState(false)
  const [dismissed, setDismissed] = useState(false)
  const cfg = severityConfig[insight.severity] ?? severityConfig.warning

  const handleDismiss = async (e: React.MouseEvent) => {
    e.stopPropagation()
    try { await dismissInsight(insight.id); setDismissed(true); onDismiss?.(insight.id) } catch {}
  }

  if (dismissed) return null

  return (
    <div
      className="card"
      style={{ padding: '16px 20px', cursor: 'pointer' }}
      onClick={() => setExpanded(!expanded)}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', flex: 1, minWidth: 0 }}>
          <span style={{ flexShrink: 0, marginTop: '4px', width: '7px', height: '7px', borderRadius: '50%', background: cfg.dot }} />
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap', marginBottom: '5px' }}>
              <span className="tag" style={{ fontSize: '11px', fontWeight: 600, color: cfg.color, background: cfg.bg, borderColor: cfg.border }}>
                {cfg.label}
              </span>
              <span style={{ fontSize: '12px', color: '#6a7890' }}>
                {categoryLabels[insight.category] || insight.category}
              </span>
            </div>
            <p style={{ fontSize: '14px', fontWeight: 500, color: '#101726', lineHeight: 1.5 }}>
              {insight.title}
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexShrink: 0 }}>
          {insight.impact_tl && (
            <span className="tag" style={{ fontSize: '12px', fontWeight: 600, color: '#16a34a', background: '#f0fdf4', borderColor: '#bbf7d0' }}>
              ₺{insight.impact_tl.toLocaleString('tr-TR', { maximumFractionDigits: 0 })} etki
            </span>
          )}
          <span style={{ fontSize: '11px', color: '#6a7890' }}>{expanded ? '▲' : '▼'}</span>
        </div>
      </div>

      {expanded && (
        <div style={{ marginTop: '14px', paddingTop: '14px', borderTop: '1px solid #e8ecf2', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div>
            <p style={{ fontSize: '11px', fontWeight: 600, color: '#6a7890', letterSpacing: '0.05em', textTransform: 'uppercase', marginBottom: '4px' }}>Bulgu</p>
            <p style={{ fontSize: '13px', color: '#3f4b60', lineHeight: 1.65 }}>{insight.finding}</p>
          </div>
          <div>
            <p style={{ fontSize: '11px', fontWeight: 600, color: '#6a7890', letterSpacing: '0.05em', textTransform: 'uppercase', marginBottom: '4px' }}>Neden</p>
            <p style={{ fontSize: '13px', color: '#3f4b60', lineHeight: 1.65 }}>{insight.cause}</p>
          </div>
          <div style={{ background: '#f0ecff', border: '1px solid #c4b5fd', borderRadius: '10px', padding: '12px 14px' }}>
            <p style={{ fontSize: '11px', fontWeight: 600, color: '#6c47ff', letterSpacing: '0.05em', textTransform: 'uppercase', marginBottom: '4px' }}>Önerilen Aksiyon</p>
            <p style={{ fontSize: '13px', color: '#4c3397', lineHeight: 1.65 }}>{insight.action}</p>
          </div>
          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button
              onClick={handleDismiss}
              style={{ fontSize: '13px', color: '#6a7890', background: 'none', border: 'none', cursor: 'pointer', transition: 'color 180ms ease' }}
              onMouseEnter={e => { (e.currentTarget as HTMLElement).style.color = '#101726' }}
              onMouseLeave={e => { (e.currentTarget as HTMLElement).style.color = '#6a7890' }}
            >
              Kapat
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
