import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
} from 'recharts'
import { fetchEcosystem, fetchCitySpecializations } from '../api/client'
import StatCard from './shared/StatCard'
import Loading from './shared/Loading'
import { fmtUsd } from './shared/fmt'

const CITIES = [
  'London', 'Singapore', 'Berlin', 'Silicon Valley', 'Madrid', 'Sao Paulo',
  'Stockholm', 'Zurich', 'Los Angeles', 'Tokyo', 'Boston', 'Paris',
  'Shanghai', 'Hangzhou', 'Tel Aviv', 'Shenzhen', 'Guangzhou', 'Seoul',
  'Beijing', 'NYC',
]

export default function CityEcosystem() {
  const { name: paramCity } = useParams<{ name: string }>()
  const [selectedCity, setSelectedCity] = useState(
    paramCity ? decodeURIComponent(paramCity) : 'London',
  )
  const [compareCity, setCompareCity] = useState('')

  const { data: eco, isLoading } = useQuery({
    queryKey: ['ecosystem', selectedCity],
    queryFn: () => fetchEcosystem(selectedCity),
    enabled: !!selectedCity,
  })

  const { data: eco2 } = useQuery({
    queryKey: ['ecosystem', compareCity],
    queryFn: () => fetchEcosystem(compareCity),
    enabled: !!compareCity,
  })

  const { data: specs } = useQuery({
    queryKey: ['citySpecs'],
    queryFn: fetchCitySpecializations,
  })

  const renderEcosystem = (data: any, title: string) => (
    <div className="space-y-4">
      <h2 className="text-xl font-bold">{title}</h2>
      <div className="grid grid-cols-3 gap-3">
        <StatCard label="Startups" value={data.startup_count} />
        <StatCard label="Total Funding" value={fmtUsd(data.total_funding)} />
        <StatCard label="Founders" value={data.founder_count} />
      </div>

      {/* Industries */}
      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <h3 className="text-sm font-semibold mb-3">Industry Breakdown</h3>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={data.industries?.slice(0, 10)} layout="vertical" margin={{ left: 100 }}>
            <XAxis type="number" />
            <YAxis type="category" dataKey="industry" width={90} tick={{ fontSize: 11 }} />
            <Tooltip formatter={(v: number) => fmtUsd(v)} />
            <Bar dataKey="count" fill="#4f46e5" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Top startups */}
      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <h3 className="text-sm font-semibold mb-3">Top Startups</h3>
        <div className="space-y-1">
          {data.top_startups?.map((s: any) => (
            <div key={s.startup_id} className="flex justify-between text-sm py-1 border-b border-gray-100">
              <Link to={`/startup/${s.startup_id}`} className="text-indigo-600 hover:underline">
                {s.name}
              </Link>
              <span className="text-gray-500">{fmtUsd(s.funding_usd)}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Top investors */}
      {data.top_investors?.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <h3 className="text-sm font-semibold mb-3">Active Investors</h3>
          <div className="flex flex-wrap gap-1">
            {data.top_investors.map((inv: any) => (
              <Link
                key={inv.investor}
                to={`/investors/${encodeURIComponent(inv.investor)}`}
                className="px-2 py-1 bg-indigo-50 text-indigo-700 rounded text-xs"
              >
                {inv.investor} ({inv.startups})
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  )

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">City Ecosystems</h1>

      <div className="flex gap-4 items-center">
        <select
          value={selectedCity}
          onChange={(e) => setSelectedCity(e.target.value)}
          className="border border-gray-300 rounded-lg px-4 py-2 text-sm"
        >
          {CITIES.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>

        <span className="text-gray-400 text-sm">vs</span>

        <select
          value={compareCity}
          onChange={(e) => setCompareCity(e.target.value)}
          className="border border-gray-300 rounded-lg px-4 py-2 text-sm"
        >
          <option value="">Select city to compare</option>
          {CITIES.filter((c) => c !== selectedCity).map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </div>

      {isLoading ? (
        <Loading />
      ) : (
        <div className={`grid gap-6 ${compareCity && eco2 ? 'grid-cols-2' : 'grid-cols-1'}`}>
          {eco && renderEcosystem(eco, selectedCity)}
          {compareCity && eco2 && renderEcosystem(eco2, compareCity)}
        </div>
      )}
    </div>
  )
}
