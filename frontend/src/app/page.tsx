'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Sidebar from '@/components/Sidebar'
import MetricCard from '@/components/MetricCard'
import HealthScore from '@/components/HealthScore'
import InsightCard from '@/components/InsightCard'
import TrendChart from '@/components/TrendChart'
import { getOverview, getInsights, generateInsights, getTrends, getIntegrationStatus } from '@/lib/api'
import type { OverviewData, Insight, IntegrationStatus } from '@/lib/types'

interface TrendPoint { date: string; revenue: number; sessions: number }

export default function Dashboard() {
  const router = useRouter()
  const [overview, setOverview] = useState<OverviewData | null>(null)
  const [insights, setInsights] = useState<Insight[]>([])
  const [trends, setTrends] = useState<TrendPoint[]>([])
  const [integrationStatus, setIntegrationStatus] = useState<IntegrationStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [activeChart, setActiveChart] = useState<'revenue' | 'sessions'>('revenue')
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false)

  useEffect(() => {
    const token = localStorage.getItem('aria_token')
    if (!token) { router.push('/login'); return }
    Promise.all([getOverview(), getInsights(), getTrends(), getIntegrationStatus()])
      .then(([ov, ins, tr, st]) => {
        setOverview(ov)
        setInsights(ins)
        setTrends(tr.weekly || [])
        setIntegrationStatus(st)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [router])

  const handleGenerate = async () => {
    setGenerating(true)
    try { setInsights(await generateInsights()) }
    catch {}
    finally { setGenerating(false) }
  }

  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', background: '#f3f5f8' }}>
      <p style={{ fontSize: '14px', color: '#6a7890' }}>Yükleniyor...</p>
    </div>
  )

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#f3f5f8' }}>
      {/* Mobile overlay */}
      {mobileSidebarOpen && (
        <div
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.3)', zIndex: 40 }}
          onClick={() => setMobileSidebarOpen(false)}
        />
      )}

      {/* Sidebar — hidden on mobile unless open */}
      <div style={{
        position: 'fixed' as const, top: 0, left: 0, bottom: 0, zIndex: 50,
        transform: mobileSidebarOpen ? 'translateX(0)' : 'translateX(-100%)',
        transition: 'transform 250ms ease',
      }} className="mobile-sidebar-panel">
        <Sidebar />
      </div>

      {/* Sidebar — always visible on desktop */}
      <div className="desktop-sidebar">
        <Sidebar />
      </div>

      <main style={{ flex: 1, overflow: 'auto', minWidth: 0 }}>
        {/* Header */}
        <header style={{
          background: '#fff', borderBottom: '1px solid #d8dfea',
          padding: '0 20px', height: '56px',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          position: 'sticky', top: 0, zIndex: 10,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {/* Mobile menu button */}
            <button
              className="mobile-menu-btn"
              onClick={() => setMobileSidebarOpen(true)}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#6a7890', padding: '4px', display: 'none' }}
            >
              <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <h1 style={{ fontSize: '15px', fontWeight: 700, color: '#101726', letterSpacing: '-0.02em' }}>Dashboard</h1>
            <span className="tag" style={{ fontSize: '12px', fontWeight: 500, color: '#16a34a', background: '#f0fdf4', borderColor: '#bbf7d0', display: 'flex', alignItems: 'center', gap: '5px' }}>
              <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#16a34a', animation: 'pulse 2s ease infinite' }} />
              Canlı
            </span>
          </div>
          <span style={{ fontSize: '13px', color: '#6a7890' }}>
            {new Date().toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}
          </span>
        </header>

        <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>

          {/* Veri kaynağı banner */}
          {overview?.data_source === 'mock' && (
            <div style={{ background: integrationStatus?.ga4 ? '#fffbeb' : '#f0ecff', border: `1px solid ${integrationStatus?.ga4 ? '#fde68a' : '#c4b5fd'}`, borderRadius: '12px', padding: '12px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px' }}>
              <p style={{ fontSize: '13px', color: integrationStatus?.ga4 ? '#92400e' : '#4c3397' }}>
                {integrationStatus?.ga4
                  ? '⚠️ Google Analytics hesabınızda henüz veri bulunmuyor. Gösterilen veriler örnek amaçlıdır.'
                  : '📊 Gerçek verilerinizi görmek için Google Analytics\'i bağlayın.'}
              </p>
              {!integrationStatus?.ga4 && (
                <a href="/integrations" style={{ fontSize: '12px', fontWeight: 600, color: '#6c47ff', whiteSpace: 'nowrap', textDecoration: 'none' }}>Bağla →</a>
              )}
            </div>
          )}

          {/* Health + Metrics */}
          <div className="grid-health">
            <div>{overview && <HealthScore data={overview.health_score} />}</div>
            <div className="grid-metrics">
              {overview && (
                <>
                  <MetricCard title="Gelir (TL)" metric={overview.revenue_tl} format="currency" />
                  <MetricCard title="Oturum" metric={overview.sessions} format="number" />
                  <MetricCard title="Dönüşüm Oranı" metric={overview.conversion_rate} format="percent" />
                  <MetricCard title="ROAS" metric={overview.roas} format="multiplier" />
                </>
              )}
            </div>
          </div>

          {/* Trend Chart */}
          {trends.length > 0 && (
            <div className="card" style={{ padding: '18px 20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
                <h2 style={{ fontSize: '14px', fontWeight: 700, color: '#101726', letterSpacing: '-0.01em' }}>14 Günlük Trend</h2>
                <div style={{ display: 'flex', gap: '4px' }}>
                  {([
                    { key: 'revenue', label: 'Gelir', color: '#6c47ff' },
                    { key: 'sessions', label: 'Oturum', color: '#2563eb' },
                  ] as const).map(tab => (
                    <button
                      key={tab.key}
                      onClick={() => setActiveChart(tab.key)}
                      style={{
                        fontSize: '12px', fontWeight: 500, padding: '5px 10px', borderRadius: '7px',
                        border: '1px solid', cursor: 'pointer', transition: 'all 150ms ease',
                        color: activeChart === tab.key ? tab.color : '#6a7890',
                        background: activeChart === tab.key ? (tab.key === 'revenue' ? '#f0ecff' : '#eff6ff') : 'transparent',
                        borderColor: activeChart === tab.key ? (tab.key === 'revenue' ? '#c4b5fd' : '#bfdbfe') : 'transparent',
                      }}
                    >
                      {tab.label}
                    </button>
                  ))}
                </div>
              </div>
              <TrendChart
                data={trends}
                metric={activeChart}
                color={activeChart === 'revenue' ? '#6c47ff' : '#2563eb'}
              />
            </div>
          )}

          {/* Insights */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h2 style={{ fontSize: '14px', fontWeight: 700, color: '#101726', letterSpacing: '-0.01em' }}>AI Insight&apos;lar</h2>
                <span className="tag" style={{ fontSize: '11px', color: '#6a7890', background: '#f3f5f8', borderColor: '#d8dfea' }}>
                  {insights.length} aktif
                </span>
              </div>
              <button onClick={handleGenerate} disabled={generating} className="btn-primary" style={{ fontSize: '12px', padding: '6px 12px' }}>
                {generating ? (
                  <>
                    <span style={{ width: '11px', height: '11px', border: '2px solid rgba(255,255,255,0.35)', borderTopColor: '#fff', borderRadius: '50%', animation: 'spin 0.7s linear infinite' }} />
                    Analiz...
                  </>
                ) : 'Yenile'}
              </button>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {insights.length === 0 ? (
                <div style={{ background: '#fff', border: '1px solid #d8dfea', borderRadius: '14px', padding: '40px', textAlign: 'center' }}>
                  <p style={{ fontSize: '14px', color: '#6a7890' }}>Henüz insight yok</p>
                </div>
              ) : insights.map(insight => (
                <InsightCard key={insight.id} insight={insight} onDismiss={id => setInsights(prev => prev.filter(i => i.id !== id))} />
              ))}
            </div>
          </div>
        </div>
      </main>

      <style>{`
        @keyframes spin  { to { transform: rotate(360deg); } }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }

        .grid-health {
          display: grid;
          grid-template-columns: 1fr 2fr;
          gap: 14px;
        }
        .grid-metrics {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 14px;
        }
        .desktop-sidebar { display: flex; }
        .mobile-sidebar-panel { display: none; }
        .mobile-menu-btn { display: none !important; }

        @media (max-width: 768px) {
          .desktop-sidebar { display: none; }
          .mobile-sidebar-panel { display: flex !important; }
          .mobile-menu-btn { display: flex !important; }
          .grid-health { grid-template-columns: 1fr; }
          .grid-metrics { grid-template-columns: 1fr 1fr; }
        }
        @media (max-width: 480px) {
          .grid-metrics { grid-template-columns: 1fr; }
        }
      `}</style>
    </div>
  )
}
