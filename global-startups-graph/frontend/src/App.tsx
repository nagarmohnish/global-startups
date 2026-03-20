import { Routes, Route, Link, useLocation } from 'react-router-dom'
import { Search } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Dashboard from './components/Dashboard'
import IndustryDeepDive from './components/IndustryDeepDive'
import InvestorNetwork from './components/InvestorNetwork'
import CityEcosystem from './components/CityEcosystem'
import StartupDetail from './components/StartupDetail'
import PathFinder from './components/PathFinder'

const NAV = [
  { path: '/', label: 'Dashboard' },
  { path: '/investors', label: 'Investors' },
  { path: '/cities', label: 'Cities' },
  { path: '/path-finder', label: 'Path Finder' },
]

export default function App() {
  const location = useLocation()
  const navigate = useNavigate()
  const [searchQuery, setSearchQuery] = useState('')

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      navigate(`/path-finder?q=${encodeURIComponent(searchQuery)}`)
    }
  }

  return (
    <div className="min-h-screen">
      {/* Navbar */}
      <nav className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center gap-8">
          <Link to="/" className="text-xl font-bold text-indigo-600">
            StartupGraph
          </Link>
          <div className="flex gap-1">
            {NAV.map((n) => (
              <Link
                key={n.path}
                to={n.path}
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  location.pathname === n.path
                    ? 'bg-indigo-50 text-indigo-700'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                {n.label}
              </Link>
            ))}
          </div>
        </div>
        <form onSubmit={handleSearch} className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search startups, investors, cities..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 pr-4 py-2 border border-gray-300 rounded-lg text-sm w-72 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        </form>
      </nav>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-6 py-6">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/industry/:name" element={<IndustryDeepDive />} />
          <Route path="/investors" element={<InvestorNetwork />} />
          <Route path="/investors/:name" element={<InvestorNetwork />} />
          <Route path="/cities" element={<CityEcosystem />} />
          <Route path="/cities/:name" element={<CityEcosystem />} />
          <Route path="/startup/:id" element={<StartupDetail />} />
          <Route path="/path-finder" element={<PathFinder />} />
        </Routes>
      </main>
    </div>
  )
}
