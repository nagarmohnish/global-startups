import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts'
import { fetchIndustryPerformance, fetchIndustryStartups } from '../api/client'
import StatCard from './shared/StatCard'
import Loading from './shared/Loading'
import { fmtUsd } from './shared/fmt'

const PIE_COLORS = ['#4f46e5', '#7c3aed', '#2563eb', '#0891b2', '#059669', '#d97706', '#dc2626', '#db2777']

export default function IndustryDeepDive() {
  const { name } = useParams<{ name: string }>()
  const decoded = decodeURIComponent(name ?? '')

  const { data: perf, isLoading: l1 } = useQuery({
    queryKey: ['indPerf', decoded],
    queryFn: () => fetchIndustryPerformance(decoded),
    enabled: !!decoded,
  })
  const { data: startups, isLoading: l2 } = useQuery({
    queryKey: ['indStartups', decoded],
    queryFn: () => fetchIndustryStartups(decoded, 50),
    enabled: !!decoded,
  })

  if (l1 || l2) return <Loading />
  if (!perf) return <p>Industry not found</p>

  const stageData = Object.entries(perf.by_stage ?? {}).map(([stage, count]) => ({
    name: stage,
    value: count as number,
  }))

  const regionData = (perf.by_region ?? []).map((r: any) => ({
    name: r.region,
    count: r.count,
    funding: r.total_funding,
  }))

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Link to="/" className="hover:text-indigo-600">Dashboard</Link>
        <span>/</span>
        <span className="text-gray-900 font-medium">{decoded}</span>
      </div>

      <h1 className="text-2xl font-bold">{decoded}</h1>

      <div className="grid grid-cols-3 gap-4">
        <StatCard label="Startups" value={perf.total_startups} />
        <StatCard label="Total Funding" value={fmtUsd(perf.total_funding)} />
        <StatCard label="Avg Funding" value={fmtUsd(perf.avg_funding)} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Funding stage breakdown */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold mb-4">Funding Stage Breakdown</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie data={stageData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} label>
                {stageData.map((_, i) => (
                  <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Regional distribution */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold mb-4">By Region</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={regionData}>
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#4f46e5" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Top investors */}
      {perf.top_investors?.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold mb-4">Top Investors in {decoded}</h2>
          <div className="flex flex-wrap gap-2">
            {perf.top_investors.map((inv: any) => (
              <Link
                key={inv.investor}
                to={`/investors/${encodeURIComponent(inv.investor)}`}
                className="px-3 py-1.5 bg-indigo-50 text-indigo-700 rounded-full text-sm hover:bg-indigo-100"
              >
                {inv.investor} ({inv.startup_count})
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Startups table */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 overflow-x-auto">
        <h2 className="text-lg font-semibold mb-4">Top Startups</h2>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left text-gray-500">
              <th className="p-2">Name</th>
              <th className="p-2">City</th>
              <th className="p-2">Founded</th>
              <th className="p-2">Funding</th>
              <th className="p-2">Stage</th>
            </tr>
          </thead>
          <tbody>
            {startups?.map((s) => (
              <tr key={s.startup_id} className="border-b hover:bg-gray-50">
                <td className="p-2">
                  <Link to={`/startup/${s.startup_id}`} className="text-indigo-600 hover:underline font-medium">
                    {s.name}
                  </Link>
                </td>
                <td className="p-2">{s.city}</td>
                <td className="p-2">{s.founded_year ?? '—'}</td>
                <td className="p-2">{fmtUsd(s.funding_usd)}</td>
                <td className="p-2">{s.funding_stage ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
