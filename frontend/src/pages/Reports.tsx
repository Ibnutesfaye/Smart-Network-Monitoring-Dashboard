import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'
import { useAuth } from '../contexts/auth-context-value'
import { Download } from 'lucide-react'

export function Reports() {
  const { isAdmin } = useAuth()
  const [reportType, setReportType] = useState('daily')
  const [format, setFormat] = useState('pdf')
  const qc = useQueryClient()

  const { data } = useQuery({
    queryKey: ['reports'],
    queryFn: () => api.get('/reports/').then((r) => r.data),
  })

  const generate = useMutation({
    mutationFn: () => api.post('/reports/generate/', { report_type: reportType, export_format: format }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['reports'] }),
  })

  const download = async (id: number) => {
    const res = await api.get(`/reports/${id}/download/`, { responseType: 'blob' })
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const a = document.createElement('a')
    a.href = url
    a.download = `report-${id}`
    a.click()
    window.URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Reports</h2>
      {isAdmin && (
        <div className="flex flex-wrap gap-3 p-4 rounded-xl border border-[var(--border)] bg-[var(--bg-card)]">
          <select value={reportType} onChange={(e) => setReportType(e.target.value)} className="px-3 py-2 rounded border border-[var(--border)] bg-[var(--bg-primary)]">
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
          </select>
          <select value={format} onChange={(e) => setFormat(e.target.value)} className="px-3 py-2 rounded border border-[var(--border)] bg-[var(--bg-primary)]">
            <option value="pdf">PDF</option>
            <option value="excel">Excel</option>
            <option value="csv">CSV</option>
          </select>
          <button type="button" onClick={() => generate.mutate()} className="px-4 py-2 rounded bg-cyan-600 hover:bg-cyan-500">
            Generate Report
          </button>
        </div>
      )}
      <div className="space-y-2">
        {(data?.results ?? []).map((r: { id: number; report_type: string; export_format: string; created_at: string; file_path: string }) => (
          <div key={r.id} className="flex justify-between items-center p-4 rounded-lg border border-[var(--border)] bg-[var(--bg-card)]">
            <div>
              <p className="font-medium capitalize">{r.report_type} Report ({r.export_format})</p>
              <p className="text-sm text-[var(--text-secondary)]">{r.created_at?.slice(0, 19)}</p>
            </div>
            {r.file_path && (
              <button type="button" onClick={() => download(r.id)} className="flex items-center gap-2 px-3 py-1.5 rounded bg-emerald-600/20 text-emerald-400">
                <Download size={16} /> Download
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
