import type { ReactNode } from 'react'

interface Column<T> {
  key: string
  header: string
  render?: (row: T) => ReactNode
}

interface Props<T> {
  columns: Column<T>[]
  data: T[]
  onRowClick?: (row: T) => void
}

export function DataTable<T extends { id?: number }>({ columns, data, onRowClick }: Props<T>) {
  return (
    <div className="overflow-x-auto rounded-xl border border-[var(--border)]">
      <table className="w-full text-sm">
        <thead className="bg-[var(--bg-secondary)]">
          <tr>
            {columns.map((c) => (
              <th key={c.key} className="px-4 py-3 text-left font-medium text-[var(--text-secondary)]">
                {c.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr
              key={(row as { id?: number }).id ?? i}
              className="border-t border-[var(--border)] hover:bg-[var(--bg-secondary)] cursor-pointer"
              onClick={() => onRowClick?.(row)}
            >
              {columns.map((c) => (
                <td key={c.key} className="px-4 py-3">
                  {c.render ? c.render(row) : String((row as Record<string, unknown>)[c.key] ?? '')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {data.length === 0 && <p className="p-8 text-center text-[var(--text-secondary)]">No data found</p>}
    </div>
  )
}
