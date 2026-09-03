import { useQuery } from '@tanstack/react-query'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts'
import { api } from '../api/client'

export function Analytics() {
  const { data: growth } = useQuery({ queryKey: ['growth'], queryFn: () => api.get('/analytics/device-growth/').then((r) => r.data) })
  const { data: traffic } = useQuery({ queryKey: ['traffic-trends'], queryFn: () => api.get('/analytics/traffic-trends/').then((r) => r.data) })
  const { data: security } = useQuery({ queryKey: ['security'], queryFn: () => api.get('/analytics/security-stats/').then((r) => r.data) })

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Analytics</h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl border border-[var(--border)] bg-[var(--bg-card)]">
          <p className="text-sm text-[var(--text-secondary)]">Risk Score</p>
          <p className="text-2xl font-bold text-orange-400">{security?.risk_score ?? 0}</p>
        </div>
        <div className="p-4 rounded-xl border border-[var(--border)] bg-[var(--bg-card)]">
          <p className="text-sm text-[var(--text-secondary)]">Unknown Devices</p>
          <p className="text-2xl font-bold">{security?.unknown_devices ?? 0}</p>
        </div>
        <div className="p-4 rounded-xl border border-[var(--border)] bg-[var(--bg-card)]">
          <p className="text-sm text-[var(--text-secondary)]">Suspicious Activity</p>
          <p className="text-2xl font-bold">{security?.suspicious_activity ?? 0}</p>
        </div>
        <div className="p-4 rounded-xl border border-[var(--border)] bg-[var(--bg-card)]">
          <p className="text-sm text-[var(--text-secondary)]">Audit Events</p>
          <p className="text-2xl font-bold">{security?.audit_events ?? 0}</p>
        </div>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-4">
          <h3 className="font-medium mb-4">Device Growth</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={growth ?? []}>
              <XAxis dataKey="date" tick={{ fontSize: 10 }} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#10b981" />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-4">
          <h3 className="font-medium mb-4">Traffic Samples</h3>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={(traffic?.samples ?? []).slice(-30)}>
              <XAxis dataKey="timestamp" tick={{ fontSize: 8 }} hide />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="bandwidth_usage" stroke="#06b6d4" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
