import type { Alert } from '../types'

const levelColors: Record<string, string> = {
  low: 'border-slate-500',
  medium: 'border-yellow-500',
  high: 'border-orange-500',
  critical: 'border-red-500',
}

export function AlertCard({ alert, onAcknowledge }: { alert: Alert; onAcknowledge?: (id: number) => void }) {
  return (
    <div className={`rounded-lg border-l-4 ${levelColors[alert.alert_level]} bg-[var(--bg-card)] p-4`}>
      <div className="flex justify-between items-start">
        <div>
          <span className="text-xs uppercase font-semibold text-[var(--text-secondary)]">{alert.alert_level}</span>
          <span className="ml-2 text-xs uppercase text-[var(--text-secondary)]">{alert.state}</span>
          <h4 className="font-medium mt-1">{alert.alert_type.replace(/_/g, ' ')}</h4>
          <p className="text-sm text-[var(--text-secondary)] mt-1">{alert.message}</p>
          {alert.device_name && <p className="text-xs mt-1 text-cyan-400">{alert.device_name}</p>}
          {alert.interface_name && <p className="text-xs mt-1 text-cyan-400">Interface: {alert.interface_name}</p>}
          {alert.occurrence_count > 1 && <p className="text-xs mt-1">Occurrences: {alert.occurrence_count}</p>}
        </div>
        {!alert.acknowledged && alert.state !== 'resolved' && onAcknowledge && (
          <button
            type="button"
            onClick={() => onAcknowledge(alert.id)}
            className="text-xs px-2 py-1 rounded bg-cyan-600 text-white hover:bg-cyan-500"
          >
            Acknowledge
          </button>
        )}
      </div>
    </div>
  )
}
