import { describe, it, expect } from 'vitest'
import { filterNodesByModule, getExternalRefs } from '../hooks/useGraphData'
import type { GraphNode, GraphEdge } from '../types'

const nodes: GraphNode[] = [
  { id: 'a', label: 'a', type: 'claim', module: 'm1', content: '', exported: false, metadata: {} },
  { id: 'b', label: 'b', type: 'claim', module: 'm1', content: '', exported: false, metadata: {} },
  { id: 'c', label: 'c', type: 'claim', module: 'm2', content: '', exported: false, metadata: {} },
  { id: 'd', label: 'd', type: 'claim', module: '', content: '', exported: false, metadata: {} },
  { id: 'e', label: 'e', type: 'claim', module: 'm3', content: '', exported: false, metadata: {} },
  { id: 'strat_0', type: 'strategy', strategy_type: 'deduction', module: 'm1' },
]

const edges: GraphEdge[] = [
  { source: 'a', target: 'strat_0', role: 'premise' },
  { source: 'c', target: 'strat_0', role: 'premise' },
  { source: 'strat_0', target: 'b', role: 'conclusion' },
]

describe('filterNodesByModule', () => {
  it('returns only nodes belonging to the given module', () => {
    const result = filterNodesByModule(nodes, 'm1')
    expect(result.map(n => n.id)).toEqual(['a', 'b', 'strat_0'])
  })
})

describe('getExternalRefs', () => {
  it('finds nodes referenced by edges but not in the module', () => {
    const moduleNodes = filterNodesByModule(nodes, 'm1')
    const moduleNodeIds = new Set(moduleNodes.map(n => n.id))
    const refs = getExternalRefs(edges, moduleNodeIds, nodes)
    expect(refs).toHaveLength(1)
    expect(refs[0].id).toBe('c')
    expect(refs[0].sourceModule).toBe('m2')
  })

  it('preserves first-seen external discovery order across modules and keeps empty module names empty', () => {
    const moduleNodes = filterNodesByModule(nodes, 'm1')
    const moduleNodeIds = new Set(moduleNodes.map(n => n.id))
    const refs = getExternalRefs(
      [
        { source: 'e', target: 'strat_0', role: 'premise' },
        { source: 'strat_0', target: 'd', role: 'conclusion' },
        { source: 'c', target: 'strat_0', role: 'premise' },
        { source: 'e', target: 'b', role: 'background' },
      ],
      moduleNodeIds,
      nodes,
    )

    expect(refs).toEqual([
      { id: 'e', label: 'e', sourceModule: 'm3' },
      { id: 'd', label: 'd', sourceModule: '' },
      { id: 'c', label: 'c', sourceModule: 'm2' },
    ])
  })
})
