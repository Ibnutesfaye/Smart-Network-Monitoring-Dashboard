import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '../api/client'

type Incident = { id:number; incident_number:string; title:string; priority:string; severity:string; status:string; site_name:string|null; assigned_to_name:string|null; created_at:string }
export function Incidents() {
  const { data, isLoading, isError } = useQuery({ queryKey:['incidents'], queryFn:()=>api.get('/incidents/?ordering=-created_at').then(r=>r.data) })
  if (isLoading) return <p role="status">Loading incidents…</p>
  if (isError) return <p role="alert">Incidents could not be loaded.</p>
  return <div className="space-y-4"><header><h2 className="text-2xl font-bold">Incident Console</h2><p className="text-sm text-[var(--text-secondary)]">Coordinate active operational problems</p></header><div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] overflow-x-auto"><table className="w-full text-sm"><thead><tr className="text-left border-b border-[var(--border)]"><th className="p-3">Incident</th><th>Title</th><th>Priority</th><th>Severity</th><th>Status</th><th>Site</th><th>Assigned</th><th>Created</th></tr></thead><tbody>{(data?.results ?? []).map((i:Incident)=><tr key={i.id} className="border-b border-[var(--border)]"><td className="p-3"><Link className="text-cyan-400" to={`/incidents/${i.id}`}>{i.incident_number}</Link></td><td>{i.title}</td><td className="uppercase">{i.priority}</td><td className="uppercase">{i.severity}</td><td>{i.status}</td><td>{i.site_name ?? 'Global'}</td><td>{i.assigned_to_name ?? 'Unassigned'}</td><td>{i.created_at.slice(0,10)}</td></tr>)}</tbody></table>{!data?.results?.length&&<p className="p-4">No incidents.</p>}</div></div>
}
