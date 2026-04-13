# External Module Lane Layout Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the module subgraph so grouped external references live in a fixed side lane with cleaner external-edge routing and more readable arrowheads.

**Architecture:** Keep ELK as the layout source for internal nodes, then run a post-layout lane-placement pass that repositions only external nodes and computes group boxes outside the internal graph footprint. External-connected edges get a deterministic orthogonal render path and stronger arrow styling, while internal-only edges keep the simpler existing behavior.

**Tech Stack:** React 18, TypeScript, Vite, Vitest, elkjs, SVG

**Spec:** `docs/specs/2026-04-13-external-module-lane-layout-design.md`

---

## Chunk 1: Side-lane layout primitives

### File responsibilities

- `gaia/cli/templates/pages/src/components/ModuleSubgraph.tsx` — owns module-subgraph grouping helpers, lane placement, group bounds, and adjusted rendered edge geometry data
- `gaia/cli/templates/pages/src/__tests__/ModuleSubgraph.layout.test.ts` — locks normalized grouping rules, stable ordering, lane placement, preferred Y alignment, overlap resolution, and geometry preservation
- `gaia/cli/templates/pages/src/hooks/useGraphData.ts` — source of `externalRefs`; read only for assumptions, no planned behavior change unless a test proves it necessary

### Task 1: Add failing tests for lane placement

**Files:**
- Modify: `gaia/cli/templates/pages/src/__tests__/ModuleSubgraph.layout.test.ts`
- Modify: `gaia/cli/templates/pages/src/components/ModuleSubgraph.tsx`

- [ ] **Step 1: Write the failing tests for side-lane layout behavior**

Extend `gaia/cli/templates/pages/src/__tests__/ModuleSubgraph.layout.test.ts` with focused tests that preserve the grouping contract from the approved spec and add the new lane assertions.

Keep or add explicit helper-level assertions for:

```ts
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
  expect(buildExternalModuleGroups(externalRefs)[0].nodeIds).toEqual(['ext-a1', 'ext-a2'])
})
```

Add lane-placement assertions such as:

```ts
it('places all external module groups in a shared lane left of the full internal footprint', () => {
  const adjusted = adjustExternalLayout(rawLayoutNodes, rawLayoutEdges, externalRefs)
  const groups = computeModuleGroups(adjusted.nodes, externalRefs, 20)
  const externals = adjusted.nodes.filter(node => node.id.startsWith('ext-'))
  const internals = adjusted.nodes.filter(node => node.id.startsWith('internal-'))
  const internalOnlyEdges = adjusted.edges.filter(edge =>
    edge.source.startsWith('internal-') && edge.target.startsWith('internal-'))
  const internalBounds = computeLayoutBounds(internals, internalOnlyEdges, [])

  expect(new Set(groups.map(group => group.x)).size).toBe(1)
  expect(Math.max(...externals.map(node => node.x + node.width))).toBeLessThan(internalBounds.minX)
})

it('keeps the external lane left of internal-only edge geometry that protrudes beyond node bounds', () => {
  const protrudingInternalEdges = [
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
  const externals = adjusted.nodes.filter(node => node.id.startsWith('ext-'))
  const internals = adjusted.nodes.filter(node => node.id.startsWith('internal-'))
  const internalOnlyEdges = adjusted.edges.filter(edge =>
    edge.source.startsWith('internal-') && edge.target.startsWith('internal-'))
  const internalBounds = computeLayoutBounds(internals, internalOnlyEdges, [])

  expect(new Set(groups.map(group => group.x)).size).toBe(1)
  expect(Math.max(...externals.map(node => node.x + node.width))).toBeLessThan(internalBounds.minX)
})

it('keeps module groups vertically near their connected internal targets', () => {
  const adjusted = adjustExternalLayout(rawLayoutNodes, rawLayoutEdges, externalRefs)
  const groups = computeModuleGroups(adjusted.nodes, externalRefs, 20)
  const moduleA = groups.find(group => group.sourceModule === 'module-a')!
  const moduleB = groups.find(group => group.sourceModule === 'module-b')!

  expect(moduleA.y).toBeLessThan(moduleB.y)
})

it('resolves lane overlap without moving internal nodes', () => {
  const adjusted = adjustExternalLayout(rawLayoutNodes, rawLayoutEdges, externalRefs)
  const groups = computeModuleGroups(adjusted.nodes, externalRefs, 20)
  const internal = adjusted.nodes.find(node => node.id === 'internal-1')

  expect(groups[1].y).toBeGreaterThanOrEqual(groups[0].y + groups[0].height)
  expect(internal).toEqual(rawLayoutNodes.find(node => node.id === 'internal-1'))
})
```

