import { useQuery } from '@tanstack/react-query'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { api } from '../api/client'
import { useWebSocket } from '../hooks/useWebSocket'
import { StatCard } from '../components/StatCard'
import { Upload, Download, Gauge } from 'lucide-react'

export function Traffic() {
  useWebSocket('/ws/dashboard/')
  const { data: summary } = useQuery({
    queryKey: ['traffic-summary'],
    queryFn: () => api.get('/traffic/summary/').then((r) => r.data),
    refetchInterval: 15000,
  })
  const { data: samples } = useQuery({
    queryKey: ['traffic'],
    queryFn: () => api.get('/traffic/', { params: { page_size: 50 } }).then((r) => r.data),
  })

  const chartData = (samples?.results ?? []).reverse().map((s: { timestamp: string; upload_speed: number; download_speed: number }) => ({
    time: s.timestamp?.slice(11, 16),
    upload: s.upload_speed,
    download: s.download_speed,
  }))

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Traffic Monitoring</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard title="Upload" value={`${summary?.current_upload?.toFixed(1) ?? 0} Mbps`} icon={Upload} />
        <StatCard title="Download" value={`${summary?.current_download?.toFixed(1) ?? 0} Mbps`} icon={Download} />
        <StatCard title="Peak Download" value={`${summary?.peak_download?.toFixed(1) ?? 0} Mbps`} icon={Gauge} />
      </div>
      <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-4">
        <h3 className="font-medium mb-4">Traffic History</h3>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={chartData}>
            <XAxis dataKey="time" />
            <YAxis />
            <Tooltip />
            <Area type="monotone" dataKey="upload" stackId="1" stroke="#06b6d4" fill="#06b6d4" fillOpacity={0.3} />
            <Area type="monotone" dataKey="download" stackId="2" stroke="#10b981" fill="#10b981" fillOpacity={0.3} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
