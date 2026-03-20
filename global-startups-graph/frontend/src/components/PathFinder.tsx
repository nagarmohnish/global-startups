import { useState } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchShortestPath, fetchSearch } from '../api/client'
import Loading from './shared/Loading'

const TYPE_COLORS: Record<string, string> = {
  Startup: 'bg-blue-100 text-blue-800',
  Investor: 'bg-green-100 text-green-800',
  Founder: 'bg-purple-100 text-purple-800',
  City: 'bg-orange-100 text-orange-800',
  Industry: 'bg-pink-100 text-pink-800',
  Region: 'bg-yellow-100 text-yellow-800',
  Country: 'bg-teal-100 text-teal-800',
  FundingStage: 'bg-gray-100 text-gray-800',
}

export default function PathFinder() {
  const [searchParams] = useSearchParams()
  const initialQ = searchParams.get('q') ?? ''

  const [searchQuery, setSearchQuery] = useState(initialQ)
  const [fromEntity, setFromEntity] = useState('')
  const [toEntity, setToEntity] = useState('')
  const [doSearch, setDoSearch] = useState(!!initialQ)
  const [doPath, setDoPath] = useState(false)

  const { data: searchResults, isLoading: searchLoading } = useQuery({
    queryKey: ['search', searchQuery],
    queryFn: () => fetchSearch(searchQuery),
    enabled: doSearch && searchQuery.length > 0,
  })

  const { data: pathResult, isLoading: pathLoading } = useQuery({
    queryKey: ['path', fromEntity, toEntity],
    queryFn: () => fetchShortestPath(fromEntity, toEntity),
    enabled: doPath && !!fromEntity && !!toEntity,
  })

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setDoSearch(true)
  }

  const handleFindPath = () => {
    if (fromEntity && toEntity) setDoPath(true)
  }

  const entityLink = (type: string, name: string, id?: string) => {
    switch (type) {
      case 'Startup': return `/startup/${id ?? name}`
      case 'Investor': return `/investors/${encodeURIComponent(name)}`
      case 'City': return `/cities/${encodeURIComponent(name)}`
      case 'Industry': return `/industry/${encodeURIComponent(name)}`
      default: return '#'
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Search & Path Finder</h1>

      {/* Search */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-lg font-semibold mb-4">Global Search</h2>
        <form onSubmit={handleSearch} className="flex gap-2">
          <input
            type="text"
            placeholder="Search startups, investors, founders, cities..."
            value={searchQuery}
            onChange={(e) => { setSearchQuery(e.target.value); setDoSearch(false) }}
            className="flex-1 border border-gray-300 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <button type="submit" className="bg-indigo-600 text-white px-6 py-2 rounded-lg text-sm hover:bg-indigo-700">
            Search
          </button>
        </form>

        {searchLoading && <Loading />}
        {searchResults && (
          <div className="mt-4 space-y-1">
            {searchResults.length === 0 ? (
              <p className="text-sm text-gray-500">No results found</p>
            ) : (
              searchResults.map((r, i) => (
                <Link
                  key={i}
                  to={entityLink(r.type, r.name, r.id)}
                  className="flex items-center gap-3 p-2 hover:bg-gray-50 rounded"
                >
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${TYPE_COLORS[r.type] ?? 'bg-gray-100'}`}>
                    {r.type}
                  </span>
                  <span className="text-sm">{r.name}</span>
                  <span className="text-xs text-gray-400 ml-auto">
                    score: {r.score?.toFixed(1)}
                  </span>
                </Link>
              ))
            )}
          </div>
        )}
      </div>

      {/* Path Finder */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-lg font-semibold mb-4">Shortest Path Finder</h2>
        <p className="text-sm text-gray-500 mb-4">
          Find the shortest connection between any two entities in the graph
        </p>
        <div className="flex gap-2 items-center">
          <input
            type="text"
            placeholder="From (name or ID)"
            value={fromEntity}
            onChange={(e) => { setFromEntity(e.target.value); setDoPath(false) }}
            className="flex-1 border border-gray-300 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <span className="text-gray-400">to</span>
          <input
            type="text"
            placeholder="To (name or ID)"
            value={toEntity}
            onChange={(e) => { setToEntity(e.target.value); setDoPath(false) }}
            className="flex-1 border border-gray-300 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <button
            onClick={handleFindPath}
            className="bg-indigo-600 text-white px-6 py-2 rounded-lg text-sm hover:bg-indigo-700"
          >
            Find Path
          </button>
        </div>

        {pathLoading && <Loading />}

        {pathResult && !pathResult.error && (
          <div className="mt-6">
            <p className="text-sm text-gray-500 mb-3">
              Path length: {pathResult.path_length} hops
            </p>
            <div className="flex items-center gap-2 flex-wrap">
              {pathResult.path_nodes?.map((node: any, i: number) => (
                <div key={i} className="flex items-center gap-2">
                  <Link
                    to={entityLink(node.type, node.name, node.id)}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium ${TYPE_COLORS[node.type] ?? 'bg-gray-100'}`}
                  >
                    {node.name}
                    <span className="text-xs opacity-60 ml-1">({node.type})</span>
                  </Link>
                  {i < (pathResult.path_nodes?.length ?? 0) - 1 && (
                    <span className="text-gray-400 text-xs">
                      —{pathResult.rel_types?.[i]}—&gt;
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {pathResult?.error && (
          <p className="mt-4 text-sm text-red-500">{pathResult.error}</p>
        )}
      </div>
    </div>
  )
}
