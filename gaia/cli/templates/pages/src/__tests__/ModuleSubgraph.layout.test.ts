import { describe, it, expect } from 'vitest'
import type { ExternalRef } from '../hooks/useGraphData'
import type { ElkEdge, ElkNode } from '../hooks/useElkLayout'
import {
  buildExternalModuleGroups,
  adjustExternalLayout,
  computeLayoutBounds,
  computeModuleGroups,
} from '../components/ModuleSubgraph'

const externalRefs: ExternalRef[] = [
  { id: 'ext-a1', sourceModule: 'module-a', label: 'A1' },
  { id: 'ext-b1', sourceModule: 'module-b', label: 'B1' },
  { id: 'ext-a2', sourceModule: 'module-a', label: 'A2' },
  { id: 'ext-unknown', sourceModule: '', label: 'Unknown' },
]

const rawLayoutNodes: ElkNode[] = [
  { id: 'internal-1', x: 300, y: 120, width: 120, height: 48 },
  { id: 'internal-2', x: 520, y: 180, width: 120, height: 48 },
  { id: 'ext-a1', x: 60, y: 90, width: 120, height: 48 },
  { id: 'ext-b1', x: 210, y: 220, width: 120, height: 48 },
  { id: 'ext-a2', x: 90, y: 260, width: 120, height: 48 },
  { id: 'ext-unknown', x: 260, y: 320, width: 120, height: 48 },
]

const rawLayoutEdges: ElkEdge[] = [
  {
    id: 'e0',
    source: 'ext-a1',
    target: 'internal-1',
    sections: [{ startPoint: { x: 180, y: 114 }, endPoint: { x: 300, y: 120 } }],
  },
  {
    id: 'e1',
    source: 'internal-1',
    target: 'ext-a2',
    sections: [{ startPoint: { x: 360, y: 144 }, endPoint: { x: 150, y: 284 } }],
  },
  {
    id: 'e2',
    source: 'internal-1',
    target: 'ext-b1',
    sections: [{ startPoint: { x: 360, y: 144 }, endPoint: { x: 270, y: 244 } }],
  },
  {
    id: 'e3',
    source: 'internal-1',
    target: 'internal-2',
    sections: [{ startPoint: { x: 360, y: 144 }, endPoint: { x: 520, y: 180 } }],
  },
]

function boxesOverlap(
  a: { x: number; y: number; width: number; height: number },
  b: { x: number; y: number; width: number; height: number },
): boolean {
  return a.x < b.x + b.width
    && a.x + a.width > b.x
    && a.y < b.y + b.height
    && a.y + a.height > b.y
}

function computePreferredGroupY(
  groupSourceModule: string,
  nodes: ElkNode[],
  edges: ElkEdge[],
  refs: ExternalRef[],
): number {
  const groupNodeIds = refs
    .filter(ref => (ref.sourceModule || 'External') === groupSourceModule)
    .map(ref => ref.id)
  const nodeMap = new Map(nodes.map(node => [node.id, node]))
  const connectedCenters = edges
    .filter(edge => groupNodeIds.includes(edge.source) || groupNodeIds.includes(edge.target))
    .flatMap(edge => [edge.source, edge.target])
    .filter(nodeId => !groupNodeIds.includes(nodeId) && !nodeId.startsWith('ext-'))
    .map(nodeId => nodeMap.get(nodeId))
    .filter((node): node is ElkNode => node != null)
    .map(node => node.y + node.height / 2)

  const groupNodes = groupNodeIds
    .map(nodeId => nodeMap.get(nodeId))
    .filter((node): node is ElkNode => node != null)
  const totalStackHeight = groupNodes.reduce(
    (sum, node, index) => sum + node.height + (index === 0 ? 0 : 20),
    0,
  )
  const preferredCenterY = connectedCenters.reduce((sum, center) => sum + center, 0) / connectedCenters.length

  return preferredCenterY - totalStackHeight / 2 - 20
}

describe('buildExternalModuleGroups', () => {
  it('groups external refs by normalized sourceModule in first-seen order', () => {
    expect(buildExternalModuleGroups(externalRefs)).toEqual([
      { groupKey: 'module-a', sourceModule: 'module-a', nodeIds: ['ext-a1', 'ext-a2'] },
      { groupKey: 'module-b', sourceModule: 'module-b', nodeIds: ['ext-b1'] },
      {
        groupKey: '__gaia_unnamed_external__',
        sourceModule: 'External',
        nodeIds: ['ext-unknown'],
      },
    ])
  })

  it('preserves first-seen node order within each external group', () => {
    expect(buildExternalModuleGroups(externalRefs)[0]?.nodeIds).toEqual(['ext-a1', 'ext-a2'])
  })

  it('keeps unnamed externals distinct from a real module named External', () => {
    expect(buildExternalModuleGroups([
      { id: 'ext-real', sourceModule: 'External' },
      { id: 'ext-unnamed', sourceModule: '' },
    ])).toEqual([
      { groupKey: 'External', sourceModule: 'External', nodeIds: ['ext-real'] },
      {
        groupKey: '__gaia_unnamed_external__',
        sourceModule: 'External',
        nodeIds: ['ext-unnamed'],
      },
    ])
  })
})

