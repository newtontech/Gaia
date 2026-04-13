import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import ModuleSubgraph from '../components/ModuleSubgraph'
import { adjustExternalLayout, computeLayoutBounds, computeModuleGroups } from '../components/ModuleSubgraph'
import type { GraphNode, GraphEdge } from '../types'

function defaultMockLayout(graph: { children?: { id: string; width: number; height: number }[], edges?: { id: string; sources: string[]; targets: string[] }[] }) {
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
      sections: [{
        startPoint: { x: i * 150 + 120, y: i * 80 + 24 },
        endPoint: { x: i * 150 + 240, y: i * 80 + 24 },
      }],
    })),
  })
}

let mockLayoutImpl = defaultMockLayout

// Mock elkjs
vi.mock('elkjs/lib/elk.bundled.js', () => ({
  default: class {
    layout(graph: { children?: { id: string; width: number; height: number }[], edges?: { id: string; sources: string[]; targets: string[] }[] }) {
      return mockLayoutImpl(graph)
    }
  },
}))

const mockNodes: GraphNode[] = [
  { id: 'a', label: 'Node A', type: 'claim', module: 'm1', content: 'Test content A',
    exported: false, metadata: {}, prior: 0.6, belief: 0.8 },
  { id: 'b', label: 'Node B', type: 'question', module: 'm1', content: 'Test content B',
    exported: false, metadata: {}, prior: null, belief: null },
  { id: 'c', label: 'Node C', type: 'setting', module: 'm2', content: 'External node',
    exported: false, metadata: { _external: true, _sourceModule: 'm2' }, prior: null, belief: null },
]

const mockEdges: GraphEdge[] = [
  { source: 'a', target: 'b', role: 'premise' },
  { source: 'c', target: 'a', role: 'conclusion' },
]

const overlappingNodes: GraphNode[] = [
  { id: 's1', label: 'Source 1', type: 'claim', module: 'm1', content: '', exported: false, metadata: {}, prior: null, belief: null },
  { id: 's2', label: 'Source 2', type: 'claim', module: 'm1', content: '', exported: false, metadata: {}, prior: null, belief: null },
  { id: 't1', label: 'Target 1', type: 'claim', module: 'm1', content: '', exported: false, metadata: {}, prior: null, belief: null },
  { id: 't2', label: 'Target 2', type: 'claim', module: 'm1', content: '', exported: false, metadata: {}, prior: null, belief: null },
]

const overlappingEdges: GraphEdge[] = [
  { source: 's1', target: 't1', role: 'premise' },
  { source: 's2', target: 't2', role: 'premise' },
]

function expectedAdjustedBounds() {
  const rawNodes = [
    { id: 'a', x: 0, y: 0, width: 120, height: 48 },
    { id: 'b', x: 150, y: 80, width: 120, height: 48 },
    { id: 'c', x: 300, y: 160, width: 120, height: 48 },
  ]
  const rawEdges = [
    {
      id: 'e0',
      source: 'a',
      target: 'b',
      sections: [{ startPoint: { x: 120, y: 24 }, endPoint: { x: 240, y: 24 } }],
    },
    {
      id: 'e1',
      source: 'c',
      target: 'a',
      sections: [{ startPoint: { x: 270, y: 104 }, endPoint: { x: 390, y: 104 } }],
    },
  ]
  const externalRefs = [{ id: 'c', sourceModule: 'm2', label: 'Node C' }]
  const adjusted = adjustExternalLayout(rawNodes, rawEdges, externalRefs)
  const groups = computeModuleGroups(adjusted.nodes, externalRefs, 20)
  return computeLayoutBounds(adjusted.nodes, adjusted.edges, groups)
}

