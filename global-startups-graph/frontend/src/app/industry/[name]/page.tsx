'use client'

import { useParams } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { fetchIndustryOverview } from '@/lib/api'
import { usd, num } from '@/lib/fmt'
import { Loading, Card, SectionHeader, StatCard, EntityLink, Badge } from '@/components/shared'

const COLORS = ['#4f46e5','#7c3aed','#059669','#d97706','#dc2626','#0891b2','#db2777','#6366f1']

export default function IndustryPage() {
  const { name } = useParams<{ name: string }>()
  const decoded = decodeURIComponent(name)
  const { data: ind, isLoading } = useQuery({
    queryKey: ['industryOverview', decoded], queryFn: () => fetchIndustryOverview(decoded),
  })

  if (isLoading) return <Loading />
  if (!ind) return <p className="text-gray-500 py-8">Industry not found</p>

  const geoData = (ind.geographic || (ind as any).geographic_distribution || []).slice(0, 10)
  const stageData = Object.entries(ind.stage_breakdown || {}).map(([k, v]) => ({ name: k, value: v as number }))

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">{ind.industry}</h1>
        <p className="text-sm text-gray-500 mt-1">Industry Overview</p>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <StatCard label="Startups" value={num(ind.startup_count)} />
        <StatCard label="Total Funding" value={usd(ind.total_funding)} />
        <StatCard label="Avg Funding" value={usd(ind.avg_funding)} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Geographic distribution */}
        <Card>
          <SectionHeader>Geographic Distribution</SectionHeader>
          <ResponsiveContainer width="100%" height={300} className="mt-3">
            <BarChart data={geoData} layout="vertical" margin={{ left: 100 }}>
              <XAxis type="number" />
              <YAxis type="category" dataKey="city" width={90} tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="count" fill="#4f46e5" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        {/* Stage breakdown */}
        <Card>
          <SectionHeader>Funding Stage Breakdown</SectionHeader>
          {stageData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300} className="mt-3">
              <PieChart>
                <Pie data={stageData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} label>
                  {stageData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : <p className="text-sm text-gray-400 mt-3">No stage data</p>}
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top startups */}
        <Card>
          <SectionHeader>Top Startups</SectionHeader>
          <div className="space-y-2 mt-3">
            {ind.top_startups?.map((s: any, i: number) => (
              <div key={s.startup_id} className="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50">
                <div className="flex items-center gap-3">
                  <span className="text-xs text-gray-400 w-5">{i + 1}.</span>
                  <div>
                    <EntityLink type="Startup" name={s.name} id={s.startup_id} />
                    <p className="text-xs text-gray-400">{s.city}</p>
                  </div>
                </div>
                <p className="text-sm font-medium">{usd(s.funding_usd)}</p>
              </div>
            ))}
          </div>
        </Card>

        {/* Key investors */}
        <Card>
          <SectionHeader>Key Investors</SectionHeader>
          <div className="space-y-2 mt-3">
            {ind.key_investors?.map((inv: any) => (
              <div key={inv.investor} className="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50">
                <Link href={`/investor/${encodeURIComponent(inv.investor)}`} className="text-brand-600 hover:underline font-medium text-sm">
                  {inv.investor}
                </Link>
                <span className="text-xs text-gray-500">{inv.startup_count} investments</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Sub-industries */}
      {ind.sub_industries?.length > 0 && (
        <Card>
          <SectionHeader>Sub-Industries</SectionHeader>
          <div className="flex flex-wrap gap-2 mt-3">
            {ind.sub_industries.map((sub: any) => (
              <span key={sub.industry || sub} className="px-3 py-1 bg-pink-50 text-pink-700 rounded-full text-xs">
                {sub.industry || sub} {sub.startup_count ? `(${sub.startup_count})` : ''}
              </span>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}
