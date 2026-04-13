import { render } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import EdgeRenderer from '../components/EdgeRenderer'
import type { ElkEdge } from '../hooks/useElkLayout'

function renderInSvg(element: React.ReactElement) {
  return render(
    <svg>
      {element}
    </svg>,
  )
}

describe('EdgeRenderer offset grouping', () => {
  it('assigns distinct path geometry for different groupIndex values', () => {
    const base: ElkEdge = {
      id: 'edge-x',
      source: 'n1',
      target: 'n2',
      sections: [{
        startPoint: { x: 10, y: 20 },
        bendPoints: [ { x: 60, y: 20 }, { x: 60, y: 80 } ],
        endPoint: { x: 120, y: 80 },
      }],
    }

    const { container: c1 } = renderInSvg(
      <EdgeRenderer layoutEdge={base} graphEdge={undefined} highlighted={null} groupIndex={0} groupCount={2} expanded={false} />
    )
    const { container: c2 } = renderInSvg(
      <EdgeRenderer layoutEdge={base} graphEdge={undefined} highlighted={null} groupIndex={1} groupCount={2} expanded={false} />
    )

    const p1 = c1.querySelector('path[marker-end]')!
    const p2 = c2.querySelector('path[marker-end]')!

    expect(p1.getAttribute('d')).not.toBe(p2.getAttribute('d'))
    expect(p1.getAttribute('marker-end')).toContain('-g0')
    expect(p2.getAttribute('marker-end')).toContain('-g1')
  })

  it('separates a shared vertical terminal stem instead of leaving it collapsed', () => {
    const base: ElkEdge = {
      id: 'edge-stem',
      source: 'n1',
      target: 'n2',
      sections: [{
        startPoint: { x: 10, y: 20 },
        bendPoints: [
          { x: 60, y: 20 },
          { x: 60, y: 80 },
          { x: 120, y: 80 },
          { x: 120, y: 140 },
        ],
        endPoint: { x: 180, y: 140 },
      }],
    }

    const { container: c1 } = renderInSvg(
      <EdgeRenderer layoutEdge={base} graphEdge={undefined} highlighted={null} groupIndex={0} groupCount={2} expanded={false} />
    )
    const { container: c2 } = renderInSvg(
      <EdgeRenderer layoutEdge={base} graphEdge={undefined} highlighted={null} groupIndex={1} groupCount={2} expanded={false} />
    )

    const d1 = c1.querySelector('path[marker-end]')!.getAttribute('d')!
    const d2 = c2.querySelector('path[marker-end]')!.getAttribute('d')!
    const points1 = [...d1.matchAll(/[-\d.]+ [-\d.]+/g)].map(match => match[0].split(' ').map(Number))
    const points2 = [...d2.matchAll(/[-\d.]+ [-\d.]+/g)].map(match => match[0].split(' ').map(Number))

    expect(points1[3][0]).not.toBe(points2[3][0])
    expect(points1[4][0]).not.toBe(points2[4][0])
  })

  it('expands separation when expanded is true', () => {
    const base: ElkEdge = {
      id: 'edge-y',
      source: 'n1',
      target: 'n2',
      sections: [{ startPoint: { x: 0, y: 0 }, endPoint: { x: 100, y: 0 } }],
    }

    const { container: cA } = renderInSvg(
      <EdgeRenderer layoutEdge={base} graphEdge={undefined} highlighted={null} groupIndex={0} groupCount={3} expanded={false} />
    )
    const { container: cB } = renderInSvg(
      <EdgeRenderer layoutEdge={base} graphEdge={undefined} highlighted={null} groupIndex={0} groupCount={3} expanded={true} />
    )

    // Compare the end X coordinate embedded in the 'd'; expanded path should have different coordinates
    const dA = cA.querySelector('path[marker-end]')!.getAttribute('d')!
    const dB = cB.querySelector('path[marker-end]')!.getAttribute('d')!
    expect(dA).not.toBe(dB)
  })
})
