'use client'

import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { fetchIndustryRanking } from '@/lib/api'
import { usd, num } from '@/lib/fmt'
import { Loading, Card, SectionHeader } from '@/components/shared'

const COLORS = ['#4f46e5','#7c3aed','#2563eb','#0891b2','#059669','#d97706','#dc2626','#db2777','#6366f1','#8b5cf6','#14b8a6','#f43f5e','#0ea5e9','#84cc16','#a855f7']

export default function IndustriesDashboard() {
  const { data: ranking, isLoading } = useQuery({
    queryKey: ['indRanking20'], queryFn: () => fetchIndustryRanking(20),
  })

  if (isLoading) return <Loading />

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Industry Deep Dive</h1>
        <p className="text-sm text-gray-500 mt-1">Click any industry to explore its ecosystem</p>
      </div>

      <Card>
        <SectionHeader>All Industries by Funding</SectionHeader>
        <ResponsiveContainer width="100%" height={600} className="mt-4">
          <BarChart data={ranking} layout="vertical" margin={{ left: 150 }}>
            <XAxis type="number" tickFormatter={v => usd(v)} />
            <YAxis type="category" dataKey="industry" width={140} tick={{ fontSize: 12 }} />
            <Tooltip formatter={(v: number) => usd(v)} />
            <Bar dataKey="total_funding" radius={[0, 4, 4, 0]}>
              {ranking?.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} cursor="pointer" />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {ranking?.map((ind, i) => (
          <Link key={ind.industry} href={`/industry/${encodeURIComponent(ind.industry)}`}>
            <Card className="hover:shadow-md transition-shadow cursor-pointer">
              <div className="flex items-start justify-between">
                <div>
                  <p className="font-semibold" style={{ color: COLORS[i % COLORS.length] }}>{ind.industry}</p>
                  <p className="text-2xl font-bold mt-1">{ind.startup_count}</p>
                  <p className="text-xs text-gray-400">startups</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium">{usd(ind.total_funding)}</p>
                  <p className="text-xs text-gray-400">total funding</p>
                  <p className="text-xs text-gray-400 mt-1">avg {usd(ind.avg_funding)}</p>
                </div>
              </div>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
}