If the current helper names or outputs are insufficient for these assertions, export only the minimal additional helper surface needed for the tests.

- [ ] **Step 2: Run the targeted layout test and verify it fails for the right reason**

Run:

```bash
cd /Users/z/Kali-Server/Gaia/gaia/cli/templates/pages && npm test -- src/__tests__/ModuleSubgraph.layout.test.ts
```

Expected: FAIL because the current implementation still pushes groups downward inside the graph instead of placing them in a dedicated side lane.

- [ ] **Step 3: Implement minimal lane-placement logic in `ModuleSubgraph.tsx`**

Update `gaia/cli/templates/pages/src/components/ModuleSubgraph.tsx` to:

1. keep `buildExternalModuleGroups()` and `computeModuleGroups()` as the grouping primitives
2. change `adjustExternalLayout()` so it computes an internal-footprint bounding box from non-external nodes plus the sections of edges whose endpoints are both internal
3. define fixed lane constants such as:

```ts
const EXTERNAL_LANE_GAP = 48
const EXTERNAL_GROUP_GAP = 24
```

4. compute a shared lane X from the rendered internal footprint, for example:

```ts
const internalOnlyEdges = layoutEdges.filter(edge => !externalIds.has(edge.source) && !externalIds.has(edge.target))
const internalBounds = computeLayoutBounds(internalNodes, internalOnlyEdges, [])
const laneRight = internalBounds.minX - EXTERNAL_LANE_GAP
const laneX = laneRight - maxExternalNodeWidth
```

5. compute each group’s preferred Y from the centers of its connected internal targets, for example:

```ts
const connectedTargets = layoutEdges
  .filter(edge => group.nodeIds.includes(edge.source) || group.nodeIds.includes(edge.target))
  .map(edge => edge.source)
  .concat(layoutEdges
    .filter(edge => group.nodeIds.includes(edge.source) || group.nodeIds.includes(edge.target))
    .map(edge => edge.target))
  .filter(nodeId => !externalIds.has(nodeId))

const preferredCenterY = connectedTargets.length > 0
  ? connectedTargets
      .map(nodeId => originalNodeMap.get(nodeId))
      .filter((node): node is ElkNode => node != null)
      .reduce((sum, node) => sum + node.y + node.height / 2, 0) / connectedTargets.length
  : fallbackY
```

6. place each stacked group at `laneX` and the nearest non-overlapping Y at or below its preferred Y
7. keep internal node positions unchanged
8. keep final bounds derived from adjusted nodes, adjusted edges, and group boxes

Do not change click handling, selection logic, or node metadata.

- [ ] **Step 4: Run the targeted layout test again and confirm pass**

Run:

```bash
cd /Users/z/Kali-Server/Gaia/gaia/cli/templates/pages && npm test -- src/__tests__/ModuleSubgraph.layout.test.ts
```

Expected: PASS.

- [ ] **Step 5: Commit the lane-layout helper change**

```bash
git add \
  gaia/cli/templates/pages/src/components/ModuleSubgraph.tsx \
  gaia/cli/templates/pages/src/__tests__/ModuleSubgraph.layout.test.ts

git commit -m "refactor(viz): dock external module groups in side lane"
```

## Chunk 2: Orthogonal routing for external-connected edges

### File responsibilities

- `gaia/cli/templates/pages/src/components/ModuleSubgraph.tsx` — supplies adjusted geometry for external-connected edges if helper ownership stays there
- `gaia/cli/templates/pages/src/components/EdgeRenderer.tsx` — renders straight internal edges and orthogonal external-connected paths with separate arrow styling
- `gaia/cli/templates/pages/src/__tests__/ModuleSubgraph.layout.test.ts` — verifies geometry emitted for external-connected edges

