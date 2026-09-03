import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Activity, AlertTriangle, Building2, Monitor, Radio, Siren } from 'lucide-react'
import { api } from '../api/client'
import { useWebSocket } from '../hooks/useWebSocket'

type SiteHealth = { id: number; name: string; health: number; total_devices: number; up_devices: number; degraded_devices: number; down_devices: number; critical_alerts: number; open_incidents: number; last_update: string | null }
type NocSummary = { health_score: number; health_contributors: Record<string, number>; devices: Record<string, number>; alerts: Record<string, number>; open_incidents: number; active_maintenance: number; sites: SiteHealth[]; sites_healthy: number; sites_total: number; last_monitoring_update: string | null }

const tone = (value: number) => value >= 90 ? 'text-emerald-400' : value >= 70 ? 'text-amber-400' : 'text-red-400'

export function Dashboard() {
  const [events, setEvents] = useState<Array<{type:string; data:unknown}>>([])
  const socketState = useWebSocket('/ws/dashboard/', (type, eventData) => setEvents(current => [{type, data:eventData}, ...current].slice(0, 50)))
  const connected = socketState === 'connected'
  const { data, isLoading, isError } = useQuery({ queryKey: ['noc-summary'], queryFn: () => api.get<NocSummary>('/noc/summary/').then(r => r.data), refetchInterval: connected ? false : 30000 })
  const { data: traffic } = useQuery({ queryKey:['noc-traffic'], queryFn:()=>api.get('/noc/traffic/').then(r=>r.data) })
  const { data: problems } = useQuery({ queryKey:['noc-problems'], queryFn:()=>api.get('/noc/problems/').then(r=>r.data) })
  if (isLoading) return <p role="status">Loading NOC state…</p>
  if (isError || !data) return <div role="alert" className="rounded-lg border border-red-500 p-4">NOC state is unavailable. Existing monitoring continues.</div>
  const cards = [
    ['Devices', data.devices.total, Monitor], ['Down', data.devices.down, AlertTriangle], ['Critical alerts', data.alerts.critical ?? 0, Siren],
    ['Open incidents', data.open_incidents, Activity], ['Active maintenance', data.active_maintenance, Radio], ['Healthy sites', `${data.sites_healthy}/${data.sites_total}`, Building2],
  ] as const
  return <div className="space-y-5">
    <header className="flex flex-wrap items-end justify-between gap-3"><div><h2 className="text-2xl font-bold">NOC Command Center</h2><p className="text-sm text-[var(--text-secondary)]">Operational network state and investigation priorities</p></div><div className="text-right text-xs"><span className={connected ? 'text-emerald-400' : 'text-amber-400'}>{connected ? '● Live' : '○ Reconnecting'}</span><div>Last monitor update {data.last_monitoring_update ? new Date(data.last_monitoring_update).toLocaleString() : 'unavailable'}</div><Link className="text-cyan-400" to="/wallboard">Open wallboard</Link></div></header>
    <section className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-5 flex flex-wrap gap-8 items-center" aria-label="Network health score"><div><div className={`text-5xl font-bold ${tone(data.health_score)}`}>{data.health_score}</div><div className="text-sm">Overall health / 100</div></div><ul className="text-sm text-[var(--text-secondary)]">{Object.entries(data.health_contributors).filter(([,v]) => v > 0).map(([k,v]) => <li key={k}>{v} {k.replaceAll('_',' ')}</li>)}</ul></section>
    <section className="grid grid-cols-2 lg:grid-cols-6 gap-3">{cards.map(([label,value,Icon]) => <div key={label} className="rounded-lg border border-[var(--border)] bg-[var(--bg-card)] p-3"><Icon size={18} aria-hidden/><div className="text-2xl font-semibold mt-2">{value}</div><div className="text-xs text-[var(--text-secondary)]">{label}</div></div>)}</section>
    <section className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] overflow-x-auto"><div className="p-4"><h3 className="font-semibold">Site health — worst first</h3></div><table className="w-full text-sm"><thead><tr className="text-left border-y border-[var(--border)]"><th className="p-3">Site</th><th>Health</th><th>Up / Total</th><th>Degraded</th><th>Down</th><th>Critical</th><th>Incidents</th><th>Last update</th></tr></thead><tbody>{data.sites.map(s => <tr key={s.id} className="border-b border-[var(--border)]"><td className="p-3 font-medium">{s.name}</td><td className={tone(s.health)}>{s.health}</td><td>{s.up_devices} / {s.total_devices}</td><td>{s.degraded_devices}</td><td>{s.down_devices}</td><td>{s.critical_alerts}</td><td>{s.open_incidents}</td><td>{s.last_update ? new Date(s.last_update).toLocaleTimeString() : 'Unknown'}</td></tr>)}</tbody></table>{!data.sites.length && <p className="p-4 text-[var(--text-secondary)]">No authorized sites.</p>}</section>
    <section className="grid lg:grid-cols-3 gap-4"><div className="p-4 rounded-xl border border-[var(--border)] bg-[var(--bg-card)]"><h3 className="font-semibold">Traffic overview</h3><p>Inbound {traffic?.inbound_bps==null?'Unavailable':`${(traffic.inbound_bps/1e6).toFixed(2)} Mbps`}</p><p>Outbound {traffic?.outbound_bps==null?'Unavailable':`${(traffic.outbound_bps/1e6).toFixed(2)} Mbps`}</p>{(traffic?.top_interfaces??[]).slice(0,5).map((p:{id:number;device:string;name:string;in_pct:number|null;out_pct:number|null})=><p className="text-sm" key={p.id}>{p.device} / {p.name}: {Math.max(p.in_pct??0,p.out_pct??0).toFixed(1)}%</p>)}</div><div className="p-4 rounded-xl border border-[var(--border)] bg-[var(--bg-card)]"><h3 className="font-semibold">Top problem resources</h3>{(problems?.most_alerts??[]).map((p:{id:number;name:string;value:number})=><p key={p.id}><Link className="text-cyan-400" to={`/devices/${p.id}`}>{p.name}</Link>: {p.value} alerts</p>)}{!problems?.most_alerts?.length&&<p>No problem resources.</p>}</div><div className="p-4 rounded-xl border border-[var(--border)] bg-[var(--bg-card)]"><h3 className="font-semibold">Live event feed</h3>{events.map((e,index)=><p className="text-sm" key={`${e.type}-${index}`}>{e.type}</p>)}{!events.length&&<p className="text-sm">No events received this session.</p>}<p className="text-xs text-[var(--text-secondary)]">Retains up to 50 events.</p></div></section>
  </div>
}
