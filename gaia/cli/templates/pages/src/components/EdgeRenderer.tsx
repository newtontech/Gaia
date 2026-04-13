import type { ElkEdge } from '../hooks/useElkLayout'
import type { GraphEdge } from '../types'

interface Props {
  layoutEdge: ElkEdge
  graphEdge: GraphEdge | undefined
  highlighted: boolean | null
  // New props for overlapping-edge handling
  groupIndex?: number
  groupCount?: number
  expanded?: boolean
}

const OFFSET_STEP = 7
const EXPAND_MULTIPLIER = 1.6

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

function pointKey(point: { x: number; y: number }) {
  return `${point.x},${point.y}`
}

function unitNormal(start: { x: number; y: number }, end: { x: number; y: number }) {
  const dx = end.x - start.x
  const dy = end.y - start.y
  const len = Math.hypot(dx, dy) || 1
  // Rotate by +90deg to get a consistent normal
  return { nx: -dy / len, ny: dx / len }
}

function offsetPoint(p: { x: number; y: number }, nx: number, ny: number, amount: number) {
  return { x: p.x + nx * amount, y: p.y + ny * amount }
}

export default function EdgeRenderer({ layoutEdge, graphEdge, highlighted, groupIndex = 0, groupCount = 1, expanded = false }: Props) {
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

  // Compute offset amount for overlapping edges
  let amount = (groupIndex - (groupCount - 1) / 2) * OFFSET_STEP
  if (expanded) amount *= EXPAND_MULTIPLIER

  // Determine a stable normal from the last non-zero segment shared by the final path run.
  const points = [section.startPoint, ...(section.bendPoints ?? []), section.endPoint]
  const segmentStarts = points.slice(0, -1)
  const segmentEnds = points.slice(1)
  const finalStartKey = pointKey(segmentStarts[segmentStarts.length - 1] ?? section.startPoint)

  let refStart = segmentStarts[segmentStarts.length - 1] ?? section.startPoint
  let refEnd = segmentEnds[segmentEnds.length - 1] ?? section.endPoint

  for (let index = segmentStarts.length - 2; index >= 0; index -= 1) {
    if (pointKey(segmentEnds[index]) !== finalStartKey) {
      break
    }
    refStart = segmentStarts[index]
    refEnd = segmentEnds[index]
  }

  const { nx, ny } = unitNormal(refStart, refEnd)

  // Apply uniform offset to all points (no endpoint fan-out)
  const adjustedStart = offsetPoint(section.startPoint, nx, ny, amount)
  const adjustedBends = (section.bendPoints ?? []).map(bp => offsetPoint(bp, nx, ny, amount))
  const adjustedEnd = offsetPoint(section.endPoint, nx, ny, amount)

  const adjustedSection = {
    startPoint: adjustedStart,
    bendPoints: adjustedBends,
    endPoint: adjustedEnd,
  }

  const pathD = buildPathD(adjustedSection)
  const markerId = `arrow-${layoutEdge.id}-g${groupIndex}`
  const haloStart = adjustedSection.bendPoints?.at(-1) ?? adjustedSection.startPoint

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
          d={`M ${haloStart.x} ${haloStart.y} L ${adjustedSection.endPoint.x} ${adjustedSection.endPoint.y}`}
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