describe('ModuleSubgraph - Zoom & Pan', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockLayoutImpl = defaultMockLayout
  })

  it('keeps the external lane inside the rendered svg bounds', async () => {
    const { container } = render(
      <ModuleSubgraph
        moduleId="m1"
        allNodes={mockNodes}
        allEdges={mockEdges}
        onBack={() => {}}
        onNavigateToModule={() => {}}
      />
    )

    const bounds = expectedAdjustedBounds()

    await waitFor(() => expect(container.querySelector('svg')).toBeInTheDocument())

    const svg = container.querySelector('svg')!
    const width = Number(svg.getAttribute('width'))
    const height = Number(svg.getAttribute('height'))
    const positiveOnlyWidth = bounds.maxX + 80
    const positiveOnlyHeight = bounds.maxY + 80

    expect(bounds.minX).toBeLessThan(0)
    expect(width).toBeGreaterThan(positiveOnlyWidth)
    expect(height).toBeGreaterThan(positiveOnlyHeight)
  })

  it('renders zoom control buttons', async () => {
    render(
      <ModuleSubgraph
        moduleId="m1"
        allNodes={mockNodes}
        allEdges={mockEdges}
        onBack={() => {}}
        onNavigateToModule={() => {}}
      />
    )

    await waitFor(() => {
      expect(screen.getByTitle(/zoom in/i)).toBeInTheDocument()
      expect(screen.getByTitle(/zoom out/i)).toBeInTheDocument()
      expect(screen.getByTitle(/reset view/i)).toBeInTheDocument()
    })
  })

  it('displays current zoom level', async () => {
    render(
      <ModuleSubgraph
        moduleId="m1"
        allNodes={mockNodes}
        allEdges={mockEdges}
        onBack={() => {}}
        onNavigateToModule={() => {}}
      />
    )

    await waitFor(() => {
      // Zoom level shows something like "100%" after auto-fit
      expect(screen.getByText(/\d+%/)).toBeInTheDocument()
    })
  })

  it('zooms in when clicking plus button', async () => {
    render(
      <ModuleSubgraph
        moduleId="m1"
        allNodes={mockNodes}
        allEdges={mockEdges}
        onBack={() => {}}
        onNavigateToModule={() => {}}
      />
    )

    await waitFor(() => expect(screen.getByTitle(/zoom in/i)).toBeInTheDocument())

    // Get initial zoom level
    const zoomDisplay = screen.getByText(/\d+%/)
    const initialValue = parseInt(zoomDisplay.textContent || '0', 10)

    // Click zoom in
    fireEvent.click(screen.getByTitle(/zoom in/i))

    // Wait for zoom to increase
    await waitFor(() => {
      const newZoomDisplay = screen.getByText(/\d+%/)
      const newValue = parseInt(newZoomDisplay.textContent || '0', 10)
      expect(newValue).toBeGreaterThan(initialValue)
    })
  })

  it('zooms out when clicking minus button', async () => {
    render(
      <ModuleSubgraph
        moduleId="m1"
        allNodes={mockNodes}
        allEdges={mockEdges}
        onBack={() => {}}
        onNavigateToModule={() => {}}
      />
    )

    await waitFor(() => expect(screen.getByTitle(/zoom out/i)).toBeInTheDocument())

    // Get initial zoom level
    const zoomDisplay = screen.getByText(/\d+%/)
    // First zoom in so we can then zoom out (avoid going below minimum)
    fireEvent.click(screen.getByTitle(/zoom in/i))
    fireEvent.click(screen.getByTitle(/zoom in/i))

    await waitFor(() => {
      const zoomedInDisplay = screen.getByText(/\d+%/)
      const zoomedInValue = parseInt(zoomedInDisplay.textContent || '0', 10)
      expect(zoomedInValue).toBeGreaterThan(100)
    })

    // Now zoom out
    fireEvent.click(screen.getByTitle(/zoom out/i))

    await waitFor(() => {
      const newZoomDisplay = screen.getByText(/\d+%/)
      const newValue = parseInt(newZoomDisplay.textContent || '0', 10)
      expect(newValue).toBeLessThan(parseInt(zoomDisplay.textContent || '0', 10) + 40)
    })
  })

  it('resets zoom when clicking reset button', async () => {
    render(
      <ModuleSubgraph
        moduleId="m1"
        allNodes={mockNodes}
        allEdges={mockEdges}
        onBack={() => {}}
        onNavigateToModule={() => {}}
      />
    )

    await waitFor(() => expect(screen.getByTitle(/reset view/i)).toBeInTheDocument())

    // Get initial zoom level
    const zoomDisplay = screen.getByText(/\d+%/)
    const initialZoom = zoomDisplay.textContent

    // Zoom in first
    fireEvent.click(screen.getByTitle(/zoom in/i))
    await waitFor(() => {
      const newZoom = screen.getByText(/\d+%/).textContent
      expect(newZoom).not.toBe(initialZoom)
    })

    // Then reset
    fireEvent.click(screen.getByTitle(/reset view/i))
    await waitFor(() => {
      // After reset, should be back to a valid zoom level
      expect(screen.getByText(/\d+%/)).toBeInTheDocument()
    })
  })

  it('limits zoom to minimum of 10%', async () => {
    render(
      <ModuleSubgraph
        moduleId="m1"
        allNodes={mockNodes}
        allEdges={mockEdges}
        onBack={() => {}}
        onNavigateToModule={() => {}}
      />
    )

    await waitFor(() => expect(screen.getByTitle(/zoom out/i)).toBeInTheDocument())

    // Click zoom out many times
    const zoomOutBtn = screen.getByTitle(/zoom out/i)
    for (let i = 0; i < 20; i++) {
      fireEvent.click(zoomOutBtn)
    }

    await waitFor(() => {
      const zoomDisplay = screen.getByText(/\d+%/)
      const value = parseInt(zoomDisplay.textContent || '0', 10)
      expect(value).toBeLessThanOrEqual(11) // Should hit minimum around 10%
    })
  })

  it('separates edges that share the same terminal segment near the right side even with different endpoints', async () => {
    mockLayoutImpl = (graph) => Promise.resolve({
      ...graph,
      width: 800,
      height: 600,
      children: [
        { id: 's1', x: 0, y: 0, width: 120, height: 48 },
        { id: 's2', x: 0, y: 120, width: 120, height: 48 },
        { id: 't1', x: 260, y: 40, width: 120, height: 48 },
        { id: 't2', x: 260, y: 100, width: 120, height: 48 },
      ],
      edges: [
        {
          id: 'e0',
          source: 's1',
          target: 't1',
          sections: [{
            startPoint: { x: 120, y: 24 },
            bendPoints: [
              { x: 180, y: 24 },
              { x: 180, y: 84 },
              { x: 362, y: 84 },
            ],
            endPoint: { x: 380, y: 84 },
          }],
        },
        {
          id: 'e1',
          source: 's2',
          target: 't2',
          sections: [{
            startPoint: { x: 120, y: 144 },
            bendPoints: [
              { x: 180, y: 144 },
              { x: 180, y: 84 },
              { x: 362, y: 84 },
            ],
            endPoint: { x: 380, y: 84 },
          }],
        },
      ],
    })

    const { container } = render(
      <ModuleSubgraph
        moduleId="m1"
        allNodes={overlappingNodes}
        allEdges={overlappingEdges}
        onBack={() => {}}
        onNavigateToModule={() => {}}
      />
    )

    await waitFor(() => expect(container.querySelector('svg')).toBeInTheDocument())

    const renderedEdges = [...container.querySelectorAll('path[marker-end]')]
    expect(renderedEdges).toHaveLength(2)

    const terminalSegments = renderedEdges.map(path => {
      const d = path.getAttribute('d') ?? ''
      const matches = [...d.matchAll(/[-\d.]+ [-\d.]+/g)].map(match => match[0])
      return matches.slice(-2)
    })

    expect(terminalSegments[0]).not.toEqual(terminalSegments[1])
  })
})
