'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Sidebar from '@/components/Sidebar'
import { planOperatorAction, confirmOperatorAction, getOperatorHistory } from '@/lib/api'
import type { OperatorAction } from '@/lib/types'

const statusConfig: Record<string, { label: string; color: string; bg: string; border: string }> = {
  pending:   { label: 'Bekliyor',  color: '#d97706', bg: '#fffbeb', border: '#fde68a' },
  confirmed: { label: 'Onaylandı', color: '#2563eb', bg: '#eff6ff', border: '#bfdbfe' },
  executed:  { label: 'Uygulandı', color: '#16a34a', bg: '#f0fdf4', border: '#bbf7d0' },
  failed:    { label: 'Başarısız', color: '#dc2626', bg: '#fef2f2', border: '#fecaca' },
}

interface PendingPlan {
  token: string
  plan: string
  actions: string[]
}

export default function OperatorPage() {
  const router = useRouter()
  const [goal, setGoal] = useState('')
  const [pending, setPending] = useState<PendingPlan | null>(null)
  const [history, setHistory] = useState<OperatorAction[]>([])
  const [planning, setPlanning] = useState(false)
  const [confirming, setConfirming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  useEffect(() => {
    const token = localStorage.getItem('aria_token')
    if (!token) { router.push('/login'); return }
    getOperatorHistory().then(setHistory).catch(() => {})
  }, [router])

  const handlePlan = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!goal.trim()) return
    setPlanning(true); setError(null); setPending(null)
    try { setPending(await planOperatorAction(goal)) }
    catch { setError('Plan oluşturulamadı. Lütfen tekrar deneyin.') }
    finally { setPlanning(false) }
  }

  const handleConfirm = async () => {
    if (!pending) return
    setConfirming(true); setError(null)
    try {
      await confirmOperatorAction(pending.token)
      setSuccess('Aksiyon başarıyla uygulandı.')
      setPending(null); setGoal('')
      setHistory(await getOperatorHistory())
      setTimeout(() => setSuccess(null), 3000)
    } catch { setError('Aksiyon uygulanamadı.') }
    finally { setConfirming(false) }
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#f3f5f8' }}>
      <Sidebar />

      <main style={{ flex: 1, overflow: 'auto' }}>
        {/* Header */}
        <header style={{ background: '#fff', borderBottom: '1px solid #d8dfea', padding: '0 28px', height: '56px', display: 'flex', alignItems: 'center', position: 'sticky', top: 0, zIndex: 10 }}>
          <h1 style={{ fontSize: '15px', fontWeight: 700, color: '#101726', letterSpacing: '-0.02em' }}>Operator Agent</h1>
          <span style={{ fontSize: '13px', color: '#6a7890', marginLeft: '10px' }}>· Kampanyalarda AI destekli aksiyonlar</span>
        </header>

        <div style={{ padding: '24px 28px', maxWidth: '720px', display: 'flex', flexDirection: 'column', gap: '14px' }}>

          {/* Security notice */}
          <div style={{ background: '#fffbeb', border: '1px solid #fde68a', borderRadius: '12px', padding: '14px 16px', display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
            <svg width="16" height="16" fill="none" stroke="#d97706" viewBox="0 0 24 24" style={{ flexShrink: 0, marginTop: '1px' }}>
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <div>
              <p style={{ fontSize: '13px', fontWeight: 600, color: '#92400e', marginBottom: '2px' }}>Güvenlik Kuralları</p>
              <p style={{ fontSize: '13px', color: '#78350f', lineHeight: 1.55 }}>
                Günlük bütçe %50&apos;den fazla artırılamaz · Kampanya onaysız kapatılamaz · Her aksiyon onayınızı bekler
              </p>
            </div>
          </div>

          {/* Plan form */}
          <div className="card" style={{ padding: '20px 22px' }}>
            <p style={{ fontSize: '11px', fontWeight: 700, color: '#6a7890', letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '14px' }}>
              Yeni Aksiyon Planı
            </p>
            <form onSubmit={handlePlan} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div>
                <label className="label">Hedefinizi yazın</label>
                <textarea
                  value={goal}
                  onChange={e => setGoal(e.target.value)}
                  placeholder="örn: Düşük performanslı kampanyaları duraklat ve bütçeyi en iyi ROAS'lı kampanyaya aktar"
                  rows={3}
                  className="input"
                  style={{ resize: 'none', lineHeight: 1.6 }}
                />
              </div>
              <div>
                <button type="submit" disabled={planning || !goal.trim()} className="btn-primary">
                  {planning ? (
                    <>
                      <span style={{ width: '12px', height: '12px', border: '2px solid rgba(255,255,255,0.35)', borderTopColor: '#fff', borderRadius: '50%', animation: 'spin 0.7s linear infinite' }} />
                      Plan oluşturuluyor...
                    </>
                  ) : 'Plan Oluştur'}
                </button>
              </div>
            </form>
          </div>

          {/* Error / Success */}
          {error && (
            <div style={{ fontSize: '13px', color: '#dc2626', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '10px', padding: '11px 14px' }}>{error}</div>
          )}
          {success && (
            <div style={{ fontSize: '13px', color: '#16a34a', background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '10px', padding: '11px 14px' }}>{success}</div>
          )}

          {/* Pending plan */}
          {pending && (
            <div style={{ background: '#fff', border: '1px solid #c4b5fd', borderRadius: '14px', padding: '20px 22px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: '#d97706', animation: 'pulse 1.5s ease infinite' }} />
                <span style={{ fontSize: '11px', fontWeight: 700, color: '#6c47ff', letterSpacing: '0.06em', textTransform: 'uppercase' }}>Onay Bekliyor</span>
              </div>

              <p style={{ fontSize: '14px', color: '#101726', lineHeight: 1.6, marginBottom: pending.actions.length > 0 ? '12px' : '0' }}>
                {pending.plan}
              </p>

              {pending.actions.length > 0 && (
                <div style={{ background: '#f8fafc', border: '1px solid #e8ecf2', borderRadius: '10px', padding: '12px 14px', marginBottom: '16px' }}>
                  <p style={{ fontSize: '11px', fontWeight: 600, color: '#6a7890', letterSpacing: '0.05em', textTransform: 'uppercase', marginBottom: '8px' }}>Uygulanacak Aksiyonlar</p>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    {pending.actions.map((action, i) => (
                      <div key={i} style={{ display: 'flex', gap: '8px', fontSize: '13px', color: '#3f4b60' }}>
                        <span style={{ color: '#6c47ff', fontWeight: 600 }}>→</span>
                        {action}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div style={{ display: 'flex', gap: '10px', paddingTop: '14px', borderTop: '1px solid #e8ecf2' }}>
                <button onClick={handleConfirm} disabled={confirming} className="btn-primary" style={{ background: '#16a34a' }}
                  onMouseEnter={e => { if (!confirming) (e.currentTarget as HTMLElement).style.background = '#15803d' }}
                  onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = '#16a34a' }}
                >
                  {confirming ? (
                    <>
                      <span style={{ width: '12px', height: '12px', border: '2px solid rgba(255,255,255,0.35)', borderTopColor: '#fff', borderRadius: '50%', animation: 'spin 0.7s linear infinite' }} />
                      Uygulanıyor...
                    </>
                  ) : (
                    <>
                      <svg width="13" height="13" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                      </svg>
                      Onayla ve Uygula
                    </>
                  )}
                </button>
                <button onClick={() => setPending(null)} className="btn-ghost">İptal</button>
              </div>
            </div>
          )}

          {/* History */}
          {history.length > 0 && (
            <div>
              <p style={{ fontSize: '11px', fontWeight: 700, color: '#6a7890', letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '10px' }}>
                Geçmiş Aksiyonlar
              </p>
              <div className="card" style={{ overflow: 'hidden' }}>
                {history.map((action, i) => {
                  const s = statusConfig[action.status] ?? statusConfig.pending
                  return (
                    <div
                      key={action.id}
                      style={{ padding: '13px 18px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: i < history.length - 1 ? '1px solid #f0f2f5' : 'none' }}
                    >
                      <div>
                        <p style={{ fontSize: '14px', fontWeight: 500, color: '#101726' }}>{action.action_type}</p>
                        <p style={{ fontSize: '12px', color: '#6a7890', marginTop: '2px' }}>
                          {new Date(action.created_at).toLocaleDateString('tr-TR', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}
                        </p>
                      </div>
                      <span className="tag" style={{ fontSize: '12px', fontWeight: 500, color: s.color, background: s.bg, borderColor: s.border }}>
                        {s.label}
                      </span>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      </main>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
      `}</style>
    </div>
  )
}
