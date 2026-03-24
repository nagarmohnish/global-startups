export function usd(n: number | null | undefined): string {
  if (n == null) return '--'
  if (n >= 1e9) return `$${(n / 1e9).toFixed(1)}B`
  if (n >= 1e6) return `$${(n / 1e6).toFixed(1)}M`
  if (n >= 1e3) return `$${(n / 1e3).toFixed(0)}K`
  return `$${n.toFixed(0)}`
}

export function num(n: number | null | undefined): string {
  if (n == null) return '--'
  return n.toLocaleString()
}

export function slug(name: string): string {
  return encodeURIComponent(name)
}

export const NODE_COLORS: Record<string, string> = {
  Startup: '#6366f1',
  Investor: '#10b981',
  Founder: '#8b5cf6',
  City: '#f59e0b',
  Industry: '#ec4899',
  IndustryCategory: '#ec4899',
  Region: '#ef4444',
  Country: '#0ea5e9',
  FundingStage: '#6b7280',
  FundingBracket: '#6b7280',
  FoundedCohort: '#6b7280',
}

export const NODE_SIZES: Record<string, number> = {
  Startup: 4, Investor: 6, Founder: 3, City: 10,
  Industry: 8, IndustryCategory: 8, Region: 12,
  Country: 8, FundingStage: 5, FundingBracket: 5, FoundedCohort: 5,
}
