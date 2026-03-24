'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { fetchTopPairs, fetchInvestorThesis } from '@/lib/api'
import { usd } from '@/lib/fmt'
import { Loading, Card, SectionHeader, EntityLink, Badge } from '@/components/shared'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis } from 'recharts'

const COLORS = ['#4f46e5','#7c3aed','#059669','#d97706','#dc2626','#0891b2','#db2777','#6366f1']

export default function InvestorsDashboard() {
  const [selected, setSelected] = useState('')
  const [inputVal, setInputVal] = useState('')

  const { data: pairs, isLoading: l1 } = useQuery({
    queryKey: ['topPairs'], queryFn: () => fetchTopPairs(30),
  })

  const { data: thesis, isLoading: l2 } = useQuery({
    queryKey: ['thesis', selected], queryFn: () => fetchInvestorThesis(selected),
    enabled: !!selected,
  })

  if (l1) return <Loading />

  const focusData = (thesis?.industry_focus ?? []).map((f: any) => ({ name: f.category, value: f.startup_count }))
  const stageData = (thesis?.stage_profile ?? []).map((s: any) => ({ name: s.stage, count: s.count }))

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Investor Intelligence</h1>
        <p className="text-sm text-gray-500 mt-1">Explore investor portfolios, co-investment networks, and thesis analysis</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Co-investor pairs */}
        <Card>
          <SectionHeader>Top Co-Investor Pairs</SectionHeader>
          <div className="space-y-1 mt-3 max-h-[500px] overflow-y-auto">
            {pairs?.map((p, i) => (
              <div key={i} className="flex items-center justify-between p-2 hover:bg-gray-50 rounded text-sm">
                <div className="flex gap-2 items-center">
                  <button onClick={() => setSelected(p.investor_a)} className="text-brand-600 hover:underline">{p.investor_a}</button>
                  <span className="text-gray-300">+</span>
                  <button onClick={() => setSelected(p.investor_b)} className="text-brand-600 hover:underline">{p.investor_b}</button>
                </div>
                <Badge color="indigo">{p.co_investment_count}x</Badge>
              </div>
            ))}
          </div>
        </Card>

        {/* Investor thesis panel */}
        <div className="space-y-4">
          <Card>
            <SectionHeader>Investor Thesis Analysis</SectionHeader>
            <div className="flex gap-2 mt-3">
              <input type="text" placeholder="Enter investor name..."
                value={inputVal}
                onChange={e => setInputVal(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && setSelected(inputVal)}
                className="flex-1 px-3 py-2 border border-gray-200 rounded-lg text-sm" />
              <button onClick={() => setSelected(inputVal)}
                className="bg-brand-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-brand-700">Analyze</button>
            </div>
          </Card>

          {selected && (l2 ? <Loading /> : thesis && (
            <>
              <Card>
                <div className="flex items-center justify-between">
                  <Link href={`/investor/${encodeURIComponent(thesis.investor)}`} className="text-xl font-bold text-brand-600 hover:underline">
                    {thesis.investor}
                  </Link>
                  <div className="text-right text-sm text-gray-500">
                    <p>{thesis.portfolio_size} companies</p>
                    <p>{usd(thesis.total_deployed)} deployed</p>
                  </div>
                </div>
              </Card>

              {/* Focus pie + Stage bar */}
              <div className="grid grid-cols-2 gap-4">
                <Card>
                  <p className="text-xs font-medium text-gray-500 mb-2">Industry Focus</p>
                  {focusData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={180}>
                      <PieChart>
                        <Pie data={focusData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={65} label={false}>
                          {focusData.map((_: any, i: number) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : <p className="text-sm text-gray-400">No data</p>}
                </Card>
                <Card>
                  <p className="text-xs font-medium text-gray-500 mb-2">Stage Preference</p>
                  {stageData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={180}>
                      <BarChart data={stageData.slice(0, 6)}>
                        <XAxis dataKey="name" tick={{ fontSize: 9 }} />
                        <YAxis hide />
                        <Tooltip />
                        <Bar dataKey="count" fill="#4f46e5" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : <p className="text-sm text-gray-400">No data</p>}
                </Card>
              </div>

              {/* Cities + Co-investors */}
              <Card>
                <p className="text-xs font-medium text-gray-500 mb-2">Active In</p>
                <div className="flex flex-wrap gap-1">
                  {thesis.city_presence?.map((c: any) => (
                    <Link key={c.city} href={`/city/${encodeURIComponent(c.city)}`}
                      className="px-2 py-0.5 bg-amber-50 text-amber-700 rounded text-xs hover:bg-amber-100">
                      {c.city} ({c.startup_count})
                    </Link>
                  ))}
                </div>
                {thesis.co_investors?.length && thesis.co_investors.length > 0 && (
                  <>
                    <p className="text-xs font-medium text-gray-500 mt-4 mb-2">Top Co-Investors</p>
                    <div className="flex flex-wrap gap-1">
                      {thesis.co_investors.slice(0, 10).map((ci: any) => (
                        <button key={ci.name} onClick={() => { setSelected(ci.name); setInputVal(ci.name) }}
                          className="px-2 py-0.5 bg-green-50 text-green-700 rounded text-xs hover:bg-green-100">
                          {ci.name}
                        </button>
                      ))}
                    </div>
                  </>
                )}
              </Card>
            </>
          ))}
        </div>
      </div>
    </div>
  )
}
