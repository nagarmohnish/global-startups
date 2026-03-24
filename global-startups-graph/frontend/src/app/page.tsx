'use client'

import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, PieChart, Pie } from 'recharts'
import { fetchStats, fetchIndustryRanking, fetchIndustryByRegion, fetchRegionComparison } from '@/lib/api'
import { usd, num } from '@/lib/fmt'
import { StatCard, Loading, Card, SectionHeader } from '@/components/shared'
import { TrendingUp, Globe, Building2, Users, DollarSign, Factory } from 'lucide-react'

const COLORS = ['#4f46e5','#7c3aed','#2563eb','#0891b2','#059669','#d97706','#dc2626','#db2777','#6366f1','#8b5cf6','#14b8a6','#f43f5e','#0ea5e9','#84cc16','#a855f7']

export default function Dashboard() {
  const { data: stats, isLoading: l1 } = useQuery({ queryKey: ['stats'], queryFn: fetchStats })
  const { data: ranking, isLoading: l2 } = useQuery({ queryKey: ['indRanking'], queryFn: () => fetchIndustryRanking(15) })
  const { data: heatmap } = useQuery({ queryKey: ['indByRegion'], queryFn: fetchIndustryByRegion })
  const { data: regions } = useQuery({ queryKey: ['regionCmp'], queryFn: fetchRegionComparison })

  if (l1 || l2) return <Loading />

  const regionColors: Record<string, string> = {
    'Europe': '#4f46e5', 'East Asia': '#dc2626', 'North America': '#059669',
    'Southeast Asia': '#d97706', 'Latin America': '#2563eb', 'Middle East': '#8b5cf6',
  }

  const allIndustries = ranking?.map(r => r.industry) ?? []
  const regionNames = Object.keys(heatmap ?? {})

  return (
    <div className="space-y-8">
      {/* Hero */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Global Startup Ecosystem</h1>
        <p className="text-gray-500 mt-1">Graph-powered intelligence across {stats?.total_cities} cities and {stats?.total_industries} industries</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <StatCard label="Startups" value={num(stats?.total_startups)} />
        <StatCard label="Total Funding" value={usd(stats?.total_funding)} />
        <StatCard label="Investors" value={num(stats?.total_investors)} />
        <StatCard label="Founders" value={num(stats?.total_founders)} />
        <StatCard label="Cities" value={num(stats?.total_cities)} />
        <StatCard label="Industries" value={num(stats?.total_industries)} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Industry ranking chart */}
        <Card className="lg:col-span-2">
          <SectionHeader>Top Industries by Total Funding</SectionHeader>
          <ResponsiveContainer width="100%" height={420} className="mt-4">
            <BarChart data={ranking} layout="vertical" margin={{ left: 140 }}>
              <XAxis type="number" tickFormatter={v => usd(v)} />
              <YAxis type="category" dataKey="industry" width={130} tick={{ fontSize: 12 }} />
              <Tooltip formatter={(v: number) => usd(v)} />
              <Bar dataKey="total_funding" radius={[0, 4, 4, 0]}>
                {ranking?.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} cursor="pointer" />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>

        {/* Region cards */}
        <Card>
          <SectionHeader>Regions</SectionHeader>
          <div className="space-y-3 mt-4">
            {regions?.map(r => (
              <div key={r.region}
                className="border rounded-lg p-4 hover:shadow-sm transition-shadow"
                style={{ borderLeftColor: regionColors[r.region] ?? '#999', borderLeftWidth: 4 }}>
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-semibold text-sm">{r.region}</p>
                    <p className="text-2xl font-bold mt-0.5">{r.startup_count}</p>
                    <p className="text-xs text-gray-400">startups</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium">{usd(r.total_funding)}</p>
                    <p className="text-xs text-gray-400 mt-1">Top: {r.top_industry}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Heatmap */}
      <Card>
        <SectionHeader>Industry x Region Heatmap</SectionHeader>
        <div className="overflow-x-auto mt-4">
          <table className="text-xs w-full">
            <thead>
              <tr>
                <th className="text-left p-2 font-medium text-gray-500">Industry</th>
                {regionNames.map(r => <th key={r} className="p-2 text-center font-medium text-gray-500">{r}</th>)}
              </tr>
            </thead>
            <tbody>
              {allIndustries.map(ind => (
                <tr key={ind} className="hover:bg-gray-50">
                  <td className="p-2">
                    <Link href={`/industry/${encodeURIComponent(ind)}`} className="font-medium text-brand-600 hover:underline">
                      {ind}
                    </Link>
                  </td>
                  {regionNames.map(reg => {
                    const val = heatmap?.[reg]?.[ind] ?? 0
                    const maxVal = Math.max(...allIndustries.map(i => heatmap?.[reg]?.[i] ?? 0))
                    const intensity = maxVal > 0 ? val / maxVal : 0
                    return (
                      <td key={reg} className="p-2 text-center"
                        style={{
                          backgroundColor: val > 0 ? `rgba(79, 70, 229, ${0.08 + intensity * 0.55})` : 'transparent',
                          color: intensity > 0.5 ? 'white' : 'inherit',
                        }}>
                        {val || ''}
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}
