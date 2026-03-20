import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from 'recharts'
import { fetchIndustryByRegion, fetchIndustryRanking, fetchRegionComparison } from '../api/client'
import StatCard from './shared/StatCard'
import Loading from './shared/Loading'
import { fmtUsd, fmtNum } from './shared/fmt'

const COLORS = [
  '#4f46e5', '#7c3aed', '#2563eb', '#0891b2', '#059669',
  '#d97706', '#dc2626', '#db2777', '#6366f1', '#8b5cf6',
]

const REGION_COLORS: Record<string, string> = {
  'Europe': '#4f46e5',
  'East Asia': '#dc2626',
  'North America': '#059669',
  'Southeast Asia': '#d97706',
  'Latin America': '#2563eb',
  'Middle East': '#8b5cf6',
}

export default function Dashboard() {
  const navigate = useNavigate()
  const { data: heatmap, isLoading: l1 } = useQuery({ queryKey: ['indByRegion'], queryFn: fetchIndustryByRegion })
  const { data: ranking, isLoading: l2 } = useQuery({ queryKey: ['indRanking'], queryFn: () => fetchIndustryRanking(15) })
  const { data: regions, isLoading: l3 } = useQuery({ queryKey: ['regionCmp'], queryFn: fetchRegionComparison })

  if (l1 || l2 || l3) return <Loading />

  const totalStartups = regions?.reduce((s, r) => s + r.startup_count, 0) ?? 0
  const totalFunding = regions?.reduce((s, r) => s + (r.total_funding ?? 0), 0) ?? 0

  // Heatmap data
  const allIndustries = ranking?.map((r) => r.industry) ?? []
  const regionNames = Object.keys(heatmap ?? {})

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold">Global Startups Dashboard</h1>

      {/* Stats row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Total Startups" value={fmtNum(totalStartups)} />
        <StatCard label="Total Funding" value={fmtUsd(totalFunding)} />
        <StatCard label="Cities" value="20" />
        <StatCard label="Regions" value={String(regionNames.length)} />
      </div>

      {/* Industry ranking */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-lg font-semibold mb-4">Top Industries by Total Funding</h2>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart
            data={ranking}
            layout="vertical"
            margin={{ left: 140 }}
          >
            <XAxis type="number" tickFormatter={(v) => fmtUsd(v)} />
            <YAxis
              type="category"
              dataKey="industry"
              width={130}
              tick={{ fontSize: 12, cursor: 'pointer' }}
              onClick={(e: any) => {
                if (e?.value) navigate(`/industry/${encodeURIComponent(e.value)}`)
              }}
            />
            <Tooltip formatter={(v: number) => fmtUsd(v)} />
            <Bar dataKey="total_funding" radius={[0, 4, 4, 0]}>
              {ranking?.map((_, i) => (
                <Cell
                  key={i}
                  fill={COLORS[i % COLORS.length]}
                  cursor="pointer"
                  onClick={() => navigate(`/industry/${encodeURIComponent(ranking![i].industry)}`)}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Region comparison */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-lg font-semibold mb-4">Region Comparison</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {regions?.map((r) => (
            <div
              key={r.region}
              className="border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
              style={{ borderLeftColor: REGION_COLORS[r.region] ?? '#999', borderLeftWidth: 4 }}
            >
              <p className="font-semibold text-sm">{r.region}</p>
              <p className="text-2xl font-bold mt-1">{r.startup_count}</p>
              <p className="text-xs text-gray-500">startups</p>
              <p className="text-sm font-medium mt-2">{fmtUsd(r.total_funding)}</p>
              <p className="text-xs text-gray-400 mt-1">Top: {r.top_industry}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Heatmap */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 overflow-x-auto">
        <h2 className="text-lg font-semibold mb-4">Industry x Region Heatmap</h2>
        <table className="text-xs w-full">
          <thead>
            <tr>
              <th className="text-left p-2">Industry</th>
              {regionNames.map((r) => (
                <th key={r} className="p-2 text-center">{r}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {allIndustries.map((ind) => (
              <tr
                key={ind}
                className="hover:bg-gray-50 cursor-pointer"
                onClick={() => navigate(`/industry/${encodeURIComponent(ind)}`)}
              >
                <td className="p-2 font-medium">{ind}</td>
                {regionNames.map((reg) => {
                  const val = heatmap?.[reg]?.[ind] ?? 0
                  const maxVal = Math.max(
                    ...allIndustries.map((i) => heatmap?.[reg]?.[i] ?? 0),
                  )
                  const intensity = maxVal > 0 ? val / maxVal : 0
                  return (
                    <td
                      key={reg}
                      className="p-2 text-center"
                      style={{
                        backgroundColor: val > 0
                          ? `rgba(79, 70, 229, ${0.1 + intensity * 0.6})`
                          : 'transparent',
                        color: intensity > 0.5 ? 'white' : 'inherit',
                      }}
                    >
                      {val || ''}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
