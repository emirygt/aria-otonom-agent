'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Sidebar from '@/components/Sidebar'
import { getCampaigns } from '@/lib/api'
import type { Campaign } from '@/lib/types'

function roasColor(roas: number) {
  if (roas >= 4) return '#16a34a'
  if (roas >= 2) return '#d97706'
  return '#dc2626'
}

export default function CampaignsPage() {
  const router = useRouter()
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('aria_token')
    if (!token) { router.push('/login'); return }
    getCampaigns().then(setCampaigns).finally(() => setLoading(false))
  }, [router])

  const totalSpend = campaigns.reduce((s, c) => s + c.spend_tl, 0)
  const totalRevenue = campaigns.reduce((s, c) => s + c.revenue_tl, 0)
  const avgRoas = totalSpend > 0 ? totalRevenue / totalSpend : 0

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#f3f5f8' }}>
      <Sidebar />
      <main style={{ flex: 1, overflow: 'auto' }}>
        <header style={{ background: '#fff', borderBottom: '1px solid #d8dfea', padding: '0 28px', height: '56px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', position: 'sticky', top: 0, zIndex: 10 }}>
          <h1 style={{ fontSize: '15px', fontWeight: 700, color: '#101726', letterSpacing: '-0.02em' }}>Kampanyalar</h1>
          <span style={{ fontSize: '13px', color: '#6a7890' }}>{campaigns.length} kampanya</span>
        </header>

        <div style={{ padding: '24px 28px', display: 'flex', flexDirection: 'column', gap: '16px', maxWidth: '1200px' }}>
          {/* Summary */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
            {[
              { label: 'Toplam Harcama', value: `₺${totalSpend.toLocaleString('tr-TR')}` },
              { label: 'Toplam Gelir', value: `₺${totalRevenue.toLocaleString('tr-TR')}` },
              { label: 'Ort. ROAS', value: `${avgRoas.toFixed(2)}x`, color: roasColor(avgRoas) },
            ].map(item => (
              <div key={item.label} className="card" style={{ padding: '16px 20px' }}>
                <p style={{ fontSize: '12px', color: '#6a7890', fontWeight: 500, marginBottom: '6px' }}>{item.label}</p>
                <p style={{ fontSize: '22px', fontWeight: 700, color: item.color || '#101726', letterSpacing: '-0.03em' }}>{item.value}</p>
              </div>
            ))}
          </div>

          {/* Table */}
          <div className="card" style={{ overflow: 'hidden' }}>
            {loading ? (
              <div style={{ padding: '48px', textAlign: 'center', color: '#6a7890', fontSize: '14px' }}>Yükleniyor...</div>
            ) : (
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ background: '#f8fafc' }}>
                    {['Kampanya', 'Harcama', 'Gelir', 'ROAS', 'Trend', 'Durum'].map((h, i) => (
                      <th key={h} style={{ padding: '11px 20px', textAlign: i === 0 ? 'left' : 'center', fontSize: '11px', fontWeight: 600, color: '#6a7890', letterSpacing: '0.05em', textTransform: 'uppercase', borderBottom: '1px solid #e8ecf2' }}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {campaigns.map((c, i) => {
                    const trendCfg = c.trend === 'up'
                      ? { label: '↑ Yükseliyor', color: '#16a34a', bg: '#f0fdf4', border: '#bbf7d0' }
                      : c.trend === 'down'
                      ? { label: '↓ Düşüyor', color: '#dc2626', bg: '#fef2f2', border: '#fecaca' }
                      : { label: '— Sabit', color: '#6a7890', bg: '#f3f5f8', border: '#d8dfea' }
                    const statusActive = c.status === 'active'
                    return (
                      <tr
                        key={i}
                        style={{ borderBottom: i < campaigns.length - 1 ? '1px solid #f0f2f5' : 'none', transition: 'background 150ms ease' }}
                        onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = '#fafbfc' }}
                        onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = 'transparent' }}
                      >
                        <td style={{ padding: '13px 20px', fontSize: '14px', fontWeight: 500, color: '#101726' }}>{c.name}</td>
                        <td style={{ padding: '13px 20px', textAlign: 'center', fontSize: '13px', color: '#3f4b60' }}>₺{c.spend_tl.toLocaleString('tr-TR')}</td>
                        <td style={{ padding: '13px 20px', textAlign: 'center', fontSize: '13px', color: '#3f4b60' }}>₺{c.revenue_tl.toLocaleString('tr-TR')}</td>
                        <td style={{ padding: '13px 20px', textAlign: 'center', fontSize: '13px', fontWeight: 700, color: roasColor(c.roas) }}>{c.roas.toFixed(2)}x</td>
                        <td style={{ padding: '13px 20px', textAlign: 'center' }}>
                          <span className="tag" style={{ fontSize: '11px', fontWeight: 500, color: trendCfg.color, background: trendCfg.bg, borderColor: trendCfg.border }}>{trendCfg.label}</span>
                        </td>
                        <td style={{ padding: '13px 20px', textAlign: 'center' }}>
                          <span className="tag" style={{ fontSize: '11px', fontWeight: 500, color: statusActive ? '#16a34a' : '#6a7890', background: statusActive ? '#f0fdf4' : '#f3f5f8', borderColor: statusActive ? '#bbf7d0' : '#d8dfea' }}>
                            {statusActive ? 'Aktif' : 'Durduruldu'}
                          </span>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
