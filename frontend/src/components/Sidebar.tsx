import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Monitor,
  Activity,
  Bell,
  FileText,
  Users,
  BarChart3,
  Network,
  Settings,
  User,
  Siren,
  CalendarClock,
} from 'lucide-react'
import { useAuth } from '../contexts/auth-context-value'

const links = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/devices', icon: Monitor, label: 'Devices' },
  { to: '/traffic', icon: Activity, label: 'Traffic' },
  { to: '/alerts', icon: Bell, label: 'Alerts' },
  { to: '/incidents', icon: Siren, label: 'Incidents' },
  { to: '/maintenance', icon: CalendarClock, label: 'Maintenance' },
  { to: '/reports', icon: FileText, label: 'Reports' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/topology', icon: Network, label: 'Topology' },
  { to: '/users', icon: Users, label: 'Users', adminOnly: true },
  { to: '/settings', icon: Settings, label: 'Settings' },
  { to: '/profile', icon: User, label: 'Profile' },
]

export function Sidebar() {
  const { isAdmin } = useAuth()
  return (
    <aside className="w-64 min-h-screen border-r border-[var(--border)] bg-[var(--bg-secondary)] p-4 flex flex-col">
      <div className="mb-8 px-2">
        <h1 className="text-lg font-bold text-cyan-400">SNMADMDCP</h1>
        <p className="text-xs text-[var(--text-secondary)]">Network Monitoring</p>
      </div>
      <nav className="flex-1 space-y-1">
        {links
          .filter((l) => !l.adminOnly || isAdmin)
          .map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg transition ${
                  isActive ? 'bg-cyan-600/20 text-cyan-400' : 'text-[var(--text-secondary)] hover:bg-[var(--bg-card)]'
                }`
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
      </nav>
    </aside>
  )
}