### Task 2: Add failing tests for external-edge routing

**Files:**
- Modify: `gaia/cli/templates/pages/src/__tests__/ModuleSubgraph.layout.test.ts`
- Modify: `gaia/cli/templates/pages/src/components/ModuleSubgraph.tsx`
- Modify: `gaia/cli/templates/pages/src/components/EdgeRenderer.tsx`

- [ ] **Step 1: Write the failing tests for orthogonal external-edge geometry**

Extend `gaia/cli/templates/pages/src/__tests__/ModuleSubgraph.layout.test.ts` with tests like:

```ts
it('recomputes geometry for edges that touch external nodes', () => {
  const adjusted = adjustExternalLayout(rawLayoutNodes, rawLayoutEdges, externalRefs)
  const section = adjusted.edges.find(edge => edge.id === 'e0')!.sections![0]

  expect(section.startPoint.x).toBeLessThan(section.endPoint.x)
  expect(section.bendPoints?.length).toBeGreaterThanOrEqual(2)
})

it('preserves internal-only edge geometry', () => {
  const adjusted = adjustExternalLayout(rawLayoutNodes, rawLayoutEdges, externalRefs)

  expect(adjusted.edges.find(edge => edge.id === 'e3')).toEqual(rawLayoutEdges.find(edge => edge.id === 'e3'))
})
```

Use the current `ElkEdge` shape in the file. If `bendPoints` are not present in the existing type, add the minimal compatible typing needed to express routed sections.

- [ ] **Step 2: Run the targeted layout test and verify it fails**

Run:

```bash
cd /Users/z/Kali-Server/Gaia/gaia/cli/templates/pages && npm test -- src/__tests__/ModuleSubgraph.layout.test.ts
```

Expected: FAIL because external-connected edges are still represented as straight endpoint-shifted lines.

- [ ] **Step 3: Implement minimal orthogonal routing for external-connected edges**

In `gaia/cli/templates/pages/src/components/ModuleSubgraph.tsx`, update the edge-adjustment step so that when either endpoint is external it emits section geometry with bend points, for example:

```ts
const exitX = sp.x + 24
const entryX = ep.x - 18
const midY = ep.y

sections: [{
  startPoint: sp,
  bendPoints: [
    { x: exitX, y: sp.y },
    { x: exitX, y: midY },
    { x: entryX, y: midY },
  ],
  endPoint: ep,
}]
```

Keep internal-only edges unchanged.

If rendering becomes awkward with the current `<line>` implementation, update `gaia/cli/templates/pages/src/components/EdgeRenderer.tsx` to render a `<path>` built from `startPoint`, optional `bendPoints`, and `endPoint`.

- [ ] **Step 4: Run the targeted layout test again and confirm pass**

Run:

```bash
cd /Users/z/Kali-Server/Gaia/gaia/cli/templates/pages && npm test -- src/__tests__/ModuleSubgraph.layout.test.ts
```

Expected: PASS.

- [ ] **Step 5: Commit the orthogonal routing change**

```bash
git add \
  gaia/cli/templates/pages/src/components/ModuleSubgraph.tsx \
  gaia/cli/templates/pages/src/components/EdgeRenderer.tsx \
  gaia/cli/templates/pages/src/__tests__/ModuleSubgraph.layout.test.ts

git commit -m "feat(viz): orthogonalize external module edges"
```

## Chunk 3: Arrow readability and integration verification

### File responsibilities

- `gaia/cli/templates/pages/src/components/EdgeRenderer.tsx` — owns arrow marker sizing, stroke width, and mandatory target-end halo for external-connected edges
- `gaia/cli/templates/pages/src/__tests__/EdgeRenderer.test.tsx` — locks external-edge marker size, stronger styling, and halo rendering with exact assertions
- `gaia/cli/templates/pages/src/components/ModuleSubgraph.tsx` — final render ordering and viewBox integration

### Task 3: Add failing tests for readable external-edge rendering

