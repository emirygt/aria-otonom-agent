import type { Metadata } from 'next'
import './globals.css'
import { SessionProvider } from './providers'

export const metadata: Metadata = {
  title: 'Aria — AI Marketing OS',
  description: 'Reklam bütçeni boşa harcama.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="tr">
      <body>
        <SessionProvider>{children}</SessionProvider>
      </body>
    </html>
  )
}
