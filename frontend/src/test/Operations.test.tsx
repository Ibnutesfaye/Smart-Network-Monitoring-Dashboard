import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { api } from '../api/client'
import { Alerts } from '../pages/Alerts'
import { InterfaceDetail } from '../pages/InterfaceDetail'
import { Maintenance } from '../pages/Maintenance'
import { Topology } from '../pages/Topology'

vi.mock('../hooks/useWebSocket', () => ({ useWebSocket: () => 'connected' }))
vi.mock('../api/client', () => ({ api: { get: vi.fn(), post: vi.fn(), patch: vi.fn() } }))

function page(node: React.ReactNode, path='/') { return render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false}}})}><MemoryRouter initialEntries={[path]}><Routes><Route path="*" element={node}/></Routes></MemoryRouter></QueryClientProvider>) }

describe('P2 operational states',()=>{
  beforeEach(()=>vi.mocked(api.get).mockReset())
  it('shows the alert console empty state and filters',async()=>{vi.mocked(api.get).mockResolvedValue({data:{results:[]}});page(<Alerts/>);expect(await screen.findByText('Active Alert Console')).toBeInTheDocument();expect(screen.getByText('No alerts match the current filters.')).toBeInTheDocument();expect(screen.getByLabelText('Severity')).toBeInTheDocument()})
  it('shows topology empty state without fabricating links',async()=>{vi.mocked(api.get).mockResolvedValue({data:{nodes:[],edges:[]}});page(<Topology/>);expect(await screen.findByText('No topology resources match the current filters.')).toBeInTheDocument()})
  it('shows maintenance empty state and creation control',async()=>{vi.mocked(api.get).mockResolvedValue({data:{results:[]}});page(<Maintenance/>);expect(await screen.findByText('Maintenance Windows')).toBeInTheDocument();expect(screen.getByRole('button',{name:'Create window'})).toBeInTheDocument()})
  it('preserves unknown interface metrics',async()=>{vi.mocked(api.get).mockImplementation((url:string)=>Promise.resolve({data:String(url).startsWith('/interfaces/')?{id:4,name:'Gi0/1',if_index:1,alias:'Uplink',admin_status:'up',oper_status:'down',speed_bps:null,mtu:null,last_polled_at:null}:{results:[]}}));page(<InterfaceDetail/>,'/interfaces/4');expect(await screen.findByText('Gi0/1')).toBeInTheDocument();expect(screen.getAllByText('Unknown').length).toBeGreaterThan(0);expect(screen.getAllByText('Metric unavailable.').length).toBe(4)})
})
