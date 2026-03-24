'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchSearch } from '@/lib/api'
import { Card, SectionHeader, EntityBadge, EntityLink } from '@/components/shared'
import { MessageSquare, Send, Sparkles } from 'lucide-react'

const EXAMPLES = [
  'Fintech startups in London',
  'AI/ML investors',
  'Berlin startup ecosystem',
  'Sequoia Capital',
  'Series A healthcare',
  'Singapore',
]

export default function AskPage() {
  const [query, setQuery] = useState('')
  const [submitted, setSubmitted] = useState('')

  const { data: results, isLoading } = useQuery({
    queryKey: ['search', submitted],
    queryFn: () => fetchSearch(submitted),
    enabled: !!submitted,
  })

  const handleSubmit = (q: string) => {
    setQuery(q)
    setSubmitted(q)
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="text-center pt-8">
        <div className="inline-flex items-center gap-2 mb-4">
          <Sparkles className="w-8 h-8 text-brand-600" />
          <h1 className="text-3xl font-bold">Ask StartupGraph</h1>
        </div>
        <p className="text-gray-500">Search across 3,022 startups, 784 investors, 1,525 founders, 20 cities</p>
      </div>

      {/* Search box */}
      <Card>
        <form onSubmit={e => { e.preventDefault(); handleSubmit(query) }} className="flex gap-2">
          <input type="text" value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Search for anything... startups, investors, cities, industries"
            className="flex-1 px-4 py-3 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" />
          <button type="submit" className="bg-brand-600 text-white px-6 py-3 rounded-xl hover:bg-brand-700 flex items-center gap-2">
            <Send className="w-4 h-4" /> Search
          </button>
        </form>

        {/* Example queries */}
        {!submitted && (
          <div className="mt-4">
            <p className="text-xs text-gray-400 mb-2">Try these:</p>
            <div className="flex flex-wrap gap-2">
              {EXAMPLES.map(ex => (
                <button key={ex} onClick={() => handleSubmit(ex)}
                  className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded-full text-sm hover:bg-gray-200 transition-colors">
                  {ex}
                </button>
              ))}
            </div>
          </div>
        )}
      </Card>

      {/* Results */}
      {isLoading && (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-brand-600" />
        </div>
      )}

      {results && (
        <Card>
          <p className="text-sm text-gray-500 mb-4">{results.length} results for "{submitted}"</p>
          {results.length === 0 ? (
            <p className="text-gray-400 text-center py-8">No results found. Try a different query.</p>
          ) : (
            <div className="space-y-1">
              {results.map((r, i) => (
                <div key={i} className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors">
                  <EntityBadge type={r.type} />
                  <EntityLink type={r.type} name={r.name} id={r.id} />
                  <span className="text-xs text-gray-300 ml-auto">
                    {r.score?.toFixed(1)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      {/* Info */}
      <div className="text-center text-xs text-gray-400 pb-8">
        <p>Full NL-to-Cypher AI queries coming in Phase 2</p>
        <p>Current: full-text search across all graph entities</p>
      </div>
    </div>
  )
}
