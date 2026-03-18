'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

// Bu sayfa artık kullanılmıyor — Google OAuth backend üzerinden yönetiliyor.
// /login?token=JWT akışı login/page.tsx'te işleniyor.
export default function AuthRedirect() {
  const router = useRouter()
  useEffect(() => { router.replace('/login') }, [])
  return null
}
