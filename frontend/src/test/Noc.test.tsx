import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { Dashboard } from '../pages/Dashboard'
import { Incidents } from '../pages/Incidents'
import { api } from '../api/client'

vi.mock('../hooks/useWebSocket', () => ({ useWebSocket: () => 'connected' }))
vi.mock('../api/client', () => ({ api: { get: vi.fn() } }))

function renderPage(page: React.ReactNode) {
  return render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><MemoryRouter>{page}</MemoryRouter></QueryClientProvider>)
}

describe('P2 operator workspaces', () => {
  beforeEach(() => vi.mocked(api.get).mockReset())

  it('renders server-derived NOC health and worst-site context', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: { health_score: 74, health_contributors: { down_devices: 1 }, devices: { total: 2, down: 1 }, alerts: { critical: 1 }, open_incidents: 1, active_maintenance: 0, sites_healthy: 0, sites_total: 1, last_monitoring_update: null, sites: [{ id: 1, name: 'Core', health: 60, total_devices: 2, up_devices: 1, degraded_devices: 0, down_devices: 1, critical_alerts: 1, open_incidents: 1, last_update: null }] } })
    renderPage(<Dashboard />)
    expect(await screen.findByText('NOC Command Center')).toBeInTheDocument()
    expect(screen.getByText('Core')).toBeInTheDocument()
    expect(screen.getByText('Overall health / 100')).toBeInTheDocument()
  })

  it('renders incident identifiers and assignment state', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: { results: [{ id: 7, incident_number: 'INC-2026-000007', title: 'WAN loss', priority: 'p1', severity: 'critical', status: 'investigating', site_name: 'Core', assigned_to_name: null, created_at: new Date().toISOString() }] } })
    renderPage(<Incidents />)
    expect(await screen.findByText('INC-2026-000007')).toBeInTheDocument()
    expect(screen.getByText('Unassigned')).toBeInTheDocument()
  })
})
