import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Course Listing Creator',
  description: 'AI-powered course listing generator',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen bg-navy" suppressHydrationWarning>
        {children}
      </body>
    </html>
  )
}
