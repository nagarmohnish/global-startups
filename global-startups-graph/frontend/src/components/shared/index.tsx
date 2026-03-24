import Link from 'next/link'

export function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-sm transition-shadow">
      <p className="text-sm text-gray-500 mb-1">{label}</p>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  )
}

export function Loading() {
  return (
    <div className="flex items-center justify-center py-16">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-600" />
    </div>
  )
}

export function Badge({ children, color = 'gray' }: { children: React.ReactNode; color?: string }) {
  const colors: Record<string, string> = {
    gray: 'bg-gray-100 text-gray-700',
    blue: 'bg-blue-50 text-blue-700',
    green: 'bg-green-50 text-green-700',
    purple: 'bg-purple-50 text-purple-700',
    amber: 'bg-amber-50 text-amber-700',
    pink: 'bg-pink-50 text-pink-700',
    indigo: 'bg-brand-50 text-brand-700',
  }
  return <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${colors[color] || colors.gray}`}>{children}</span>
}

const TYPE_COLORS: Record<string, string> = {
  Startup: 'indigo', Investor: 'green', Founder: 'purple',
  City: 'amber', Industry: 'pink', Region: 'blue',
}

export function EntityBadge({ type }: { type: string }) {
  return <Badge color={TYPE_COLORS[type] || 'gray'}>{type}</Badge>
}

export function EntityLink({ type, name, id }: { type: string; name: string; id?: string }) {
  const href = type === 'Startup' ? `/startup/${id || name}`
    : type === 'Investor' ? `/investor/${encodeURIComponent(name)}`
    : type === 'City' ? `/city/${encodeURIComponent(name)}`
    : type === 'Industry' ? `/industry/${encodeURIComponent(name)}`
    : '#'
  return (
    <Link href={href} className="text-brand-600 hover:text-brand-700 hover:underline font-medium">
      {name}
    </Link>
  )
}

export function SectionHeader({ children }: { children: React.ReactNode }) {
  return <h2 className="text-lg font-semibold text-gray-900">{children}</h2>
}

export function Card({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return <div className={`bg-white rounded-xl border border-gray-200 p-6 ${className}`}>{children}</div>
}
