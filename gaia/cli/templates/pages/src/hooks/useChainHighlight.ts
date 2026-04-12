import { useState, useCallback } from 'react'
import type { GraphEdge } from '../types'

export function computeUpstreamChain(nodeId: string, edges: GraphEdge[]): Set<string> {
  const reverseAdj = new Map<string, string[]>()
  for (const e of edges) {
    const sources = reverseAdj.get(e.target) ?? []
    sources.push(e.source)
    reverseAdj.set(e.target, sources)
  }

  const visited = new Set<string>()
  const queue = [nodeId]
  while (queue.length > 0) {
    const current = queue.shift()!
    if (visited.has(current)) continue
    visited.add(current)
    for (const parent of reverseAdj.get(current) ?? []) {
      if (!visited.has(parent)) queue.push(parent)
    }
  }
  return visited
}

export interface ChainHighlightState {
  highlightedIds: Set<string> | null
  selectedNodeId: string | null
  selectNode: (id: string) => void
  clearSelection: () => void
}

export function useChainHighlight(edges: GraphEdge[]): ChainHighlightState {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)
  const [highlightedIds, setHighlightedIds] = useState<Set<string> | null>(null)

  const selectNode = useCallback(
    (id: string) => {
      setSelectedNodeId(id)
      setHighlightedIds(computeUpstreamChain(id, edges))
    },
    [edges],
  )

  const clearSelection = useCallback(() => {
    setSelectedNodeId(null)
    setHighlightedIds(null)
  }, [])

  return { highlightedIds, selectedNodeId, selectNode, clearSelection }
}
