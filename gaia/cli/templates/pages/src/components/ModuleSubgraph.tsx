import { useMemo, useRef, useCallback } from 'react'
import { useElkLayout } from '../hooks/useElkLayout'
import { filterNodesByModule, filterEdgesForModule, getExternalRefs } from '../hooks/useGraphData'
import { useChainHighlight } from '../hooks/useChainHighlight'
import NodeRenderer from './NodeRenderer'
import EdgeRenderer from './EdgeRenderer'
import DetailPanel from './DetailPanel'
import type { GraphNode, GraphEdge } from '../types'

interface Props {
  moduleId: string
  allNodes: GraphNode[]
  allEdges: GraphEdge[]
  onBack: () => void
  onNavigateToModule: (moduleId: string, nodeId: string) => void
}

export default function ModuleSubgraph({
  moduleId, allNodes, allEdges, onBack, onNavigateToModule,
}: Props) {
  const svgRef = useRef<SVGSVGElement>(null)

  const { moduleNodes, moduleEdges, externalRefs } = useMemo(() => {
    const mNodes = filterNodesByModule(allNodes, moduleId)
    const mNodeIds = new Set(mNodes.map(n => n.id))
    const mEdges = filterEdgesForModule(allEdges, mNodeIds)
    const refs = getExternalRefs(mEdges, mNodeIds, allNodes)
    const extNodes: GraphNode[] = refs.map(r => ({
      id: r.id,
      label: `↗ ${r.label}`,
      type: 'setting' as const,
      module: r.sourceModule,
      content: '',
      exported: false,
      metadata: { _external: true, _sourceModule: r.sourceModule },
    }))
    return {
      moduleNodes: [...mNodes, ...extNodes],
      moduleEdges: mEdges,
      externalRefs: refs,
    }
  }, [allNodes, allEdges, moduleId])

  const layout = useElkLayout(moduleNodes, moduleEdges)
  const { highlightedIds, selectedNodeId, selectNode, clearSelection } = useChainHighlight(allEdges)

  const nodesById = useMemo(() => {
    const m = new Map<string, GraphNode>()
    for (const n of allNodes) m.set(n.id, n)
    return m
  }, [allNodes])

  const handleNodeSelect = useCallback((id: string) => {
    const ext = externalRefs.find(r => r.id === id)
    if (ext) {
      onNavigateToModule(ext.sourceModule, id)
      return
    }
    selectNode(id)
  }, [externalRefs, onNavigateToModule, selectNode])

  const selectedNode = selectedNodeId ? nodesById.get(selectedNodeId) ?? null : null

  if (!layout) {
    return <div style={{ padding: 40, textAlign: 'center', color: '#888' }}>Computing layout...</div>
  }

  const padding = 40
  const viewBox = `${-padding} ${-padding} ${layout.width + padding * 2} ${layout.height + padding * 2}`

  const edgeByKey = new Map<string, GraphEdge>()
  for (const e of moduleEdges) {
    edgeByKey.set(`${e.source}->${e.target}`, e)
  }

  return (
    <div style={{ display: 'flex', height: '100%' }}>
      <div style={{ flex: 1, overflow: 'auto', position: 'relative' }}>
        <div style={{
          padding: '8px 16px', fontSize: 13, color: '#666',
          borderBottom: '1px solid #eee', background: '#fafafa',
        }}>
          <span onClick={onBack} style={{ cursor: 'pointer', color: '#4488bb' }}>
            ← All Modules
          </span>
          {' / '}
          <strong>{moduleId}</strong>
        </div>

        <svg ref={svgRef} width="100%" viewBox={viewBox}
          style={{ minHeight: 400, maxHeight: 'calc(100vh - 120px)' }}>
          {layout.edges.map(le => {
            const ge = edgeByKey.get(`${le.source}->${le.target}`)
            const inChain = highlightedIds
              ? highlightedIds.has(le.source) && highlightedIds.has(le.target)
              : null
            return (
              <EdgeRenderer
                key={le.id}
                layoutEdge={le}
                graphEdge={ge}
                highlighted={inChain}
              />
            )
          })}
          {layout.nodes.map(ln => {
            const gn = moduleNodes.find(n => n.id === ln.id)
            if (!gn) return null
            const inChain = highlightedIds ? highlightedIds.has(ln.id) : null
            return (
              <NodeRenderer
                key={ln.id}
                node={gn}
                x={ln.x}
                y={ln.y}
                width={ln.width}
                height={ln.height}
                highlighted={inChain}
                onSelect={handleNodeSelect}
              />
            )
          })}
        </svg>
      </div>

      <DetailPanel
        node={selectedNode}
        edges={allEdges}
        nodesById={Object.fromEntries(nodesById)}
        onClose={clearSelection}
      />
    </div>
  )
}
