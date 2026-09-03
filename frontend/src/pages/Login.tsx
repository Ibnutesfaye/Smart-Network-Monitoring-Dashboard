import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/auth-context-value'
import { Shield } from 'lucide-react'

export function Login() {
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('admin123')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(username, password)
      navigate('/')
    } catch {
      setError('Invalid credentials')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center grid-bg">
      <form onSubmit={handleSubmit} className="w-full max-w-md p-8 rounded-2xl border border-[var(--border)] bg-[var(--bg-card)] shadow-2xl">
        <div className="flex items-center gap-3 mb-6">
          <Shield className="h-10 w-10 text-cyan-400" />
          <div>
            <h1 className="text-xl font-bold">SNMADMDCP</h1>
            <p className="text-sm text-[var(--text-secondary)]">Network Monitoring Dashboard</p>
          </div>
        </div>
        {error && <p className="mb-4 text-sm text-red-400">{error}</p>}
        <label className="block mb-4">
          <span className="text-sm text-[var(--text-secondary)]">Username</span>
          <input
            className="mt-1 w-full px-3 py-2 rounded-lg bg-[var(--bg-primary)] border border-[var(--border)]"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
        </label>
        <label className="block mb-6">
          <span className="text-sm text-[var(--text-secondary)]">Password</span>
          <input
            type="password"
            className="mt-1 w-full px-3 py-2 rounded-lg bg-[var(--bg-primary)] border border-[var(--border)]"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        <button
          type="submit"
          disabled={loading}
          className="w-full py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 font-medium disabled:opacity-50"
        >
          {loading ? 'Signing in...' : 'Sign In'}
        </button>
        <p className="mt-4 text-xs text-center text-[var(--text-secondary)]">Demo: admin/admin123 or analyst/analyst123</p>
      </form>
    </div>
  )
}
