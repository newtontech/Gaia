import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import EdgeRenderer from '../components/EdgeRenderer'
import type { ElkEdge } from '../hooks/useElkLayout'
import type { GraphEdge } from '../types'

function renderInSvg(element: React.ReactElement) {
  return render(
    <svg>
      {element}
    </svg>,
  )
}

describe('EdgeRenderer', () => {
  it('renders stronger styling and a halo for external-connected edges', () => {
    const layoutEdge: ElkEdge = {
      id: 'edge-1',
      source: 'ext-a1',
      target: 'internal-1',
      sections: [{
        startPoint: { x: 40, y: 50 },
        bendPoints: [
          { x: 64, y: 50 },
          { x: 64, y: 100 },
          { x: 182, y: 100 },
        ],
        endPoint: { x: 200, y: 100 },
      }],
    }
    const graphEdge: GraphEdge = { source: 'ext-a1', target: 'internal-1', role: 'premise' }

    const { container } = renderInSvg(
      <EdgeRenderer layoutEdge={layoutEdge} graphEdge={graphEdge} highlighted={null} />,
    )

    const pathElement = container.querySelector('path[marker-end]')
    const markerElement = container.querySelector('marker')
    const markerPath = markerElement?.querySelector('path')

    expect(pathElement).toHaveAttribute('marker-end', expect.stringContaining('arrow-'))
    expect(pathElement).toHaveAttribute('stroke-width', '2')
    expect(markerElement).toHaveAttribute('markerWidth', '8')
    expect(markerElement).toHaveAttribute('markerHeight', '8')
    expect(markerPath).toHaveAttribute('fill', '#555')
    expect(screen.getByTestId('external-edge-halo')).toBeInTheDocument()
  })
})
