'use client'

import { useParams } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis } from 'recharts'
import { fetchInvestorThesis } from '@/lib/api'
import { usd } from '@/lib/fmt'
import { Loading, Card, SectionHeader, EntityLink, Badge } from '@/components/shared'

const COLORS = ['#4f46e5','#7c3aed','#059669','#d97706','#dc2626','#0891b2','#db2777','#6366f1']

export default function InvestorPage() {
  const { name } = useParams<{ name: string }>()
  const decoded = decodeURIComponent(name)
  const { data: thesis, isLoading } = useQuery({
    queryKey: ['thesis', decoded], queryFn: () => fetchInvestorThesis(decoded),
  })

  if (isLoading) return <Loading />
  if (!thesis) return <p className="text-gray-500 py-8">Investor not found</p>

  const focusData = (thesis.industry_focus ?? []).map((f: any) => ({ name: f.category, value: f.startup_count }))
  const stageData = (thesis.stage_profile ?? []).map((s: any) => ({ name: s.stage, count: s.count }))

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">{thesis.investor}</h1>
        <div className="flex items-center gap-3 mt-2 text-sm text-gray-500">
          <span>{thesis.portfolio_size} portfolio companies</span>
          <span>&middot;</span>
          <span>{usd(thesis.total_deployed)} deployed</span>
          {thesis.primary_focus && <><span>&middot;</span><Badge color="pink">{thesis.primary_focus}</Badge></>}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Industry focus */}
        <Card>
          <SectionHeader>Industry Focus</SectionHeader>
          {focusData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250} className="mt-3">
              <PieChart>
                <Pie data={focusData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label={({ name, value }) => `${name} (${value})`} labelLine={false}>
                  {focusData.map((_: any, i: number) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : <p className="text-sm text-gray-400 mt-3">No focus data</p>}
        </Card>

        {/* Stage preference */}
        <Card>
          <SectionHeader>Stage Preference</SectionHeader>
          {stageData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250} className="mt-3">
              <BarChart data={stageData}>
                <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#4f46e5" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <p className="text-sm text-gray-400 mt-3">No stage data</p>}
        </Card>

        {/* Geographic presence */}
        <Card>
          <SectionHeader>Active In</SectionHeader>
          <div className="space-y-2 mt-3">
            {thesis.city_presence?.map((c: any) => (
              <div key={c.city} className="flex justify-between items-center">
                <Link href={`/city/${encodeURIComponent(c.city)}`} className="text-sm text-brand-600 hover:underline">{c.city}</Link>
                <span className="text-xs text-gray-500">{c.startup_count} startups</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Co-investors */}
      {thesis.co_investors?.length > 0 && (
        <Card>
          <SectionHeader>Top Co-Investors</SectionHeader>
          <div className="flex flex-wrap gap-2 mt-3">
            {thesis.co_investors.map((ci: any) => (
              <Link key={ci.name} href={`/investor/${encodeURIComponent(ci.name)}`}
                className="px-3 py-1.5 bg-green-50 text-green-700 rounded-full text-sm hover:bg-green-100">
                {ci.name} ({ci.shared})
              </Link>
            ))}
          </div>
        </Card>
      )}

      {/* Portfolio */}
      <Card>
        <SectionHeader>Portfolio ({thesis.portfolio_size} companies)</SectionHeader>
        <div className="overflow-x-auto mt-3">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-gray-500">
                <th className="p-2">Startup</th><th className="p-2">City</th>
                <th className="p-2">Industry</th><th className="p-2">Funding</th><th className="p-2">Stage</th>
              </tr>
            </thead>
            <tbody>
              {thesis.portfolio?.map((s: any) => (
                <tr key={s.startup_id} className="border-b hover:bg-gray-50">
                  <td className="p-2"><EntityLink type="Startup" name={s.name} id={s.startup_id} /></td>
                  <td className="p-2 text-gray-500">{s.city}</td>
                  <td className="p-2 text-gray-500">{s.industry}</td>
                  <td className="p-2">{usd(s.funding_usd)}</td>
                  <td className="p-2"><Badge>{s.funding_stage || '--'}</Badge></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <div className="text-center">
        <Link href={`/explore?q=${encodeURIComponent(thesis.investor)}`}
          className="inline-flex items-center gap-2 px-6 py-3 bg-gray-900 text-white rounded-lg hover:bg-gray-800 text-sm font-medium">
          Explore in Graph
        </Link>
      </div>
    </div>
  )
}
