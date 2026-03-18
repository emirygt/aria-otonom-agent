'use client'

import { usePathname } from 'next/navigation'
import Link from 'next/link'

const navItems = [
  {
    href: '/',
    label: 'Dashboard',
    icon: (
      <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
      </svg>
    ),
  },
  {
    href: '/campaigns',
    label: 'Kampanyalar',
    icon: (
      <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
  },
  {
    href: '/insights',
    label: "Insight'lar",
    icon: (
      <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
      </svg>
    ),
  },
  {
    href: '/operator',
    label: 'Operator',
    icon: (
      <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
  },
  {
    href: '/integrations',
    label: 'Entegrasyonlar',
    icon: (
      <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
      </svg>
    ),
  },
  {
    href: '/settings',
    label: 'Ayarlar',
    icon: (
      <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
  },
]

export default function Sidebar() {
  const pathname = usePathname()

  return (
    <aside style={{
      width: '72px',
      flexShrink: 0,
      background: '#ffffff',
      borderRight: '1px solid #d8dfea',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      minHeight: '100vh',
      paddingTop: '16px',
      paddingBottom: '16px',
    }}>
      {/* Logo */}
      <div style={{ marginBottom: '20px', paddingBottom: '16px', borderBottom: '1px solid #e8ecf2', width: '100%', display: 'flex', justifyContent: 'center' }}>
        <div style={{
          width: '36px', height: '36px',
          background: '#6c47ff',
          borderRadius: '10px',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <span style={{ color: '#fff', fontSize: '15px', fontWeight: 800 }}>A</span>
        </div>
      </div>

      {/* Nav icons */}
      <nav style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px', flex: 1, width: '100%', padding: '0 10px' }}>
        {navItems.map(item => {
          const active = pathname === item.href
          return (
            <Link
              key={item.href}
              href={item.href}
              title={item.label}
              style={{
                width: '48px', height: '48px',
                display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '3px',
                borderRadius: '10px',
                color: active ? '#6c47ff' : '#6a7890',
                background: active ? '#f0ecff' : 'transparent',
                border: active ? '1px solid #c4b5fd' : '1px solid transparent',
                textDecoration: 'none',
                transition: 'all 180ms ease',
                fontSize: '9px',
                fontWeight: 500,
              }}
              onMouseEnter={e => {
                if (!active) {
                  const el = e.currentTarget as HTMLElement
                  el.style.background = '#f3f5f8'
                  el.style.color = '#101726'
                }
              }}
              onMouseLeave={e => {
                if (!active) {
                  const el = e.currentTarget as HTMLElement
                  el.style.background = 'transparent'
                  el.style.color = '#6a7890'
                }
              }}
            >
              {item.icon}
              <span style={{ fontSize: '9px', letterSpacing: '0.01em', lineHeight: 1 }}>
                {item.label.split("'")[0].substring(0, 6)}
              </span>
            </Link>
          )
        })}
      </nav>

      {/* Logout */}
      <div style={{ width: '100%', padding: '0 10px', paddingTop: '12px', borderTop: '1px solid #e8ecf2' }}>
        <button
          onClick={() => { localStorage.removeItem('aria_token'); window.location.href = '/login' }}
          title="Çıkış yap"
          style={{
            width: '48px', height: '48px', margin: '0 auto',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            borderRadius: '10px', background: 'transparent', border: 'none',
            color: '#6a7890', cursor: 'pointer', transition: 'all 180ms ease',
          }}
          onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = '#f3f5f8'; (e.currentTarget as HTMLElement).style.color = '#dc2626' }}
          onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = 'transparent'; (e.currentTarget as HTMLElement).style.color = '#6a7890' }}
        >
          <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
        </button>
      </div>
    </aside>
  )
}
