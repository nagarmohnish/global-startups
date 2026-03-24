'use client'

import { useParams } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { fetchCityProfile } from '@/lib/api'
import { usd, num } from '@/lib/fmt'
import { Loading, Card, SectionHeader, StatCard, EntityLink, Badge } from '@/components/shared'

export default function CityPage() {
  const { name } = useParams<{ name: string }>()
  const decoded = decodeURIComponent(name)
  const { data: city, isLoading } = useQuery({
    queryKey: ['cityProfile', decoded], queryFn: () => fetchCityProfile(decoded),
  })

  if (isLoading) return <Loading />
  if (!city) return <p className="text-gray-500 py-8">City not found</p>

  const specData = (city.specializations || (city as any).industry_breakdown || [])
    .slice(0, 12)
    .map((s: any) => ({
      name: s.industry,
      count: s.count || s.startup_count,
      lq: s.lq || s.location_quotient,
    }))

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">{city.city}</h1>
        <p className="text-sm text-gray-500 mt-1">Startup Ecosystem Profile</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Startups" value={num(city.startup_count)} />
        <StatCard label="Total Funding" value={usd(city.total_funding)} />
        <StatCard label="Avg Funding" value={usd(city.avg_funding)} />
        <StatCard label="Founders" value={num(city.founder_count)} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Industry breakdown */}
        <Card>
          <SectionHeader>Industry Specializations</SectionHeader>
          <ResponsiveContainer width="100%" height={350} className="mt-3">
            <BarChart data={specData} layout="vertical" margin={{ left: 120 }}>
              <XAxis type="number" />
              <YAxis type="category" dataKey="name" width={110} tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v: number, name: string) => name === 'lq' ? v.toFixed(2) : v} />
              <Bar dataKey="count" fill="#4f46e5" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
          {specData.some((s: any) => s.lq) && (
            <div className="mt-3">
              <p className="text-xs font-medium text-gray-500 mb-2">Location Quotient (LQ &gt; 1 = genuine specialization)</p>
              <div className="flex flex-wrap gap-2">
                {specData.filter((s: any) => s.lq > 1).map((s: any) => (
                  <span key={s.name} className="px-2 py-1 bg-green-50 text-green-700 rounded text-xs">
                    {s.name}: LQ {s.lq?.toFixed(1)}
                  </span>
                ))}
              </div>
            </div>
          )}
        </Card>

        {/* Top startups */}
        <Card>
          <SectionHeader>Top Startups by Funding</SectionHeader>
          <div className="space-y-2 mt-3">
            {city.top_startups?.map((s: any, i: number) => (
              <div key={s.startup_id} className="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50">
                <div className="flex items-center gap-3">
                  <span className="text-xs text-gray-400 w-5">{i + 1}.</span>
                  <div>
                    <EntityLink type="Startup" name={s.name} id={s.startup_id} />
                    <p className="text-xs text-gray-400">{s.industry}</p>
                  </div>
                </div>
                <p className="text-sm font-medium">{usd(s.funding_usd)}</p>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top investors */}
        <Card>
          <SectionHeader>Most Active Investors</SectionHeader>
          <div className="flex flex-wrap gap-2 mt-3">
            {city.top_investors?.map((inv: any) => (
              <Link key={inv.investor} href={`/investor/${encodeURIComponent(inv.investor)}`}
                className="px-3 py-1.5 bg-green-50 text-green-700 rounded-full text-sm hover:bg-green-100">
                {inv.investor} ({inv.count || inv.startups})
              </Link>
            ))}
          </div>
        </Card>

        {/* Ecosystem peers */}
        <Card>
          <SectionHeader>Similar Ecosystems</SectionHeader>
          {city.ecosystem_peers?.length > 0 ? (
            <div className="space-y-2 mt-3">
              {city.ecosystem_peers.map((p: any) => (
                <div key={p.city} className="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50">
                  <Link href={`/city/${encodeURIComponent(p.city)}`} className="text-brand-600 hover:underline font-medium">
                    {p.city}
                  </Link>
                  <span className="text-xs text-gray-500">
                    {p.shared_investors} shared investors
                    {p.industry_similarity && ` | ${(p.industry_similarity * 100).toFixed(0)}% similar`}
                  </span>
                </div>
              ))}
            </div>
          ) : <p className="text-sm text-gray-400 mt-3">No ecosystem peer data</p>}
        </Card>
      </div>

      {/* Funding stage distribution */}
      {city.stage_distribution && Object.keys(city.stage_distribution).length > 0 && (
        <Card>
          <SectionHeader>Funding Stage Distribution</SectionHeader>
          <div className="flex flex-wrap gap-2 mt-3">
            {Object.entries(city.stage_distribution).map(([stage, count]) => (
              <div key={stage} className="px-3 py-2 border rounded-lg text-center">
                <p className="text-lg font-bold">{count as number}</p>
                <p className="text-xs text-gray-500">{stage}</p>
              </div>
            ))}
          </div>
        </Card>
      )}

      <div className="text-center">
        <Link href={`/explore?q=${encodeURIComponent(city.city)}`}
          className="inline-flex items-center gap-2 px-6 py-3 bg-gray-900 text-white rounded-lg hover:bg-gray-800 text-sm font-medium">
          Explore in Graph
        </Link>
      </div>
    </div>
  )
}
