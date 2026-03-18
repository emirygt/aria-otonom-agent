'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Sidebar from '@/components/Sidebar'
import InsightCard from '@/components/InsightCard'
import { getInsights, generateInsights } from '@/lib/api'
import type { Insight } from '@/lib/types'

export default function InsightsPage() {
  const router = useRouter()
  const [insights, setInsights] = useState<Insight[]>([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [filter, setFilter] = useState<'all' | 'critical' | 'warning' | 'opportunity'>('all')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const token = localStorage.getItem('aria_token')
    if (!token) { router.push('/login'); return }
    getInsights().then(setInsights).catch(() => setError("Yüklenemedi")).finally(() => setLoading(false))
  }, [router])

  const handleGenerate = async () => {
    setGenerating(true); setError(null)
    try { setInsights(await generateInsights()) }
    catch { setError('Insight üretilemedi.') }
    finally { setGenerating(false) }
  }

  const counts = {
    critical: insights.filter(i => i.severity === 'critical').length,
    warning: insights.filter(i => i.severity === 'warning').length,
    opportunity: insights.filter(i => i.severity === 'opportunity').length,
  }
  const filtered = filter === 'all' ? insights : insights.filter(i => i.severity === filter)

  const filterItems = [
    { key: 'all', label: 'Tümü' },
    { key: 'critical', label: `Kritik · ${counts.critical}` },
    { key: 'warning', label: `Uyarı · ${counts.warning}` },
    { key: 'opportunity', label: `Fırsat · ${counts.opportunity}` },
  ] as const

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#f3f5f8' }}>
      <Sidebar />
      <main style={{ flex: 1, overflow: 'auto' }}>
        <header style={{ background: '#fff', borderBottom: '1px solid #d8dfea', padding: '0 28px', height: '56px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', position: 'sticky', top: 0, zIndex: 10 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <h1 style={{ fontSize: '15px', fontWeight: 700, color: '#101726', letterSpacing: '-0.02em' }}>Insight&apos;lar</h1>
            {/* Filter tabs */}
            <div style={{ display: 'flex', gap: '2px' }}>
              {filterItems.map(item => (
                <button
                  key={item.key}
                  onClick={() => setFilter(item.key)}
                  style={{
                    fontSize: '13px', fontWeight: 500, padding: '5px 11px', borderRadius: '7px',
                    border: '1px solid', cursor: 'pointer', transition: 'all 150ms ease',
                    color: filter === item.key ? '#6c47ff' : '#6a7890',
                    background: filter === item.key ? '#f0ecff' : 'transparent',
                    borderColor: filter === item.key ? '#c4b5fd' : 'transparent',
                  }}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>
          <button onClick={handleGenerate} disabled={generating} className="btn-primary" style={{ fontSize: '13px', padding: '7px 14px' }}>
            {generating ? (
              <>
                <span style={{ width: '11px', height: '11px', border: '2px solid rgba(255,255,255,0.35)', borderTopColor: '#fff', borderRadius: '50%', animation: 'spin 0.7s linear infinite' }} />
                Analiz...
              </>
            ) : <>
              <svg width="12" height="12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Yeni Analiz
            </>}
          </button>
        </header>

        <div style={{ padding: '24px 28px', display: 'flex', flexDirection: 'column', gap: '16px', maxWidth: '1200px' }}>
          {/* Summary pills */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
            {[
              { key: 'critical', label: 'Kritik', count: counts.critical, color: '#dc2626', bg: '#fef2f2', border: '#fecaca' },
              { key: 'warning', label: 'Uyarı', count: counts.warning, color: '#d97706', bg: '#fffbeb', border: '#fde68a' },
              { key: 'opportunity', label: 'Fırsat', count: counts.opportunity, color: '#6c47ff', bg: '#f0ecff', border: '#c4b5fd' },
            ].map(item => (
              <div
                key={item.key}
                className="card"
                style={{ padding: '14px 18px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer', background: filter === item.key ? item.bg : '#fff', borderColor: filter === item.key ? item.border : '#d8dfea' }}
                onClick={() => setFilter(filter === item.key ? 'all' : item.key as 'critical' | 'warning' | 'opportunity')}
              >
                <span style={{ fontSize: '13px', color: '#3f4b60', fontWeight: 500 }}>{item.label}</span>
                <span style={{ fontSize: '20px', fontWeight: 800, color: item.color, letterSpacing: '-0.04em' }}>{item.count}</span>
              </div>
            ))}
          </div>

          {error && (
            <div style={{ fontSize: '13px', color: '#dc2626', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', padding: '10px 14px' }}>{error}</div>
          )}

          {loading ? (
            <div style={{ padding: '48px', textAlign: 'center', color: '#6a7890', fontSize: '14px' }}>Yükleniyor...</div>
          ) : filtered.length === 0 ? (
            <div style={{ background: '#fff', border: '1px solid #d8dfea', borderRadius: '14px', padding: '56px', textAlign: 'center' }}>
              <p style={{ fontSize: '14px', color: '#6a7890', marginBottom: '6px' }}>
                {filter === 'all' ? 'Henüz insight yok' : 'Bu kategoride insight yok'}
              </p>
              <button onClick={handleGenerate} disabled={generating} className="btn-primary" style={{ fontSize: '13px', marginTop: '14px' }}>
                Analizi başlat →
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {filtered.map(insight => (
                <InsightCard key={insight.id} insight={insight} onDismiss={id => setInsights(prev => prev.filter(i => i.id !== id))} />
              ))}
            </div>
          )}
        </div>
      </main>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}
