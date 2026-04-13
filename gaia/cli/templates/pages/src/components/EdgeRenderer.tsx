import type { ElkEdge } from '../hooks/useElkLayout'
import type { GraphEdge } from '../types'

interface Props {
  layoutEdge: ElkEdge
  graphEdge: GraphEdge | undefined
  highlighted: boolean | null
}

function buildPathD(section: NonNullable<ElkEdge['sections']>[number]): string {
  const points = [
    section.startPoint,
    ...(section.bendPoints ?? []),
    section.endPoint,
  ]

  return points
    .map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`)
    .join(' ')
}

export default function EdgeRenderer({ layoutEdge, graphEdge, highlighted }: Props) {
  const opacity = highlighted === false ? 0.1 : 1
  const role = graphEdge?.role ?? 'premise'
  const isBackground = role === 'background'
  const hasExternalEndpoint = layoutEdge.source.startsWith('ext-') || layoutEdge.target.startsWith('ext-')
  const stroke = hasExternalEndpoint ? '#555' : isBackground ? '#999' : '#666'
  const dashArray = isBackground ? '6,4' : undefined
  const strokeWidth = hasExternalEndpoint ? 2 : 1.5
  const markerWidth = hasExternalEndpoint ? 8 : 6
  const markerHeight = hasExternalEndpoint ? 8 : 6

  const section = layoutEdge.sections?.[0]
  if (!section) return null

  const pathD = buildPathD(section)
  const markerId = `arrow-${layoutEdge.id}`
  const haloStart = section.bendPoints?.at(-1) ?? section.startPoint

  return (
    <g opacity={opacity}>
      <defs>
        <marker id={markerId} viewBox="0 0 10 10" refX="9" refY="5"
          markerWidth={markerWidth} markerHeight={markerHeight} orient="auto">
          <path d="M 0 0 L 10 5 L 0 10 z" fill={stroke} />
        </marker>
      </defs>
      {hasExternalEndpoint && (
        <path
          data-testid="external-edge-halo"
          d={`M ${haloStart.x} ${haloStart.y} L ${section.endPoint.x} ${section.endPoint.y}`}
          stroke="#fff"
          strokeWidth={6}
          fill="none"
          strokeLinecap="round"
        />
      )}
      <path
        d={pathD}
        fill="none"
        stroke={stroke}
        strokeWidth={strokeWidth}
        strokeDasharray={dashArray}
        markerEnd={`url(#${markerId})`}
      />
    </g>
  )
}
