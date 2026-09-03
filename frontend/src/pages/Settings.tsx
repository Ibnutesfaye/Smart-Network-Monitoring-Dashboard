import { useTheme } from '../contexts/theme-context-value'

export function Settings() {
  const { theme, toggle } = useTheme()

  return (
    <div className="space-y-6 max-w-lg">
      <h2 className="text-2xl font-bold">Settings</h2>
      <div className="p-4 rounded-xl border border-[var(--border)] bg-[var(--bg-card)]">
        <h3 className="font-medium mb-2">Appearance</h3>
        <p className="text-sm text-[var(--text-secondary)] mb-4">Current theme: {theme}</p>
        <button type="button" onClick={toggle} className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500">
          Toggle Dark / Light Mode
        </button>
      </div>
      <div className="p-4 rounded-xl border border-[var(--border)] bg-[var(--bg-card)]">
        <h3 className="font-medium mb-2">Notifications</h3>
        <p className="text-sm text-[var(--text-secondary)]">Email notifications are sent for critical alerts (configured on server).</p>
      </div>
    </div>
  )
}
