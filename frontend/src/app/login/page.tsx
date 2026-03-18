'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { login, register } from '@/lib/api'

export default function LoginPage() {
  const router = useRouter()
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [loading, setLoading] = useState(false)
  const [googleLoading, setGoogleLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Backend Google OAuth callback: /login?token=JWT
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const token = params.get('token')
    if (token) {
      localStorage.setItem('aria_token', token)
      router.replace('/')
      return
    }
    const err = params.get('error')
    if (err) {
      setError(`Google girişi başarısız: ${err}`)
    }
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); setError(null); setLoading(true)
    try {
      const token = mode === 'login' ? await login(email, password) : await register(email, password, fullName)
      localStorage.setItem('aria_token', token)
      router.push('/')
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      setError(axiosErr?.response?.data?.detail || 'Bir hata oluştu')
    } finally { setLoading(false) }
  }

  const handleGoogleSignIn = () => {
    setGoogleLoading(true)
    setError(null)
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000'
    window.location.href = `${apiUrl}/api/v1/auth/google/connect`
  }

  return (
    <div style={{ minHeight: '100vh', background: '#f3f5f8', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '24px' }}>
      <div style={{ width: '100%', maxWidth: '380px' }}>

        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <div style={{
            width: '42px', height: '42px', background: '#6c47ff', borderRadius: '12px',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto 10px',
            boxShadow: '0 4px 16px rgba(108,71,255,0.25)',
          }}>
            <span style={{ color: '#fff', fontSize: '17px', fontWeight: 800 }}>A</span>
          </div>
          <h2 style={{ fontSize: '18px', fontWeight: 800, color: '#101726', letterSpacing: '-0.03em' }}>Aria</h2>
          <p style={{ fontSize: '13px', color: '#6a7890', marginTop: '2px' }}>AI Marketing OS</p>
        </div>

        {/* Card */}
        <div style={{
          background: '#ffffff',
          border: '1px solid #d8dfea',
          borderRadius: '16px',
          padding: '28px',
          boxShadow: '0 4px 24px rgba(16,23,38,0.07)',
        }}>

          {/* Google ile Giriş */}
          <button
            onClick={handleGoogleSignIn}
            disabled={googleLoading}
            style={{
              width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center',
              gap: '10px', padding: '11px', borderRadius: '10px',
              border: '1px solid #d8dfea', background: '#ffffff',
              cursor: googleLoading ? 'not-allowed' : 'pointer',
              fontSize: '14px', fontWeight: 500, color: '#101726',
              opacity: googleLoading ? 0.6 : 1,
              transition: 'background 150ms',
              marginBottom: '18px',
            }}
            onMouseEnter={e => { if (!googleLoading) e.currentTarget.style.background = '#f3f5f8' }}
            onMouseLeave={e => { e.currentTarget.style.background = '#ffffff' }}
          >
            {googleLoading ? (
              <span style={{ width: '16px', height: '16px', border: '2px solid #d8dfea', borderTopColor: '#6c47ff', borderRadius: '50%', animation: 'spin 0.7s linear infinite' }} />
            ) : (
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                <path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.875 2.684-6.615z" fill="#4285F4"/>
                <path d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z" fill="#34A853"/>
                <path d="M3.964 10.71A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.042l3.007-2.332z" fill="#FBBC05"/>
                <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z" fill="#EA4335"/>
              </svg>
            )}
            {googleLoading ? 'Yönlendiriliyor...' : 'Google ile devam et'}
          </button>

          {/* Ayraç */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '18px' }}>
            <div style={{ flex: 1, height: '1px', background: '#d8dfea' }} />
            <span style={{ fontSize: '12px', color: '#6a7890' }}>veya</span>
            <div style={{ flex: 1, height: '1px', background: '#d8dfea' }} />
          </div>

          {/* Mode tabs */}
          <div style={{ display: 'flex', background: '#f3f5f8', borderRadius: '10px', padding: '3px', marginBottom: '22px' }}>
            {(['login', 'register'] as const).map(m => (
              <button
                key={m}
                onClick={() => { setMode(m); setError(null) }}
                style={{
                  flex: 1, padding: '7px', borderRadius: '8px', border: 'none', cursor: 'pointer',
                  fontSize: '13px', fontWeight: 500,
                  color: mode === m ? '#101726' : '#6a7890',
                  background: mode === m ? '#ffffff' : 'transparent',
                  boxShadow: mode === m ? '0 1px 4px rgba(16,23,38,0.1)' : 'none',
                  transition: 'all 180ms ease',
                }}
              >
                {m === 'login' ? 'Giriş yap' : 'Kayıt ol'}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {mode === 'register' && (
              <div>
                <label className="label">Ad Soyad</label>
                <input className="input" type="text" value={fullName} onChange={e => setFullName(e.target.value)} required placeholder="Ahmet Yılmaz" />
              </div>
            )}
            <div>
              <label className="label">E-posta</label>
              <input className="input" type="email" value={email} onChange={e => setEmail(e.target.value)} required placeholder="ahmet@magazan.com" />
            </div>
            <div>
              <label className="label">Şifre</label>
              <input className="input" type="password" value={password} onChange={e => setPassword(e.target.value)} required minLength={6} placeholder="••••••••" />
            </div>

            {error && (
              <div style={{ fontSize: '13px', color: '#dc2626', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', padding: '9px 12px' }}>
                {error}
              </div>
            )}

            <button type="submit" disabled={loading} className="btn-primary" style={{ width: '100%', justifyContent: 'center', padding: '11px', fontSize: '14px', marginTop: '2px' }}>
              {loading ? (
                <>
                  <span style={{ width: '13px', height: '13px', border: '2px solid rgba(255,255,255,0.35)', borderTopColor: '#fff', borderRadius: '50%', animation: 'spin 0.7s linear infinite' }} />
                  Bekleniyor...
                </>
              ) : mode === 'login' ? 'Giriş yap →' : 'Hesap oluştur →'}
            </button>
          </form>
        </div>

        <p style={{ textAlign: 'center', fontSize: '12px', color: '#6a7890', marginTop: '20px' }}>
          Reklam bütçeni boşa harcama.
        </p>
      </div>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}
