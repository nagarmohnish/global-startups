const BASE = '/api'

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(`API ${res.status}: ${path}`)
  return res.json()
}

// Stats
export const fetchStats = () => get<GlobalStats>('/stats')

// Industries
export const fetchIndustryByRegion = () => get<Record<string, Record<string, number>>>('/industries/by-region')
export const fetchIndustryRanking = (limit = 15) => get<IndustryRanking[]>(`/industries/ranking?limit=${limit}`)
export const fetchIndustryOverview = (name: string) => get<IndustryOverview>(`/industry/${enc(name)}/overview`)
export const fetchIndustryStartups = (name: string, limit = 50) =>
  get<StartupSummary[]>(`/industries/${enc(name)}/startups?limit=${limit}`)

// Geographic
export const fetchCityProfile = (name: string) => get<CityProfile>(`/city/${enc(name)}/profile`)
export const fetchCityComparison = (cities: string[]) =>
  get<CityComparison>(`/analytics/city-comparison?cities=${cities.map(enc).join(',')}`)
export const fetchRegionComparison = () => get<RegionSummary[]>('/regions/compare')

// Startups
export const fetchStartupProfile = (id: string) => get<StartupProfile>(`/startup/${id}`)
export const fetchStartupCompetitors = (id: string) => get<Competitor[]>(`/startup/${id}/competitors`)
export const fetchSimilarStartups = (id: string) => get<SimilarStartup[]>(`/startups/${id}/similar`)
export const fetchInvestorMatch = (id: string) => get<InvestorMatchResult[]>(`/startup/${id}/investor-match`)

// Investors
export const fetchInvestorThesis = (name: string) => get<InvestorThesis>(`/investor/${enc(name)}/thesis`)
export const fetchTopPairs = (limit = 30) => get<CoPair[]>(`/investors/top-pairs?limit=${limit}`)
export const fetchInvestorsByIndustry = (ind: string) => get<any[]>(`/investors/by-industry/${enc(ind)}`)

// Founders
export const fetchSerialFounders = () => get<SerialFounder[]>('/founders/serial')

// Graph
export const fetchNeighborhood = (name: string, depth = 1) =>
  get<GraphData>(`/graph/neighborhood?name=${enc(name)}&depth=${depth}`)
export const fetchShortestPath = (from: string, to: string) =>
  get<PathResult>(`/graph/shortest-path?from=${enc(from)}&to=${enc(to)}`)

// Search
export const fetchAutocomplete = (q: string) => get<SearchResult[]>(`/autocomplete?q=${enc(q)}`)
export const fetchSearch = (q: string) => get<SearchResult[]>(`/search?q=${enc(q)}`)

function enc(s: string) { return encodeURIComponent(s) }

// Types
export interface GlobalStats {
  total_startups: number; total_funding: number; total_investors: number
  total_founders: number; total_cities: number; total_industries: number
  by_cohort: Record<string, number>
}

export interface IndustryRanking {
  industry: string; total_funding: number; avg_funding: number
  startup_count: number; median_funding: number
}

export interface StartupSummary {
  startup_id: string; name: string; city: string; country: string
  funding_usd: number | null; funding_stage: string | null
  founded_year: number | null; description: string | null; website: string | null
}

export interface StartupProfile extends StartupSummary {
  region: string; primary_industry: string; industries: string[]
  founders: { name: string }[]; investors: { name: string; funding_stage: string }[]
  competitors: { name: string; startup_id: string; score: number; industry: string; city: string }[]
  similar: { name: string; startup_id: string; score: number; city: string }[]
  team_size_category: string | null; revenue_usd: number | null
}

export interface Competitor {
  name: string; startup_id: string; score: number; industry: string; city: string
  funding_usd: number | null
}

export interface SimilarStartup {
  startup_id: string; name: string; city: string; industry: string
  funding_usd: number | null; score: number; shared_investors: number; shared_industries: number
}

export interface CityProfile {
  city: string; country: string; region: string
  startup_count: number; total_funding: number; avg_funding: number
  top_category: string; founder_count: number
  specializations: { industry: string; startup_count: number; location_quotient: number; city_share: number }[]
  top_startups: StartupSummary[]
  top_investors: { investor: string; startups: number }[]
  ecosystem_peers: { city: string; shared_investors: number; industry_similarity: number }[]
  stage_distribution: Record<string, number>
}

export interface CityComparison {
  cities: CityProfile[]
  shared_investors: { investor: string; cities: string[] }[]
}

export interface RegionSummary {
  region: string; startup_count: number; total_funding: number
  avg_funding: number; top_industry: string
}

export interface InvestorThesis {
  investor: string; portfolio_size: number; total_deployed: number
  primary_focus: string; geographic_reach: number
  industry_focus: { category: string; startup_count: number; total_funding: number }[]
  city_presence: { city: string; startup_count: number }[]
  stage_profile: { stage: string; count: number }[]
  portfolio: StartupSummary[]; co_investors: { name: string; shared: number }[]
}

export interface IndustryOverview {
  industry: string; startup_count: number; total_funding: number; avg_funding: number
  geographic: { city: string; count: number; funding: number }[]
  top_startups: StartupSummary[]; key_investors: { investor: string; startup_count: number }[]
  stage_breakdown: Record<string, number>
  sub_industries: string[]
}

export interface CoPair {
  investor_a: string; investor_b: string
  co_investment_count: number; shared_startups: string[]
}

export interface SerialFounder { founder: string; startups: string[]; cnt: number }

export interface GraphData {
  nodes: GraphNode[]; edges: GraphEdge[]
}
export interface GraphNode {
  id: string; label: string; type: string
  [key: string]: any
}
export interface GraphEdge {
  source: string; target: string; type: string
  [key: string]: any
}

export interface PathResult {
  path_nodes: { type: string; name: string; id?: string }[]
  rel_types: string[]; path_length: number
  error?: string
}

export interface SearchResult {
  id: string; name: string; type: string; score: number
}

export interface InvestorMatchResult {
  investor: string; match_score: number; industries: string[]; stages: string[]
}
