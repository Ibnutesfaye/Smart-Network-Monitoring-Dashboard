import type { LucideIcon } from 'lucide-react'

interface Props {
  title: string
  value: string | number
  icon: LucideIcon
  accent?: string
}

export function StatCard({ title, value, icon: Icon, accent = 'text-cyan-400' }: Props) {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-5 shadow-lg">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-[var(--text-secondary)]">{title}</p>
          <p className="mt-1 text-2xl font-bold">{value}</p>
        </div>
        <Icon className={`h-10 w-10 ${accent}`} />
      </div>
    </div>
  )
}
