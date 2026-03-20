const BASE = '/api'

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

// Industry
export const fetchIndustryByRegion = () => get<Record<string, Record<string, number>>>('/industries/by-region')
export const fetchIndustryRanking = (limit = 10) => get<any[]>(`/industries/ranking?limit=${limit}`)
export const fetchIndustryPerformance = (name: string) => get<any>(`/industries/${encodeURIComponent(name)}`)
export const fetchIndustryStartups = (name: string, limit = 50) =>
  get<any[]>(`/industries/${encodeURIComponent(name)}/startups?limit=${limit}`)

// Geographic
export const fetchCitySpecializations = () => get<Record<string, any>>('/cities/specializations')
export const fetchRegionComparison = () => get<any[]>('/regions/compare')

// Investors
export const fetchInvestorPortfolio = (name: string) => get<any>(`/investors/${encodeURIComponent(name)}`)
export const fetchInvestorNetwork = (name: string, depth = 2) =>
  get<any>(`/investors/${encodeURIComponent(name)}/network?depth=${depth}`)
export const fetchTopPairs = (limit = 20) => get<any[]>(`/investors/top-pairs?limit=${limit}`)
export const fetchInvestorsByIndustry = (industry: string) =>
  get<any[]>(`/investors/by-industry/${encodeURIComponent(industry)}`)

// Founders
export const fetchSerialFounders = () => get<any[]>('/founders/serial')

// Graph
export const fetchShortestPath = (from: string, to: string) =>
  get<any>(`/graph/shortest-path?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}`)
export const fetchSimilarStartups = (id: string, limit = 10) =>
  get<any[]>(`/startups/${id}/similar?limit=${limit}`)
export const fetchCommonInvestors = (a: string, b: string) =>
  get<any[]>(`/startups/compare?a=${a}&b=${b}`)

// Ecosystem
export const fetchEcosystem = (city: string) => get<any>(`/ecosystems/${encodeURIComponent(city)}`)

// Search
export const fetchSearch = (q: string) => get<any[]>(`/search?q=${encodeURIComponent(q)}`)
