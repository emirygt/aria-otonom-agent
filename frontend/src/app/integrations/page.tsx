'use client'

import { useEffect, useState, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Sidebar from '@/components/Sidebar'
import { getIntegrationStatus } from '@/lib/api'
import api from '@/lib/api'
import type { IntegrationStatus } from '@/lib/types'

const platforms = [
  { key: 'ga4' as keyof IntegrationStatus, name: 'Google Analytics 4', desc: 'Trafik, dönüşüm ve kullanıcı davranışı verilerini analiz edin.', initial: 'G', color: '#2563eb', canConnect: true },
  { key: 'google_ads' as keyof IntegrationStatus, name: 'Google Ads', desc: 'Kampanya harcamalarını, ROAS ve anahtar kelime performansını takip edin.', initial: 'A', color: '#16a34a', canConnect: true },
  { key: 'meta' as keyof IntegrationStatus, name: 'Meta Ads', desc: 'Facebook ve Instagram reklam kampanyalarının performansını görün.', initial: 'M', color: '#1877f2', canConnect: false },
  { key: 'shopify' as keyof IntegrationStatus, name: 'Shopify', desc: 'Mağaza geliri, sipariş ve ürün verilerini senkronize edin.', initial: 'S', color: '#96bf48', canConnect: false },
  { key: 'ticimax' as keyof IntegrationStatus, name: 'Ticimax', desc: 'Ticimax mağazanızın satış ve stok verilerini entegre edin.', initial: 'T', color: '#f97316', canConnect: false },
]

function IntegrationsContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [status, setStatus] = useState<IntegrationStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [connecting, setConnecting] = useState(false)
  const [propertyId, setPropertyId] = useState('')
  const [savingProperty, setSavingProperty] = useState(false)
  const [propertySaved, setPropertySaved] = useState(false)
  const [showPropertyInput, setShowPropertyInput] = useState(false)
  const [customerId, setCustomerId] = useState('')
  const [savingCustomer, setSavingCustomer] = useState(false)
  const [customerSaved, setCustomerSaved] = useState(false)

  useEffect(() => {
    const token = localStorage.getItem('aria_token')
    if (!token) { router.push('/login'); return }
    getIntegrationStatus().then(s => {
      setStatus(s)
      // GA4 yeni bağlandıysa veya bağlıysa property ID giriş alanını göster
      if (searchParams.get('ga4') === 'connected' || s.ga4) {
        setShowPropertyInput(true)
      }
    }).finally(() => setLoading(false))
  }, [router, searchParams])

  const handleConnectGoogle = async () => {
    setConnecting(true)
    try {
      const res = await api.get('/api/v1/integrations/google/connect')
      window.location.href = res.data.url
    } catch {
      setConnecting(false)
    }
  }

  const handleDisconnectGA4 = async () => {
    try {
      await api.delete('/api/v1/integrations/ga4')
      setStatus(prev => prev ? { ...prev, ga4: false } : prev)
      setShowPropertyInput(false)
      setPropertySaved(false)
    } catch {}
  }

  const handleDisconnectAds = async () => {
    try {
      await api.delete('/api/v1/integrations/google_ads')
      setStatus(prev => prev ? { ...prev, google_ads: false } : prev)
      setCustomerSaved(false)
    } catch {}
  }

  const handleSaveCustomer = async () => {
    if (!customerId.trim()) return
    setSavingCustomer(true)
    try {
      await api.post('/api/v1/integrations/google_ads/customer', { property_id: customerId.trim() })
      setCustomerSaved(true)
    } catch {
    } finally {
      setSavingCustomer(false)
    }
  }

  const handleSaveProperty = async () => {
    if (!propertyId.trim()) return
    setSavingProperty(true)
    try {
      await api.post('/api/v1/integrations/ga4/property', { property_id: propertyId.trim() })
      setPropertySaved(true)
    } catch {
    } finally {
      setSavingProperty(false)
    }
  }

  const connectedCount = status ? Object.values(status).filter(Boolean).length : 0
  const justConnected = searchParams.get('ga4') === 'connected'

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#f3f5f8' }}>
      <Sidebar />
      <main style={{ flex: 1, overflow: 'auto' }}>
        <header style={{ background: '#fff', borderBottom: '1px solid #d8dfea', padding: '0 28px', height: '56px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', position: 'sticky', top: 0, zIndex: 10 }}>
          <h1 style={{ fontSize: '15px', fontWeight: 700, color: '#101726', letterSpacing: '-0.02em' }}>Entegrasyonlar</h1>
          <span style={{ fontSize: '13px', color: '#6a7890' }}>{loading ? '...' : `${connectedCount} / ${platforms.length} bağlı`}</span>
        </header>

        <div style={{ padding: '24px 28px', maxWidth: '680px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {loading ? (
            <p style={{ fontSize: '14px', color: '#6a7890' }}>Yükleniyor...</p>
          ) : (
            <>
              {/* Başarı mesajı */}
              {justConnected && (
                <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '12px', padding: '14px 16px' }}>
                  <p style={{ fontSize: '13px', fontWeight: 600, color: '#16a34a' }}>✓ Google Analytics 4 başarıyla bağlandı!</p>
                  <p style={{ fontSize: '13px', color: '#166534', marginTop: '2px' }}>Aşağıya GA4 Mülk ID&apos;nizi girin.</p>
                </div>
              )}

              {/* Customer ID girişi — Google Ads bağlıysa göster */}
              {status?.google_ads && (
                <div style={{ background: '#fff', border: '1px solid #d8dfea', borderRadius: '14px', padding: '16px 18px' }}>
                  <p style={{ fontSize: '13px', fontWeight: 600, color: '#101726', marginBottom: '10px' }}>Google Ads Müşteri ID&apos;si</p>
                  <p style={{ fontSize: '12px', color: '#6a7890', marginBottom: '10px' }}>
                    Google Ads → Sağ üst köşe → 10 haneli müşteri kimliği (xxx-xxx-xxxx)
                  </p>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <input
                      className="input"
                      value={customerId}
                      onChange={e => { setCustomerId(e.target.value); setCustomerSaved(false) }}
                      placeholder="örn: 123-456-7890"
                      style={{ flex: 1, fontSize: '13px' }}
                    />
                    <button
                      onClick={handleSaveCustomer}
                      disabled={savingCustomer || !customerId.trim()}
                      className="btn-primary"
                      style={{ fontSize: '12px', padding: '0 16px' }}
                    >
                      {savingCustomer ? 'Kaydediliyor...' : customerSaved ? '✓ Kaydedildi' : 'Kaydet'}
                    </button>
                  </div>
                </div>
              )}

              {/* Property ID girişi — GA4 bağlıysa göster */}
              {showPropertyInput && (
                <div style={{ background: '#fff', border: '1px solid #d8dfea', borderRadius: '14px', padding: '16px 18px' }}>
                  <p style={{ fontSize: '13px', fontWeight: 600, color: '#101726', marginBottom: '10px' }}>GA4 Mülk ID&apos;si</p>
                  <p style={{ fontSize: '12px', color: '#6a7890', marginBottom: '10px' }}>
                    GA4 → Yönetici → Mülk Ayarları → Mülk Kimliği (rakam)
                  </p>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <input
                      className="input"
                      value={propertyId}
                      onChange={e => { setPropertyId(e.target.value); setPropertySaved(false) }}
                      placeholder="örn: 528556104"
                      style={{ flex: 1, fontSize: '13px' }}
                    />
                    <button
                      onClick={handleSaveProperty}
                      disabled={savingProperty || !propertyId.trim()}
                      className="btn-primary"
                      style={{ fontSize: '12px', padding: '0 16px' }}
                    >
                      {savingProperty ? 'Kaydediliyor...' : propertySaved ? '✓ Kaydedildi' : 'Kaydet'}
                    </button>
                  </div>
                </div>
              )}

              {platforms.map(p => {
                const connected = status?.[p.key] ?? false
                return (
                  <div key={p.key} className="card" style={{ padding: '16px 18px', display: 'flex', alignItems: 'center', gap: '14px' }}>
                    <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: p.color, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                      <span style={{ color: '#fff', fontSize: '14px', fontWeight: 800 }}>{p.initial}</span>
                    </div>

                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '2px' }}>
                        <p style={{ fontSize: '14px', fontWeight: 600, color: '#101726' }}>{p.name}</p>
                        {connected && (
                          <span className="tag" style={{ fontSize: '11px', fontWeight: 500, color: '#16a34a', background: '#f0fdf4', borderColor: '#bbf7d0' }}>Bağlı</span>
                        )}
                      </div>
                      <p style={{ fontSize: '13px', color: '#6a7890', lineHeight: 1.5 }}>{p.desc}</p>
                    </div>

                    {connected ? (
                      <button
                        className="btn-ghost"
                        onClick={p.key === 'ga4' ? handleDisconnectGA4 : p.key === 'google_ads' ? handleDisconnectAds : undefined}
                        style={{ fontSize: '12px', color: '#dc2626', flexShrink: 0 }}
                      >
                        Bağlantıyı kes
                      </button>
                    ) : p.canConnect ? (
                      <button
                        onClick={handleConnectGoogle}
                        disabled={connecting}
                        className="btn-primary"
                        style={{ fontSize: '12px', padding: '7px 14px', flexShrink: 0 }}
                      >
                        {connecting ? 'Yönlendiriliyor...' : 'Bağla'}
                      </button>
                    ) : (
                      <button disabled className="btn-ghost" style={{ fontSize: '12px', opacity: 0.5, flexShrink: 0, cursor: 'not-allowed' }}>
                        Yakında
                      </button>
                    )}
                  </div>
                )
              })}

              <div style={{ background: '#f0ecff', border: '1px solid #c4b5fd', borderRadius: '12px', padding: '14px 16px', marginTop: '4px' }}>
                <p style={{ fontSize: '13px', fontWeight: 600, color: '#6c47ff', marginBottom: '4px' }}>GA4 Entegrasyonu</p>
                <p style={{ fontSize: '13px', color: '#4c3397', lineHeight: 1.6 }}>
                  &quot;Bağla&quot; butonuna tıklayın, Google hesabınızla giriş yapın ve izin verin. Sonra GA4 Mülk ID&apos;nizi girerek gerçek verilerinizi görün.
                </p>
              </div>
            </>
          )}
        </div>
      </main>
    </div>
  )
}

export default function IntegrationsPage() {
  return (
    <Suspense fallback={null}>
      <IntegrationsContent />
    </Suspense>
  )
}
