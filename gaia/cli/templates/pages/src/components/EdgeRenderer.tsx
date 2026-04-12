import type { ElkEdge } from '../hooks/useElkLayout'
import type { GraphEdge } from '../types'

interface Props {
  layoutEdge: ElkEdge
  graphEdge: GraphEdge | undefined
  highlighted: boolean | null
}

export default function EdgeRenderer({ layoutEdge, graphEdge, highlighted }: Props) {
  const opacity = highlighted === false ? 0.1 : 1
  const role = graphEdge?.role ?? 'premise'
  const isBackground = role === 'background'
  const stroke = isBackground ? '#999' : '#666'
  const dashArray = isBackground ? '6,4' : undefined

  const section = layoutEdge.sections?.[0]
  if (!section) return null

  const { startPoint: sp, endPoint: ep } = section
  const markerId = `arrow-${layoutEdge.id}`

  return (
    <g opacity={opacity}>
      <defs>
        <marker id={markerId} viewBox="0 0 10 10" refX="9" refY="5"
          markerWidth="6" markerHeight="6" orient="auto">
          <path d="M 0 0 L 10 5 L 0 10 z" fill={stroke} />
        </marker>
      </defs>
      <line
        x1={sp.x} y1={sp.y} x2={ep.x} y2={ep.y}
        stroke={stroke} strokeWidth={1.5}
        strokeDasharray={dashArray}
        markerEnd={`url(#${markerId})`}
      />
    </g>
  )
}
