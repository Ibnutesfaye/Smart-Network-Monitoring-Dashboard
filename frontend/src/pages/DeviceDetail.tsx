import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { api } from '../api/client'
import type { DeviceInterface } from '../types'

export function DeviceDetail() {
  const { id } = useParams()
  const { data: device } = useQuery({
    queryKey: ['device', id],
    queryFn: () => api.get(`/devices/${id}/`).then((r) => r.data),
  })
  const { data: history } = useQuery({
    queryKey: ['device-history', id],
    queryFn: () => api.get(`/devices/${id}/history/`).then((r) => r.data),
  })
  const { data: interfaces, isLoading: interfacesLoading } = useQuery({
    queryKey: ['interfaces', id],
    queryFn: () => api.get(`/interfaces/?device=${id}`).then((r) => r.data),
  })
  const { data: telemetry } = useQuery({
    queryKey: ['device-telemetry', id, '24h'],
    queryFn: () => api.get(`/telemetry/devices/${id}/?range=24h`).then((r) => r.data),
  })
  const { data: alerts } = useQuery({ queryKey:['alerts','device',id], queryFn:()=>api.get(`/alerts/?device=${id}`).then(r=>r.data) })
  const { data: incidents } = useQuery({ queryKey:['incidents','device',id], queryFn:()=>api.get(`/incidents/?primary_device=${id}`).then(r=>r.data) })

  const chartData = (telemetry?.results ?? history?.history ?? []).map((h: { timestamp?: string; recorded_at?: string; latency_ms: number }) => ({
    time: (h.timestamp ?? h.recorded_at)?.slice(11, 16),
    latency: h.latency_ms,
  }))

  return (
    <div className="space-y-6">
      <header><h2 className="text-2xl font-bold">{device?.device_name}</h2><p className="uppercase text-sm">{device?.status} · {device?.criticality} criticality · observed {device?.last_seen?.slice(0,19)??'never'}</p></header>
      <nav aria-label="Device workspace" className="flex flex-wrap gap-3 text-cyan-400"><a href="#overview">Overview</a><a href="#interfaces">Interfaces</a><a href="#performance">Performance</a><a href="#alerts">Alerts</a><a href="#incidents">Incidents</a></nav>
      <div id="overview" className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl border border-[var(--border)] bg-[var(--bg-card)]">
          <p className="text-sm text-[var(--text-secondary)]">IP</p>
          <p className="font-mono">{device?.ip_address}</p>
        </div>
        <div className="p-4 rounded-xl border border-[var(--border)] bg-[var(--bg-card)]">
          <p className="text-sm text-[var(--text-secondary)]">Status</p>
          <p className="capitalize">{device?.status}</p>
        </div>
        <div className="p-4 rounded-xl border border-[var(--border)] bg-[var(--bg-card)]">
          <p className="text-sm text-[var(--text-secondary)]">Latency</p>
          <p>{device?.last_latency_ms ?? '-'} ms</p>
        </div>
        <div className="p-4 rounded-xl border border-[var(--border)] bg-[var(--bg-card)]">
          <p className="text-sm text-[var(--text-secondary)]">Availability</p>
          <p>{history?.availability_percent ?? 0}%</p>
        </div>
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 text-sm">{[['Hostname',device?.hostname||'Unknown'],['Vendor / Model',[device?.vendor,device?.model].filter(Boolean).join(' ')||'Unknown'],['Serial',device?.serial_number||'Unknown'],['OS',device?.operating_system||'Unknown'],['Type',device?.device_type||'Unknown'],['IPv6',device?.ipv6_address||'Unavailable'],['MAC',device?.mac_address||'Unknown'],['Packet loss',device?.current_packet_loss==null?'Unavailable':`${device.current_packet_loss}%`],['Uptime',device?.uptime_seconds==null?'Unavailable':`${device.uptime_seconds}s`],['Last checked',device?.last_checked_at?.slice(0,19)||'Never'],['First discovered',device?.first_discovered_at?.slice(0,19)||'Unknown'],['SNMP profile',device?.snmp_enabled?`${device.snmp_version} / ${device.snmp_profile}`:'Disabled']].map(([k,v])=><div className="p-3 border border-[var(--border)] rounded" key={k}><div className="text-[var(--text-secondary)]">{k}</div><div>{v}</div></div>)}</div>
      <div id="interfaces" className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-4">
        <h3 className="font-medium">SNMP monitoring</h3>
        {!device?.snmp_enabled ? <p className="text-[var(--text-secondary)]">SNMP is disabled for this device.</p> : (
          <p className="text-[var(--text-secondary)]">Version {device.snmp_version} · {device.snmp_status}{device.snmp_last_error_code ? ` · ${device.snmp_last_error_code}` : ''}</p>
        )}
      </div>
      <div id="performance" className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-4">
        <h3 className="font-medium mb-4">Interfaces</h3>
        {interfacesLoading ? <p>Loading interfaces…</p> : interfaces?.results?.length ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="text-left"><th>Name</th><th>Status</th><th>Speed</th><th>Inbound</th><th>Outbound</th></tr></thead>
              <tbody>{interfaces.results.map((item: DeviceInterface) => (
                <tr key={item.id} className="border-t border-[var(--border)]">
                  <td className="py-2"><Link className="text-cyan-400" to={`/interfaces/${item.id}`}>{item.name}</Link></td><td>{item.admin_status === 'up' && item.oper_status === 'down' ? '⚠ down' : item.oper_status}</td>
                  <td>{item.speed_bps ? `${(item.speed_bps / 1_000_000).toFixed(0)} Mbps` : 'Unknown'}</td>
                  <td>{item.utilization_in_pct == null ? '—' : `${item.utilization_in_pct.toFixed(1)}%`}</td>
                  <td>{item.utilization_out_pct == null ? '—' : `${item.utilization_out_pct.toFixed(1)}%`}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        ) : <p className="text-[var(--text-secondary)]">No interface telemetry has been collected.</p>}
      </div>
      <section id="alerts" className="rounded-xl border border-[var(--border)] p-4"><h3 className="font-semibold">Alert history</h3>{(alerts?.results??[]).map((a:{id:number;alert_level:string;state:string;message:string})=><p key={a.id}>{a.alert_level.toUpperCase()} · {a.state} · {a.message}</p>)}{!alerts?.results?.length&&<p>No alerts.</p>}</section>
      <section id="incidents" className="rounded-xl border border-[var(--border)] p-4"><h3 className="font-semibold">Incidents</h3>{(incidents?.results??[]).map((i:{id:number;incident_number:string;title:string;status:string})=><p key={i.id}><Link className="text-cyan-400" to={`/incidents/${i.id}`}>{i.incident_number}</Link> · {i.status} · {i.title}</p>)}{!incidents?.results?.length&&<p>No incidents.</p>}</section>
      <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-4">
        <h3 className="font-medium mb-4">Latency History</h3>
        {!chartData.length && <p className="text-[var(--text-secondary)]">No telemetry is available for this range.</p>}
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={chartData}>
            <XAxis dataKey="time" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="latency" stroke="#06b6d4" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
