'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { fetchCityProfile, fetchCityComparison } from '@/lib/api'
import { usd, num } from '@/lib/fmt'
import { Loading, Card, SectionHeader, StatCard, EntityLink } from '@/components/shared'

const CITIES = [
  'London','Singapore','Berlin','Silicon Valley','Madrid','Sao Paulo',
  'Stockholm','Zurich','Los Angeles','Tokyo','Boston','Paris',
  'Shanghai','Hangzhou','Tel Aviv','Shenzhen','Guangzhou','Seoul','Beijing','NYC',
]

export default function CitiesDashboard() {
  const [selected, setSelected] = useState(['London', 'Berlin'])

  const { data: comparison, isLoading } = useQuery({
    queryKey: ['cityCompare', selected],
    queryFn: () => fetchCityComparison(selected),
    enabled: selected.length >= 2,
  })

  const toggleCity = (city: string) => {
    if (selected.includes(city)) {
      if (selected.length > 2) setSelected(selected.filter(c => c !== city))
    } else if (selected.length < 4) {
      setSelected([...selected, city])
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">City Ecosystem Comparison</h1>
        <p className="text-sm text-gray-500 mt-1">Select 2-4 cities to compare side by side</p>
      </div>

      {/* City selector */}
      <Card>
        <div className="flex flex-wrap gap-2">
          {CITIES.map(city => (
            <button key={city}
              onClick={() => toggleCity(city)}
              className={`px-3 py-1.5 rounded-full text-sm transition-colors ${
                selected.includes(city)
                  ? 'bg-brand-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}>
              {city}
            </button>
          ))}
        </div>
      </Card>

      {isLoading ? <Loading /> : comparison && (
        <>
          {/* Stats comparison */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(comparison.cities || {}).map(([city, data]: [string, any]) => (
              <Card key={city}>
                <Link href={`/city/${encodeURIComponent(city)}`} className="text-lg font-bold text-brand-600 hover:underline">
                  {city}
                </Link>
                <div className="mt-3 space-y-2 text-sm">
                  <div className="flex justify-between"><span className="text-gray-500">Startups</span><span className="font-medium">{data.startup_count}</span></div>
                  <div className="flex justify-between"><span className="text-gray-500">Total Funding</span><span className="font-medium">{usd(data.total_funding)}</span></div>
                  <div className="flex justify-between"><span className="text-gray-500">Avg Funding</span><span className="font-medium">{usd(data.avg_funding)}</span></div>
                </div>
                {data.top_industries?.length > 0 && (
                  <div className="mt-3 pt-3 border-t">
                    <p className="text-xs font-medium text-gray-500 mb-1">Top Industries</p>
                    {data.top_industries.slice(0, 3).map((ind: any) => (
                      <div key={ind.industry} className="flex justify-between text-xs mt-1">
                        <span>{ind.industry}</span><span className="text-gray-400">{ind.count}</span>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            ))}
          </div>

          {/* Shared investors */}
          {comparison.shared_investors?.length > 0 && (
            <Card>
              <SectionHeader>Shared Investors</SectionHeader>
              <p className="text-xs text-gray-400 mt-1">Investors active in multiple selected cities</p>
              <div className="space-y-2 mt-3">
                {comparison.shared_investors.slice(0, 15).map((inv: any) => (
                  <div key={inv.investor} className="flex items-center justify-between p-2 rounded hover:bg-gray-50">
                    <Link href={`/investor/${encodeURIComponent(inv.investor)}`}
                      className="text-brand-600 hover:underline text-sm font-medium">{inv.investor}</Link>
                    <div className="flex gap-1">
                      {inv.active_cities?.map((c: string) => (
                        <span key={c} className="px-2 py-0.5 bg-amber-50 text-amber-700 rounded text-xs">{c}</span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Ecosystem peer scores */}
          {(comparison as any).ecosystem_peer_scores?.length > 0 && (
            <Card>
              <SectionHeader>Ecosystem Similarity Scores</SectionHeader>
              <div className="space-y-2 mt-3">
                {(comparison as any).ecosystem_peer_scores.map((p: any, i: number) => (
                  <div key={i} className="flex items-center gap-4 p-2 rounded hover:bg-gray-50">
                    <span className="text-sm font-medium">{p.city_a}</span>
                    <div className="flex-1 h-2 bg-gray-100 rounded-full">
                      <div className="h-full bg-brand-500 rounded-full" style={{ width: `${Math.min((p.score || 0) * 10, 100)}%` }} />
                    </div>
                    <span className="text-sm font-medium">{p.city_b}</span>
                    <span className="text-xs text-gray-400">{p.score}</span>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </>
      )}
    </div>
  )
}
