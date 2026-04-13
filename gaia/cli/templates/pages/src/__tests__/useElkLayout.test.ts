import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor, act } from '@testing-library/react'

const { layoutMock } = vi.hoisted(() => ({
  layoutMock: vi.fn(),
}))

vi.mock('elkjs/lib/elk.bundled.js', () => ({
  default: class { layout = layoutMock },
}))

import { buildElkGraph, useElkLayout } from '../hooks/useElkLayout'
import type { GraphNode, GraphEdge } from '../types'

const nodes: GraphNode[] = [
  { id: 'a', label: 'a', type: 'setting', module: 'm1', content: '', exported: false, metadata: {} },
  { id: 'strat_0', type: 'strategy', strategy_type: 'deduction', module: 'm1' },
  { id: 'b', label: 'b', type: 'claim', module: 'm1', content: '', exported: false, metadata: {} },
]

const edges: GraphEdge[] = [
  { source: 'a', target: 'strat_0', role: 'premise' },
  { source: 'strat_0', target: 'b', role: 'conclusion' },
]

beforeEach(() => {
  layoutMock.mockReset()
  layoutMock.mockResolvedValue({ children: [], edges: [], width: 0, height: 0 })
})

describe('buildElkGraph', () => {
  it('produces ELK-compatible graph with children and edges', () => {
    const elk = buildElkGraph(nodes, edges)
    expect(elk.id).toBe('root')
    expect(elk.children).toHaveLength(3)
    expect(elk.edges).toHaveLength(2)
  })

  it('assigns different dimensions by node type', () => {
    const elk = buildElkGraph(nodes, edges)
    const setting = elk.children!.find(c => c.id === 'a')!
    const strategy = elk.children!.find(c => c.id === 'strat_0')!
    expect(setting.width).toBeGreaterThan(strategy.width!)
  })
})

describe('useElkLayout', () => {
  it('clears layout when ELK rejects the current request', async () => {
    layoutMock.mockRejectedValueOnce(new Error('elk failed'))

    const { result } = renderHook(() => useElkLayout(nodes, edges))

    await waitFor(() => {
      expect(result.current).toBeNull()
    })
  })
})
