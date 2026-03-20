import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchTopPairs, fetchInvestorPortfolio, fetchInvestorNetwork } from '../api/client'
import Loading from './shared/Loading'
import { fmtUsd } from './shared/fmt'

export default function InvestorNetwork() {
  const { name: paramName } = useParams<{ name: string }>()
  const [selectedInvestor, setSelectedInvestor] = useState(
    paramName ? decodeURIComponent(paramName) : '',
  )
  const [inputVal, setInputVal] = useState(selectedInvestor)

  const { data: pairs, isLoading: l1 } = useQuery({
    queryKey: ['topPairs'],
    queryFn: () => fetchTopPairs(30),
  })

  const { data: portfolio, isLoading: l2 } = useQuery({
    queryKey: ['portfolio', selectedInvestor],
    queryFn: () => fetchInvestorPortfolio(selectedInvestor),
    enabled: !!selectedInvestor,
  })

  const { data: network } = useQuery({
    queryKey: ['network', selectedInvestor],
    queryFn: () => fetchInvestorNetwork(selectedInvestor),
    enabled: !!selectedInvestor,
  })

  const handleSelect = (name: string) => {
    setSelectedInvestor(name)
    setInputVal(name)
  }

  if (l1) return <Loading />

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Investor Network</h1>

      {/* Search */}
      <div className="flex gap-2">
        <input
          type="text"
          placeholder="Search investor..."
          value={inputVal}
          onChange={(e) => setInputVal(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSelect(inputVal)}
          className="border border-gray-300 rounded-lg px-4 py-2 text-sm w-80 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
        <button
          onClick={() => handleSelect(inputVal)}
          className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-indigo-700"
        >
          Search
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top co-investor pairs */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold mb-4">Top Co-Investor Pairs</h2>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {pairs?.map((p, i) => (
              <div
                key={i}
                className="flex items-center justify-between p-2 hover:bg-gray-50 rounded text-sm"
              >
                <div className="flex gap-2">
                  <button
                    onClick={() => handleSelect(p.investor_a)}
                    className="text-indigo-600 hover:underline"
                  >
                    {p.investor_a}
                  </button>
                  <span className="text-gray-400">+</span>
                  <button
                    onClick={() => handleSelect(p.investor_b)}
                    className="text-indigo-600 hover:underline"
                  >
                    {p.investor_b}
                  </button>
                </div>
                <span className="bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full text-xs">
                  {p.co_investment_count}x
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Investor portfolio */}
        {selectedInvestor && (
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-lg font-semibold mb-2">{selectedInvestor}</h2>
            {l2 ? (
              <Loading />
            ) : portfolio ? (
              <div className="space-y-4">
                <div className="grid grid-cols-3 gap-3 text-sm">
                  <div className="bg-gray-50 rounded p-3">
                    <p className="text-gray-500">Startups</p>
                    <p className="text-xl font-bold">{portfolio.startups?.length ?? 0}</p>
                  </div>
                  <div className="bg-gray-50 rounded p-3">
                    <p className="text-gray-500">Industries</p>
                    <p className="text-xl font-bold">{portfolio.industries?.length ?? 0}</p>
                  </div>
                  <div className="bg-gray-50 rounded p-3">
                    <p className="text-gray-500">Total Deployed</p>
                    <p className="text-xl font-bold">{fmtUsd(portfolio.total_deployed)}</p>
                  </div>
                </div>

                {/* Industries */}
                <div>
                  <p className="text-sm font-medium text-gray-500 mb-1">Industries</p>
                  <div className="flex flex-wrap gap-1">
                    {portfolio.industries?.map((ind: string) => (
                      <Link
                        key={ind}
                        to={`/industry/${encodeURIComponent(ind)}`}
                        className="px-2 py-0.5 bg-purple-50 text-purple-700 rounded text-xs"
                      >
                        {ind}
                      </Link>
                    ))}
                  </div>
                </div>

                {/* Co-investors */}
                {portfolio.co_investors?.length > 0 && (
                  <div>
                    <p className="text-sm font-medium text-gray-500 mb-1">Top Co-investors</p>
                    <div className="flex flex-wrap gap-1">
                      {portfolio.co_investors.map((ci: any) => (
                        <button
                          key={ci.name}
                          onClick={() => handleSelect(ci.name)}
                          className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded text-xs hover:bg-blue-100"
                        >
                          {ci.name}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Startups */}
                <div className="max-h-60 overflow-y-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-left text-gray-500 border-b">
                        <th className="p-1">Startup</th>
                        <th className="p-1">City</th>
                        <th className="p-1">Funding</th>
                      </tr>
                    </thead>
                    <tbody>
                      {portfolio.startups?.map((s: any) => (
                        <tr key={s.startup_id} className="border-b hover:bg-gray-50">
                          <td className="p-1">
                            <Link to={`/startup/${s.startup_id}`} className="text-indigo-600 hover:underline">
                              {s.name}
                            </Link>
                          </td>
                          <td className="p-1">{s.city}</td>
                          <td className="p-1">{fmtUsd(s.funding_usd)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Network */}
                {network?.nodes?.length > 0 && (
                  <div>
                    <p className="text-sm font-medium text-gray-500 mb-1">
                      Network ({network.nodes.length} connected investors)
                    </p>
                    <div className="flex flex-wrap gap-1">
                      {network.nodes.slice(0, 20).map((n: any) => (
                        <button
                          key={n.name}
                          onClick={() => handleSelect(n.name)}
                          className={`px-2 py-0.5 rounded text-xs ${
                            n.dist === 1
                              ? 'bg-green-50 text-green-700'
                              : 'bg-yellow-50 text-yellow-700'
                          }`}
                        >
                          {n.name} (hop {n.dist})
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-gray-500 text-sm">No data found for this investor</p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
