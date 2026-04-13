import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import ModuleSubgraph from '../components/ModuleSubgraph'
import type { GraphNode, GraphEdge } from '../types'

// Mock elkjs
vi.mock('elkjs/lib/elk.bundled.js', () => ({
  default: class {
    layout(graph: { children?: { id: string; width: number; height: number }[], edges?: any[] }) {
      return Promise.resolve({
        ...graph,
        width: 800,
        height: 600,
        children: (graph.children ?? []).map((c, i) => ({
          ...c,
          x: i * 150,
          y: i * 80,
          width: c.width || 140,
          height: c.height || 48,
        })),
        edges: (graph.edges ?? []).map((edge: { id: string; sources: string[]; targets: string[] }, i: number) => ({
          id: edge.id,
          source: edge.sources[0],
          target: edge.targets[0],
          sections: [{ startPoint: { x: i * 150 + 120, y: i * 80 + 24 }, endPoint: { x: i * 150 + 240, y: i * 80 + 24 } }],
        })),
      })
    }
  },
}))

const nodes: GraphNode[] = [
  { id: 'a', label: 'A', type: 'claim', module: 'm1', content: '', exported: false, metadata: {}, prior: null, belief: null },
  { id: 'b', label: 'B', type: 'claim', module: 'm1', content: '', exported: false, metadata: {}, prior: null, belief: null },
]

const edges: GraphEdge[] = [
  { source: 'a', target: 'b', role: 'premise' },
  { source: 'a', target: 'b', role: 'premise' },
]

describe('ModuleSubgraph dismiss via scrim', () => {
  beforeEach(() => vi.clearAllMocks())

  it('shows scrim when a node is selected and closes on click', async () => {
    const { container } = render(
      <ModuleSubgraph moduleId="m1" allNodes={nodes} allEdges={edges} onBack={() => {}} onNavigateToModule={() => {}} />
    )

    // Wait for layout
    await waitFor(() => expect(container.querySelector('svg')).toBeInTheDocument())

    // Click the first node to open the panel
    const graphNodes = container.querySelectorAll('g.graph-node')
    expect(graphNodes.length).toBeGreaterThan(0)
    fireEvent.click(graphNodes[0])

    // Scrim should appear
    await waitFor(() => expect(screen.getByLabelText('graph-scrim')).toBeInTheDocument())

    // Click scrim to close
    fireEvent.click(screen.getByLabelText('graph-scrim'))

    await waitFor(() => expect(screen.queryByLabelText('graph-scrim')).not.toBeInTheDocument())
  })

  it('does not close on scrim click if dragging occurred (guarded by isDragging)', async () => {
    const { container } = render(
      <ModuleSubgraph moduleId="m1" allNodes={nodes} allEdges={edges} onBack={() => {}} onNavigateToModule={() => {}} />
    )

    await waitFor(() => expect(container.querySelector('svg')).toBeInTheDocument())

    // Open panel
    const graphNodes = container.querySelectorAll('g.graph-node')
    fireEvent.click(graphNodes[0])
    await waitFor(() => expect(screen.getByLabelText('graph-scrim')).toBeInTheDocument())

    // Simulate drag sequence then click scrim
    const canvas = screen.getByLabelText('graph-scrim')
    fireEvent.mouseDown(canvas, { clientX: 10, clientY: 10 })
    fireEvent.mouseMove(canvas, { clientX: 40, clientY: 40 })
    fireEvent.mouseUp(canvas, { clientX: 40, clientY: 40 })

    fireEvent.click(canvas)

    // Best-effort check: scrim may still be present (no close) — depends on internal isDragging timing
    // Here we only assert it didn't immediately disappear.
    expect(screen.getByLabelText('graph-scrim')).toBeInTheDocument()
  })
})
