import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import DetailPanel from '../components/DetailPanel'
import type { GraphNode } from '../types'

const baseKnowledgeNode: GraphNode = {
  id: 'node-1',
  label: 'Readable node',
  type: 'claim',
  module: 'm1',
  content: '',
  exported: false,
  metadata: {},
  prior: 0.4,
  belief: 0.7,
}

describe('DetailPanel', () => {
  it('renders structured content with body-first layout and separate metadata', () => {
    render(
      <DetailPanel
        node={{
          ...baseKnowledgeNode,
          content: [
            'QID: Q2',
            'Type: context',
            'Role: motivation',
            'Content: It is common to build systems that simplify user interactions with complex underlying data.',
            'source_ref: N/A',
          ].join('\n'),
        }}
        edges={[]}
        nodesById={{ 'node-1': baseKnowledgeNode }}
        onClose={vi.fn()}
      />,
    )

    expect(screen.getByText('It is common to build systems that simplify user interactions with complex underlying data.')).toBeInTheDocument()
    expect(screen.getByText('QID: Q2 · Type: context · Role: motivation · source_ref: N/A')).toBeInTheDocument()
  })

  it('falls back to raw content for unstructured text', () => {
    render(
      <DetailPanel
        node={{
          ...baseKnowledgeNode,
          content: 'Plain unstructured body text.',
        }}
        edges={[]}
        nodesById={{ 'node-1': baseKnowledgeNode }}
        onClose={vi.fn()}
      />,
    )

    expect(screen.getByText('Plain unstructured body text.')).toBeInTheDocument()
    expect(screen.queryByText('QID')).not.toBeInTheDocument()
  })
})
