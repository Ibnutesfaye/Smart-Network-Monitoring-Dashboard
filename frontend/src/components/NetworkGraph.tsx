import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import ForceGraph2D from 'react-force-graph-2d'

interface Node {
  id: string
  label: string
  status?: string
  type?: string
}

interface Edge {
  source: string
  target: string
}

interface Props {
  nodes: Node[]
  edges: Edge[]
  onNodeSelect?: (node: Node) => void
}

export function NetworkGraph({ nodes, edges, onNodeSelect }: Props) {
  const ref = useRef<{ centerAt: (x: number, y: number) => void; zoomToFit: (duration?: number, padding?: number) => void } | null>(null)
  const navigate = useNavigate()
  const graphData = {
    nodes: nodes.map((n) => ({ ...n, name: n.label })),
    links: edges.map((e) => ({ source: e.source, target: e.target })),
  }

  useEffect(() => {
    ref.current?.centerAt(0, 0)
  }, [nodes])

  return (
    <div className="relative h-[500px] rounded-xl border border-[var(--border)] bg-[var(--bg-card)] overflow-hidden"><button className="absolute z-10 right-3 top-3 bg-slate-800 text-white px-2 py-1 rounded" onClick={()=>ref.current?.zoomToFit(400,40)}>Fit</button>
      <ForceGraph2D
        ref={ref as never}
        graphData={graphData}
        nodeLabel="name"
        nodeColor={(n) => {
          const node = n as Node
          if (node.type === 'gateway') return '#06b6d4'
          return node.status === 'online' ? '#10b981' : node.status === 'offline' ? '#ef4444' : '#94a3b8'
        }}
        onNodeClick={(n) => {
          const node = n as Node
          if (onNodeSelect) onNodeSelect(node)
          else if (node.type !== 'gateway' && node.id !== 'gateway') navigate(`/devices/${node.id}`)
        }}
        linkColor={() => '#334155'}
        backgroundColor="transparent"
      />
    </div>
  )
}