**Files:**
- Modify: `gaia/cli/templates/pages/src/components/EdgeRenderer.tsx`
- Create: `gaia/cli/templates/pages/src/__tests__/EdgeRenderer.test.tsx`

- [ ] **Step 1: Write the failing rendering-level test**

Create `gaia/cli/templates/pages/src/__tests__/EdgeRenderer.test.tsx` with one focused test that renders an external-connected edge and proves the enhanced treatment is present with exact assertions.

Target assertions should include all required readability changes from the spec:

```ts
expect(pathElement).toHaveAttribute('marker-end', expect.stringContaining('arrow-'))
expect(pathElement).toHaveAttribute('stroke-width', '2')
expect(markerElement).toHaveAttribute('markerWidth', '8')
expect(markerElement).toHaveAttribute('markerHeight', '8')
expect(markerPath).toHaveAttribute('fill', '#555')
expect(screen.getByTestId('external-edge-halo')).toBeInTheDocument()
```

If there is a cleaner semantic assertion than `data-testid` for the halo, prefer that. Do not use snapshots.

- [ ] **Step 2: Run the focused test set and verify it fails**

Run:

```bash
cd /Users/z/Kali-Server/Gaia/gaia/cli/templates/pages && npm test -- src/__tests__/EdgeRenderer.test.tsx src/__tests__/ModuleSubgraph.layout.test.ts
```

Expected: FAIL because external-connected edges still use the default thin arrow treatment and do not render the required halo.

- [ ] **Step 3: Implement minimal readable arrow styling**

Update `gaia/cli/templates/pages/src/components/EdgeRenderer.tsx` to distinguish external-connected edges from internal-only edges. The minimal acceptable implementation is:

```tsx
const hasExternalEndpoint = layoutEdge.source.startsWith('ext-') || layoutEdge.target.startsWith('ext-')
const strokeWidth = hasExternalEndpoint ? 2 : 1.5
const markerWidth = hasExternalEndpoint ? 8 : 6
const markerHeight = hasExternalEndpoint ? 8 : 6
const stroke = hasExternalEndpoint ? '#555' : defaultStroke
```

Also render a subtle, mandatory halo local to the target end for external-connected edges, for example by drawing a wider white underlay path beneath the last segment of the external-connected path.

Also verify render order in `gaia/cli/templates/pages/src/components/ModuleSubgraph.tsx` remains:

1. group boxes
2. edges
3. nodes

- [ ] **Step 4: Run the focused test set and confirm pass**

Run:

```bash
cd /Users/z/Kali-Server/Gaia/gaia/cli/templates/pages && npm test -- src/__tests__/EdgeRenderer.test.tsx src/__tests__/ModuleSubgraph.layout.test.ts
```

Expected: PASS.

- [ ] **Step 5: Run the full template-pages test suite**

Run:

```bash
cd /Users/z/Kali-Server/Gaia/gaia/cli/templates/pages && npm test
```

Expected: full Vitest suite passes.

- [ ] **Step 6: Run the template-pages app for manual verification**

Run:

```bash
cd /Users/z/Kali-Server/Gaia/gaia/cli/templates/pages && npm run dev
```

Manual checks:

- open a module subgraph containing external refs from multiple modules
- confirm all external-module groups appear in the left-side lane
- confirm each group is labeled and contains the correct dashed white nodes
- confirm groups align roughly with the region of the graph they feed
- confirm lines still terminate on the specific small external nodes
- confirm arrowheads at targets are visually clearer than before
- confirm clicking an external node still navigates to the source module
- confirm internal nodes do not visibly shift because of the lane-placement pass

- [ ] **Step 7: Commit the final rendering and verification change**

```bash
git add \
  gaia/cli/templates/pages/src/components/ModuleSubgraph.tsx \
  gaia/cli/templates/pages/src/components/EdgeRenderer.tsx \
  gaia/cli/templates/pages/src/__tests__/ModuleSubgraph.layout.test.ts \
  gaia/cli/templates/pages/src/__tests__/EdgeRenderer.test.tsx

git commit -m "feat(viz): improve external edge readability"
```