describe('adjustExternalLayout', () => {
  it('repositions only external nodes', () => {
    const adjusted = adjustExternalLayout(rawLayoutNodes, rawLayoutEdges, externalRefs)
    const internal = adjusted.nodes.find(n => n.id === 'internal-1')
    expect(internal).toEqual(rawLayoutNodes[0])
  })

  it('places all external module groups in a shared lane left of the full internal footprint', () => {
    const adjusted = adjustExternalLayout(rawLayoutNodes, rawLayoutEdges, externalRefs)
    const groups = computeModuleGroups(adjusted.nodes, externalRefs, 20)
    const externalNodes = adjusted.nodes.filter(node => node.id.startsWith('ext-'))
    const internalNodes = adjusted.nodes.filter(node => !node.id.startsWith('ext-'))
    const internalOnlyEdges = adjusted.edges.filter(
      edge => !edge.source.startsWith('ext-') && !edge.target.startsWith('ext-'),
    )
    const internalBounds = computeLayoutBounds(internalNodes, internalOnlyEdges, [])

    expect(new Set(groups.map(group => group.x)).size).toBe(1)
    expect(Math.max(...externalNodes.map(node => node.x + node.width))).toBeLessThan(
      internalBounds.minX,
    )
  })

  it('preserves the fixed horizontal lane gap at the rendered group-box level even when external node widths differ', () => {
    const variableWidthNodes: ElkNode[] = rawLayoutNodes.map(node => {
      if (node.id === 'ext-a1' || node.id === 'ext-a2') {
        return { ...node, width: 180 }
      }
      if (node.id === 'ext-b1') {
        return { ...node, width: 100 }
      }
      return node
    })
    const adjusted = adjustExternalLayout(variableWidthNodes, rawLayoutEdges, externalRefs)
    const groups = computeModuleGroups(adjusted.nodes, externalRefs, 20)
    const internalNodes = adjusted.nodes.filter(node => !node.id.startsWith('ext-'))
    const internalOnlyEdges = adjusted.edges.filter(
      edge => !edge.source.startsWith('ext-') && !edge.target.startsWith('ext-'),
    )
    const internalBounds = computeLayoutBounds(internalNodes, internalOnlyEdges, [])

    expect(new Set(groups.map(group => group.x)).size).toBe(1)
    for (const group of groups) {
      expect(internalBounds.minX - (group.x + group.width)).toBe(48)
    }
  })

  it('keeps the external lane left of internal-only edge geometry that protrudes beyond node bounds', () => {
    const protrudingInternalEdges: ElkEdge[] = [
      ...rawLayoutEdges.slice(0, 3),
      {
        ...rawLayoutEdges[3],
        sections: [{
          startPoint: { x: 360, y: 144 },
          bendPoints: [{ x: 240, y: 144 }],
          endPoint: { x: 520, y: 180 },
        }],
      },
    ]

    const adjusted = adjustExternalLayout(rawLayoutNodes, protrudingInternalEdges, externalRefs)
    const groups = computeModuleGroups(adjusted.nodes, externalRefs, 20)
    const externalNodes = adjusted.nodes.filter(node => node.id.startsWith('ext-'))
    const internalNodes = adjusted.nodes.filter(node => !node.id.startsWith('ext-'))
    const internalOnlyEdges = adjusted.edges.filter(
      edge => !edge.source.startsWith('ext-') && !edge.target.startsWith('ext-'),
    )
    const internalBounds = computeLayoutBounds(internalNodes, internalOnlyEdges, [])

    expect(new Set(groups.map(group => group.x)).size).toBe(1)
    expect(Math.max(...externalNodes.map(node => node.x + node.width))).toBeLessThan(
      internalBounds.minX,
    )
  })

  it('keeps module groups vertically near their connected internal targets', () => {
    const adjusted = adjustExternalLayout(rawLayoutNodes, rawLayoutEdges, externalRefs)
    const groups = computeModuleGroups(adjusted.nodes, externalRefs, 20)
    const moduleA = groups.find(group => group.sourceModule === 'module-a')!
    const moduleB = groups.find(group => group.sourceModule === 'module-b')!

    expect(moduleA.y).toBeLessThan(moduleB.y)
  })

  it('keeps the first group at its preferred Y when nothing earlier forces overlap resolution', () => {
    const adjusted = adjustExternalLayout(rawLayoutNodes, rawLayoutEdges, externalRefs)
    const groups = computeModuleGroups(adjusted.nodes, externalRefs, 20)
    const moduleA = groups.find(group => group.sourceModule === 'module-a')!

    expect(moduleA.y).toBe(computePreferredGroupY('module-a', rawLayoutNodes, rawLayoutEdges, externalRefs))
  })

  it('preserves the fixed external gap between rendered module group boxes without moving internal nodes', () => {
    const adjusted = adjustExternalLayout(rawLayoutNodes, rawLayoutEdges, externalRefs)
    const groups = computeModuleGroups(adjusted.nodes, externalRefs, 20)
    const internal = adjusted.nodes.find(node => node.id === 'internal-1')
    const realizedGap = groups[1]!.y - (groups[0]!.y + groups[0]!.height)

    expect(boxesOverlap(groups[0]!, groups[1]!)).toBe(false)
    expect(realizedGap).toBe(24)
    expect(internal).toEqual(rawLayoutNodes.find(node => node.id === 'internal-1'))
  })

  it('updates edge geometry when a moved external node is the source of an edge', () => {
    const adjusted = adjustExternalLayout(rawLayoutNodes, rawLayoutEdges, externalRefs)
    expect(adjusted.edges[0].sections?.[0].startPoint).not.toEqual(rawLayoutEdges[0].sections?.[0].startPoint)
    expect(adjusted.edges[0].sections?.[0].endPoint).toEqual(rawLayoutEdges[0].sections?.[0].endPoint)
  })

  it('moves bend points together with a moved external source node', () => {
    const bentEdges: ElkEdge[] = [
      {
        ...rawLayoutEdges[0],
        sections: [{
          startPoint: { x: 180, y: 114 },
          bendPoints: [{ x: 220, y: 114 }, { x: 220, y: 150 }],
          endPoint: { x: 300, y: 120 },
        }],
      },
      ...rawLayoutEdges.slice(1),
    ]

    const adjusted = adjustExternalLayout(rawLayoutNodes, bentEdges, externalRefs)
    expect(adjusted.edges[0].sections?.[0].bendPoints).not.toEqual(bentEdges[0].sections?.[0].bendPoints)
  })

  it('updates edge geometry when a moved external node is the target of an edge', () => {
    const adjusted = adjustExternalLayout(rawLayoutNodes, rawLayoutEdges, externalRefs)
    expect(adjusted.edges[1].sections?.[0].endPoint).not.toEqual(rawLayoutEdges[1].sections?.[0].endPoint)
    expect(adjusted.edges[1].sections?.[0].startPoint).toEqual(rawLayoutEdges[1].sections?.[0].startPoint)
  })

  it('recomputes orthogonal bend points for edges that touch external nodes', () => {
    const adjusted = adjustExternalLayout(rawLayoutNodes, rawLayoutEdges, externalRefs)
    const externalSourceEdge = adjusted.edges.find(edge => edge.id === 'e0')!
    const externalTargetEdge = adjusted.edges.find(edge => edge.id === 'e1')!

    expect(externalSourceEdge.sections?.[0].bendPoints).toHaveLength(3)
    expect(externalTargetEdge.sections?.[0].bendPoints).toHaveLength(3)
  })

  it('routes external-connected edges with orthogonal first and last segments', () => {
    const adjusted = adjustExternalLayout(rawLayoutNodes, rawLayoutEdges, externalRefs)
    const section = adjusted.edges.find(edge => edge.id === 'e0')!.sections?.[0]!
    const [firstBend, secondBend, thirdBend] = section.bendPoints!

    expect(firstBend.y).toBe(section.startPoint.y)
    expect(secondBend.x).toBe(firstBend.x)
    expect(thirdBend.y).toBe(section.endPoint.y)
  })

  it('preserves geometry for edges whose endpoints are both internal', () => {
    const adjusted = adjustExternalLayout(rawLayoutNodes, rawLayoutEdges, externalRefs)
    expect(adjusted.edges[3]).toEqual(rawLayoutEdges[3])
  })
})

describe('computeModuleGroups', () => {
  it('computes module boxes from adjusted node positions rather than raw layout positions', () => {
    const adjusted = adjustExternalLayout(rawLayoutNodes, rawLayoutEdges, externalRefs)
    const groups = computeModuleGroups(adjusted.nodes, externalRefs, 20)
    const moduleA = groups.find(g => g.sourceModule === 'module-a')!
    const adjustedA1 = adjusted.nodes.find(node => node.id === 'ext-a1')!
    const adjustedA2 = adjusted.nodes.find(node => node.id === 'ext-a2')!

    expect(moduleA.x).toBe(Math.min(adjustedA1.x, adjustedA2.x) - 20)
    expect(moduleA.y).toBe(Math.min(adjustedA1.y, adjustedA2.y) - 20)
    expect(moduleA.width).toBeGreaterThan(120)
  })
})
