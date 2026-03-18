'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Sidebar from '@/components/Sidebar'
import { getMe } from '@/lib/api'
import type { User } from '@/lib/types'

const planConfig: Record<string, { label: string; color: string; bg: string; border: string }> = {
  starter:  { label: 'Starter',  color: '#6a7890', bg: '#f3f5f8', border: '#d8dfea' },
  growth:   { label: 'Growth',   color: '#6c47ff', bg: '#f0ecff', border: '#c4b5fd' },
  operator: { label: 'Operator', color: '#d97706', bg: '#fffbeb', border: '#fde68a' },
}

export default function SettingsPage() {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    const token = localStorage.getItem('aria_token')
    if (!token) { router.push('/login'); return }
    getMe().then(setUser).finally(() => setLoading(false))
  }, [router])

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault()
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const plan = user ? (planConfig[user.plan] ?? planConfig.starter) : null

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#f3f5f8' }}>
      <Sidebar />
      <main style={{ flex: 1, overflow: 'auto' }}>
        <header style={{ background: '#fff', borderBottom: '1px solid #d8dfea', padding: '0 28px', height: '56px', display: 'flex', alignItems: 'center', position: 'sticky', top: 0, zIndex: 10 }}>
          <h1 style={{ fontSize: '15px', fontWeight: 700, color: '#101726', letterSpacing: '-0.02em' }}>Ayarlar</h1>
        </header>

        <div style={{ padding: '24px 28px', maxWidth: '560px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {loading ? (
            <p style={{ fontSize: '14px', color: '#6a7890' }}>Yükleniyor...</p>
          ) : (
            <>
              {/* Plan */}
              <div className="card" style={{ padding: '18px 20px' }}>
                <p style={{ fontSize: '11px', fontWeight: 700, color: '#6a7890', letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '12px' }}>Plan</p>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span className="tag" style={{ fontSize: '12px', fontWeight: 600, color: plan?.color, background: plan?.bg, borderColor: plan?.border }}>
                      {plan?.label}
                    </span>
                    <span style={{ fontSize: '13px', color: '#6a7890' }}>mevcut planınız</span>
                  </div>
                  <button style={{ fontSize: '13px', color: '#6c47ff', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 500, transition: 'opacity 180ms ease' }}
                    onMouseEnter={e => { (e.currentTarget as HTMLElement).style.opacity = '0.7' }}
                    onMouseLeave={e => { (e.currentTarget as HTMLElement).style.opacity = '1' }}
                  >
                    Planı yükselt →
                  </button>
                </div>
              </div>

              {/* Profile */}
              <div className="card" style={{ padding: '18px 20px' }}>
                <p style={{ fontSize: '11px', fontWeight: 700, color: '#6a7890', letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '16px' }}>Profil Bilgileri</p>
                <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div>
                    <label className="label">Ad Soyad</label>
                    <input type="text" defaultValue={user?.full_name} className="input" />
                  </div>
                  <div>
                    <label className="label">E-posta</label>
                    <input type="email" defaultValue={user?.email} disabled className="input" style={{ background: '#f8fafc', color: '#6a7890', cursor: 'not-allowed' }} />
                    <p style={{ fontSize: '12px', color: '#6a7890', marginTop: '4px' }}>E-posta değiştirilemez</p>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', paddingTop: '4px' }}>
                    <button type="submit" className="btn-primary" style={{ fontSize: '13px', padding: '8px 16px' }}>Kaydet</button>
                    {saved && <span style={{ fontSize: '13px', color: '#16a34a', fontWeight: 500 }}>✓ Kaydedildi</span>}
                  </div>
                </form>
              </div>

              {/* Password */}
              <div className="card" style={{ padding: '18px 20px' }}>
                <p style={{ fontSize: '11px', fontWeight: 700, color: '#6a7890', letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '16px' }}>Şifre Değiştir</p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  <input type="password" placeholder="Mevcut şifre" className="input" />
                  <input type="password" placeholder="Yeni şifre" className="input" />
                  <input type="password" placeholder="Yeni şifre (tekrar)" className="input" />
                  <div>
                    <button type="button" className="btn-ghost" style={{ fontSize: '13px' }}>Şifreyi güncelle</button>
                  </div>
                </div>
              </div>

              {/* Danger zone */}
              <div style={{ background: '#fff', border: '1px solid #fecaca', borderRadius: '14px', padding: '18px 20px' }}>
                <p style={{ fontSize: '11px', fontWeight: 700, color: '#dc2626', letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '12px' }}>Tehlikeli Bölge</p>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div>
                    <p style={{ fontSize: '14px', fontWeight: 500, color: '#101726' }}>Hesabı sil</p>
                    <p style={{ fontSize: '13px', color: '#6a7890', marginTop: '2px' }}>Bu işlem geri alınamaz</p>
                  </div>
                  <button style={{
                    fontSize: '13px', fontWeight: 500, padding: '7px 14px', borderRadius: '8px',
                    color: '#dc2626', background: '#fef2f2', border: '1px solid #fecaca',
                    cursor: 'pointer', transition: 'all 180ms ease',
                  }}
                    onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = '#fecaca' }}
                    onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = '#fef2f2' }}
                  >
                    Hesabı sil
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </main>
    </div>
  )
}
