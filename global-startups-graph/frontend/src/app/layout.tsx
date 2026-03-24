'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { Search, BarChart3, Globe, Users, Compass, MessageSquare } from 'lucide-react'
import './globals.css'

const NAV = [
  { href: '/', label: 'Dashboard', icon: BarChart3 },
  { href: '/explore', label: 'Explore', icon: Compass },
  { href: '/dashboards/cities', label: 'Cities', icon: Globe },
  { href: '/dashboards/investors', label: 'Investors', icon: Users },
  { href: '/ask', label: 'Ask AI', icon: MessageSquare },
]

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: { queries: { staleTime: 60_000, retry: 1 } },
  }))
  const pathname = usePathname()
  const router = useRouter()
  const [q, setQ] = useState('')

  return (
    <html lang="en">
      <head><title>StartupGraph</title></head>
      <body>
        <QueryClientProvider client={queryClient}>
          {/* Top nav */}
          <nav className="bg-white border-b border-gray-200 px-6 py-2.5 flex items-center justify-between sticky top-0 z-50 shadow-sm">
            <div className="flex items-center gap-6">
              <Link href="/" className="text-xl font-bold bg-gradient-to-r from-brand-600 to-purple-600 bg-clip-text text-transparent">
                StartupGraph
              </Link>
              <div className="flex gap-0.5">
                {NAV.map(n => {
                  const Icon = n.icon
                  const active = pathname === n.href || (n.href !== '/' && pathname.startsWith(n.href))
                  return (
                    <Link
                      key={n.href}
                      href={n.href}
                      className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                        active ? 'bg-brand-50 text-brand-700' : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                      {n.label}
                    </Link>
                  )
                })}
              </div>
            </div>
            <form onSubmit={e => { e.preventDefault(); if (q.trim()) router.push(`/explore?q=${encodeURIComponent(q)}`) }}
              className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search startups, investors, cities..."
                value={q}
                onChange={e => setQ(e.target.value)}
                className="pl-9 pr-4 py-2 border border-gray-200 rounded-lg text-sm w-80 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
              />
            </form>
          </nav>
          <main className="max-w-[1400px] mx-auto px-6 py-6">{children}</main>
        </QueryClientProvider>
      </body>
    </html>
  )
}
