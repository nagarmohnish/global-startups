import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchSimilarStartups, fetchSearch } from '../api/client'
import Loading from './shared/Loading'
import { fmtUsd } from './shared/fmt'

export default function StartupDetail() {
  const { id } = useParams<{ id: string }>()

  // Use search to find the startup by ID (since we don't have a direct get-by-id endpoint)
  const { data: searchResults, isLoading: l1 } = useQuery({
    queryKey: ['search', id],
    queryFn: () => fetchSearch(id ?? ''),
    enabled: !!id,
  })

  const { data: similar, isLoading: l2 } = useQuery({
    queryKey: ['similar', id],
    queryFn: () => fetchSimilarStartups(id!, 10),
    enabled: !!id,
  })

  if (l1) return <Loading />

  // We'll get startup details from similar query's context
  // For now, show what we have from search

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Link to="/" className="hover:text-indigo-600">Dashboard</Link>
        <span>/</span>
        <span className="text-gray-900 font-medium">Startup {id}</span>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h1 className="text-2xl font-bold mb-2">
          {searchResults?.[0]?.name ?? id}
        </h1>
        <p className="text-sm text-gray-500">ID: {id}</p>
      </div>

      {/* Similar startups */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-lg font-semibold mb-4">Similar Startups</h2>
        {l2 ? (
          <Loading />
        ) : similar && similar.length > 0 ? (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-gray-500">
                <th className="p-2">Name</th>
                <th className="p-2">City</th>
                <th className="p-2">Industry</th>
                <th className="p-2">Funding</th>
                <th className="p-2">Similarity Score</th>
              </tr>
            </thead>
            <tbody>
              {similar.map((s) => (
                <tr key={s.startup_id} className="border-b hover:bg-gray-50">
                  <td className="p-2">
                    <Link to={`/startup/${s.startup_id}`} className="text-indigo-600 hover:underline">
                      {s.name}
                    </Link>
                  </td>
                  <td className="p-2">{s.city}</td>
                  <td className="p-2">{s.industry}</td>
                  <td className="p-2">{fmtUsd(s.funding_usd)}</td>
                  <td className="p-2">
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-indigo-500 rounded-full"
                          style={{ width: `${Math.min(s.score * 10, 100)}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-500">{s.score}</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="text-sm text-gray-500">No similar startups found</p>
        )}
      </div>
    </div>
  )
}
