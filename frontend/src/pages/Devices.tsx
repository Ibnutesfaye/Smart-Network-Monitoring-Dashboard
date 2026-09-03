import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { DataTable } from '../components/DataTable'
import { useAuth } from '../contexts/auth-context-value'
import { useWebSocket } from '../hooks/useWebSocket'
import type { Device, Paginated, Site } from '../types'

export function Devices() {
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [site, setSite] = useState('')
  const navigate = useNavigate()
  const { isAdmin } = useAuth()
  const qc = useQueryClient()
  useWebSocket('/ws/devices/')

  const { data } = useQuery({
    queryKey: ['devices', search, status, site],
    queryFn: () =>
      api
        .get<Paginated<Device>>('/devices/', { params: { search, status: status || undefined, site: site || undefined } })
        .then((r) => r.data),
  })
  const { data: sites } = useQuery({
    queryKey: ['sites'],
    queryFn: () => api.get<Paginated<Site>>('/sites/', { params: { active: true } }).then((r) => r.data),
  })

  const discover = useMutation({
    mutationFn: () => api.post('/devices/discover/'),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['devices'] }),
  })

  const statusBadge = (s: string) => (
    <span
      className={`px-2 py-0.5 rounded text-xs ${
        s === 'online' ? 'bg-emerald-600/20 text-emerald-400' : s === 'offline' ? 'bg-red-600/20 text-red-400' : 'bg-slate-600/20'
      }`}
    >
      {s}
    </span>
  )

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-4 items-center justify-between">
        <h2 className="text-2xl font-bold">Devices</h2>
        {isAdmin && (
          <button
            type="button"
            onClick={() => discover.mutate()}
            className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-sm"
          >
            Run Discovery
          </button>
        )}
      </div>
      <div className="flex gap-3">
        <input
          placeholder="Search..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="px-3 py-2 rounded-lg border border-[var(--border)] bg-[var(--bg-card)] flex-1 max-w-xs"
        />
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="px-3 py-2 rounded-lg border border-[var(--border)] bg-[var(--bg-card)]"
        >
          <option value="">All statuses</option>
          <option value="online">Online</option>
          <option value="offline">Offline</option>
          <option value="degraded">Degraded</option>
          <option value="maintenance">Maintenance</option>
        </select>
        <select value={site} onChange={(e) => setSite(e.target.value)} className="px-3 py-2 rounded-lg border border-[var(--border)] bg-[var(--bg-card)]">
          <option value="">All sites</option>
          {(sites?.results ?? []).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
        </select>
      </div>
      <DataTable
        data={data?.results ?? []}
        onRowClick={(d) => navigate(`/devices/${d.id}`)}
        columns={[
          { key: 'device_name', header: 'Name' },
          { key: 'ip_address', header: 'IP' },
          { key: 'vendor', header: 'Vendor' },
          { key: 'status', header: 'Status', render: (d) => statusBadge(d.status) },
          { key: 'last_seen', header: 'Last Seen', render: (d) => d.last_seen?.slice(0, 19) ?? '-' },
        ]}
      />
    </div>
  )
}
