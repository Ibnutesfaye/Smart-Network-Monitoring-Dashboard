import { useState } from 'react'
import { api } from '../api/client'
import { useAuth } from '../contexts/auth-context-value'

export function Profile() {
  const { user } = useAuth()
  const [oldPassword, setOldPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [message, setMessage] = useState('')

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await api.post('/auth/password-change/', { old_password: oldPassword, new_password: newPassword })
      setMessage('Password updated successfully')
      setOldPassword('')
      setNewPassword('')
    } catch {
      setMessage('Failed to update password')
    }
  }

  return (
    <div className="space-y-6 max-w-lg">
      <h2 className="text-2xl font-bold">Profile</h2>
      <div className="p-4 rounded-xl border border-[var(--border)] bg-[var(--bg-card)]">
        <p><strong>Username:</strong> {user?.username}</p>
        <p><strong>Email:</strong> {user?.email}</p>
        <p><strong>Role:</strong> {user?.role}</p>
      </div>
      <form onSubmit={handleChangePassword} className="p-4 rounded-xl border border-[var(--border)] bg-[var(--bg-card)] space-y-4">
        <h3 className="font-medium">Change Password</h3>
        {message && <p className="text-sm text-cyan-400">{message}</p>}
        <input
          type="password"
          placeholder="Current password"
          value={oldPassword}
          onChange={(e) => setOldPassword(e.target.value)}
          className="w-full px-3 py-2 rounded border border-[var(--border)] bg-[var(--bg-primary)]"
        />
        <input
          type="password"
          placeholder="New password"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          className="w-full px-3 py-2 rounded border border-[var(--border)] bg-[var(--bg-primary)]"
        />
        <button type="submit" className="px-4 py-2 rounded bg-cyan-600 hover:bg-cyan-500">Update Password</button>
      </form>
    </div>
  )
}
