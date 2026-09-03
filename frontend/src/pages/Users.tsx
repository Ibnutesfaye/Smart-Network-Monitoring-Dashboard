import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import { DataTable } from '../components/DataTable'
import type { User, Paginated } from '../types'

export function Users() {
  const { data } = useQuery({
    queryKey: ['users'],
    queryFn: () => api.get<Paginated<User>>('/users/').then((r) => r.data),
  })

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">User Management</h2>
      <DataTable
        data={data?.results ?? []}
        columns={[
          { key: 'username', header: 'Username' },
          { key: 'email', header: 'Email' },
          { key: 'role', header: 'Role' },
          { key: 'created_at', header: 'Created', render: (u) => u.created_at?.slice(0, 10) ?? '-' },
        ]}
      />
    </div>
  )
}
