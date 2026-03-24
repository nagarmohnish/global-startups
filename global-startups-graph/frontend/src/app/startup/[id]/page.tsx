'use client'

import { useParams } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { fetchStartupProfile, fetchInvestorMatch } from '@/lib/api'
import { usd } from '@/lib/fmt'
import { Loading, Card, SectionHeader, Badge, EntityLink } from '@/components/shared'
import { ExternalLink, MapPin, Calendar, DollarSign, Users, Trophy } from 'lucide-react'

export default function StartupPage() {
  const { id } = useParams<{ id: string }>()
  const { data: startup, isLoading } = useQuery({
    queryKey: ['startup', id], queryFn: () => fetchStartupProfile(id),
  })
  const { data: matches } = useQuery({
    queryKey: ['investorMatch', id], queryFn: () => fetchInvestorMatch(id),
  })

  if (isLoading) return <Loading />
  if (!startup || 'error' in startup) return <p className="text-gray-500 py-8">Startup not found</p>

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold">{startup.name}</h1>
            {startup.funding_stage && <Badge color="indigo">{startup.funding_stage}</Badge>}
          </div>
          <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
            {startup.city && <span className="flex items-center gap-1"><MapPin className="w-3.5 h-3.5" />{startup.city}, {startup.country}</span>}
            {startup.founded_year && <span className="flex items-center gap-1"><Calendar className="w-3.5 h-3.5" />Founded {startup.founded_year}</span>}
            {startup.primary_industry && <Link href={`/industry/${encodeURIComponent(startup.primary_industry)}`} className="flex items-center gap-1 text-brand-600 hover:underline">{startup.primary_industry}</Link>}
          </div>
        </div>
        {startup.website && (
          <a href={startup.website} target="_blank" rel="noopener" className="flex items-center gap-1.5 px-4 py-2 bg-brand-600 text-white rounded-lg text-sm hover:bg-brand-700">
            <ExternalLink className="w-4 h-4" /> Website
          </a>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card><p className="text-sm text-gray-500">Total Funding</p><p className="text-2xl font-bold mt-1">{usd(startup.funding_usd)}</p></Card>
        <Card><p className="text-sm text-gray-500">Stage</p><p className="text-2xl font-bold mt-1">{startup.funding_stage || '--'}</p></Card>
        <Card><p className="text-sm text-gray-500">Team Size</p><p className="text-2xl font-bold mt-1">{startup.team_size_category || '--'}</p></Card>
        <Card><p className="text-sm text-gray-500">Revenue</p><p className="text-2xl font-bold mt-1">{usd(startup.revenue_usd)}</p></Card>
      </div>

      {/* Description */}
      {startup.description && (
        <Card>
          <SectionHeader>About</SectionHeader>
          <p className="text-sm text-gray-600 mt-2 leading-relaxed">{startup.description}</p>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Founders & Investors */}
        <Card>
          <SectionHeader>Founders</SectionHeader>
          <div className="flex flex-wrap gap-2 mt-3">
            {startup.founders?.length ? startup.founders.map((f: any) => (
              <Badge key={f.name || f} color="purple">{f.name || f}</Badge>
            )) : <p className="text-sm text-gray-400">No founder data</p>}
          </div>

          <SectionHeader>Investors</SectionHeader>
          <div className="flex flex-wrap gap-2 mt-3">
            {startup.investors?.length ? startup.investors.map((inv: any) => (
              <Link key={inv.name || inv} href={`/investor/${encodeURIComponent(inv.name || inv)}`}
                className="px-2.5 py-1 bg-green-50 text-green-700 rounded-full text-xs hover:bg-green-100">
                {inv.name || inv}
              </Link>
            )) : <p className="text-sm text-gray-400">No investor data</p>}
          </div>

          <SectionHeader>Industries</SectionHeader>
          <div className="flex flex-wrap gap-2 mt-3">
            {startup.industries?.map((ind: string) => (
              <Link key={ind} href={`/industry/${encodeURIComponent(ind)}`}
                className="px-2.5 py-1 bg-pink-50 text-pink-700 rounded-full text-xs hover:bg-pink-100">
                {ind}
              </Link>
            ))}
          </div>
        </Card>

        {/* Competitors */}
        <Card>
          <SectionHeader>Competitors</SectionHeader>
          {startup.competitors?.length ? (
            <div className="space-y-2 mt-3">
              {startup.competitors.map((c: any) => (
                <div key={c.startup_id} className="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
                  <div>
                    <EntityLink type="Startup" name={c.name} id={c.startup_id} />
                    <p className="text-xs text-gray-400">{c.city} &middot; {c.industry}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium">{usd(c.funding_usd)}</p>
                    <div className="w-16 h-1.5 bg-gray-200 rounded-full mt-1">
                      <div className="h-full bg-red-400 rounded-full" style={{ width: `${Math.min(c.score * 8, 100)}%` }} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : <p className="text-sm text-gray-400 mt-3">No competitors identified</p>}
        </Card>
      </div>

      {/* Similar startups */}
      {startup.similar?.length > 0 && (
        <Card>
          <SectionHeader>Similar Startups (Cross-City)</SectionHeader>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-3">
            {startup.similar.map((s: any) => (
              <div key={s.startup_id} className="flex items-center justify-between p-3 border rounded-lg">
                <div>
                  <EntityLink type="Startup" name={s.name} id={s.startup_id} />
                  <p className="text-xs text-gray-400">{s.city} &middot; {s.industry}</p>
                </div>
                <p className="text-sm font-medium">{usd(s.funding_usd)}</p>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Investor matches */}
      {matches && matches.length > 0 && (
        <Card>
          <SectionHeader>Potential Investors</SectionHeader>
          <p className="text-xs text-gray-400 mt-1">Investors who fund similar startups but haven&apos;t invested here</p>
          <div className="space-y-2 mt-3">
            {matches.slice(0, 10).map((m: any) => (
              <div key={m.investor} className="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
                <Link href={`/investor/${encodeURIComponent(m.investor)}`}
                  className="text-brand-600 hover:underline font-medium text-sm">{m.investor}</Link>
                <span className="text-xs text-gray-500">Score: {m.match_score}</span>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Explore in graph */}
      <div className="text-center">
        <Link href={`/explore?q=${encodeURIComponent(startup.name)}`}
          className="inline-flex items-center gap-2 px-6 py-3 bg-gray-900 text-white rounded-lg hover:bg-gray-800 text-sm font-medium">
          Explore in Graph
        </Link>
      </div>
    </div>
  )
}
