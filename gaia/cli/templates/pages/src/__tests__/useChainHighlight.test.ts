import { describe, it, expect } from 'vitest'
import { computeUpstreamChain } from '../hooks/useChainHighlight'
import type { GraphEdge } from '../types'

const edges: GraphEdge[] = [
  { source: 'a', target: 'strat_0', role: 'premise' },
  { source: 'strat_0', target: 'b', role: 'conclusion' },
  { source: 'b', target: 'strat_1', role: 'premise' },
  { source: 'strat_1', target: 'c', role: 'conclusion' },
]

describe('computeUpstreamChain', () => {
  it('returns the clicked node itself when it has no premises', () => {
    const chain = computeUpstreamChain('a', edges)
    expect(chain).toEqual(new Set(['a']))
  })

  it('traces back one step from a conclusion', () => {
    const chain = computeUpstreamChain('b', edges)
    expect(chain).toEqual(new Set(['a', 'strat_0', 'b']))
  })

  it('traces back multiple steps', () => {
    const chain = computeUpstreamChain('c', edges)
    expect(chain).toEqual(new Set(['a', 'strat_0', 'b', 'strat_1', 'c']))
  })

  it('returns only the node for disconnected nodes', () => {
    const chain = computeUpstreamChain('d', edges)
    expect(chain).toEqual(new Set(['d']))
  })
})
