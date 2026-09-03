import { LogOut, Moon, Sun } from 'lucide-react'
import { useAuth } from '../contexts/auth-context-value'
import { useTheme } from '../contexts/theme-context-value'
import { useNavigate } from 'react-router-dom'

export function Navbar() {
  const { user, logout } = useAuth()
  const { theme, toggle } = useTheme()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <header className="h-14 border-b border-[var(--border)] flex items-center justify-between px-6 bg-[var(--bg-secondary)]">
      <span className="text-sm text-[var(--text-secondary)]">
        Welcome, <strong className="text-[var(--text-primary)]">{user?.username}</strong>
        <span className="ml-2 px-2 py-0.5 rounded text-xs bg-cyan-600/20 text-cyan-400">{user?.role}</span>
      </span>
      <div className="flex items-center gap-3">
        <button type="button" onClick={toggle} className="p-2 rounded hover:bg-[var(--bg-card)]" aria-label="Toggle theme">
          {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </button>
        <button
          type="button"
          onClick={handleLogout}
          className="flex items-center gap-2 px-3 py-1.5 rounded text-sm hover:bg-red-600/20 text-red-400"
        >
          <LogOut size={16} /> Logout
        </button>
      </div>
    </header>
  )
}
