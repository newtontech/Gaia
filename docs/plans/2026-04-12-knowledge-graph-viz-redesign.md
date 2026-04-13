# Knowledge Graph Visualization Redesign — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the flat Cytoscape graph with a two-level module-first ELK-based visualization that supports reasoning chain navigation for 50–200 node knowledge packages.

**Architecture:** Python-side `_graph_json.py` rewritten to emit strategy/operator as intermediate nodes with role-tagged edges and module metadata. React template replaced: cytoscape removed, elkjs added, SVG-based rendering with `ModuleOverview` (Level 1) and `ModuleSubgraph` (Level 2) components. Three custom hooks (`useGraphData`, `useElkLayout`, `useChainHighlight`) handle data loading, layout computation, and BFS chain tracing.

**Tech Stack:** Python 3.12, React 18, TypeScript, elkjs (WASM layout engine), Vite, vitest

**Spec:** `docs/specs/2026-04-12-knowledge-graph-viz-redesign.md`

---

## Chunk 1: Python Data Layer

### Task 1: Rewrite `generate_graph_json()` — strategy/operator as nodes

**Files:**
- Modify: `gaia/cli/commands/_graph_json.py` (full rewrite, 73 lines)
- Modify: `tests/cli/test_graph_json.py` (rewrite existing tests for new schema)

The new `generate_graph_json()` must produce:

```json
{
  "modules": [{"id": "motivation", "order": 0, "node_count": 5, "strategy_count": 0}],
  "cross_module_edges": [{"from_module": "s2_laser", "to_module": "s3_band", "count": 2}],
  "nodes": [
    {"id": "pkg::label", "type": "setting", "module": "motivation", "label": "label",
     "title": "Title", "content": "...", "prior": 0.5, "belief": 0.7, "exported": true, "metadata": {}},
    {"id": "strat_0", "type": "strategy", "strategy_type": "deduction",
     "module": "s2_laser", "reason": "A implies B"}
  ],
  "edges": [
    {"source": "pkg::premise", "target": "strat_0", "role": "premise"},
    {"source": "pkg::bg", "target": "strat_0", "role": "background"},
    {"source": "strat_0", "target": "pkg::conclusion", "role": "conclusion"}
  ]
}
```

- [ ] **Step 1: Write failing tests for new schema**

Replace the contents of `tests/cli/test_graph_json.py` with:

```python
"""Tests for graph.json generator (v2: strategy/operator as nodes)."""

from __future__ import annotations

import json

from gaia.cli.commands._graph_json import generate_graph_json


def _make_ir(
    knowledges: list[dict] | None = None,
    strategies: list[dict] | None = None,
    operators: list[dict] | None = None,
    module_order: list[str] | None = None,
) -> dict:
    """Build a minimal IR dict for testing."""
    return {
        "package_name": "test_pkg",
        "namespace": "github",
        "knowledges": knowledges or [],
        "strategies": strategies or [],
        "operators": operators or [],
        "module_order": module_order or [],
    }


def test_knowledge_nodes_emitted():
    """Knowledge nodes appear with correct fields."""
    ir = _make_ir(
        knowledges=[
            {"id": "github:test_pkg::a", "label": "a", "title": "Claim A",
             "type": "claim", "content": "Claim A.", "module": "m1",
             "metadata": {"figure": "fig.png"}},
        ],
        module_order=["m1"],
    )
    beliefs = {"beliefs": [{"knowledge_id": "github:test_pkg::a", "belief": 0.9, "label": "a"}]}
    params = {"priors": [{"knowledge_id": "github:test_pkg::a", "value": 0.7}]}
    exported = {"github:test_pkg::a"}

    data = json.loads(generate_graph_json(ir, beliefs_data=beliefs, param_data=params, exported_ids=exported))

    nodes = [n for n in data["nodes"] if n["type"] != "strategy"]
    assert len(nodes) == 1
    n = nodes[0]
    assert n["id"] == "github:test_pkg::a"
    assert n["belief"] == 0.9
    assert n["prior"] == 0.7
    assert n["exported"] is True
    assert n["module"] == "m1"


def test_strategy_becomes_node_with_role_edges():
    """Each strategy produces an intermediate node and role-tagged edges."""
    ir = _make_ir(
        knowledges=[
            {"id": "github:test_pkg::a", "label": "a", "type": "claim", "content": "A.", "module": "m1"},
            {"id": "github:test_pkg::b", "label": "b", "type": "claim", "content": "B.", "module": "m1"},
        ],
        strategies=[
            {"type": "deduction", "premises": ["github:test_pkg::a"],
             "background": [], "conclusion": "github:test_pkg::b", "reason": "A implies B."},
        ],
        module_order=["m1"],
    )

    data = json.loads(generate_graph_json(ir))

    strat_nodes = [n for n in data["nodes"] if n["type"] == "strategy"]
    assert len(strat_nodes) == 1
    sn = strat_nodes[0]
    assert sn["strategy_type"] == "deduction"
    assert sn["module"] == "m1"  # inherited from conclusion's module

    # Edges: a→strat (premise), strat→b (conclusion)
    premise_edges = [e for e in data["edges"] if e["role"] == "premise"]
    concl_edges = [e for e in data["edges"] if e["role"] == "conclusion"]
    assert len(premise_edges) == 1
    assert premise_edges[0]["source"] == "github:test_pkg::a"
    assert premise_edges[0]["target"] == sn["id"]
    assert len(concl_edges) == 1
    assert concl_edges[0]["source"] == sn["id"]
    assert concl_edges[0]["target"] == "github:test_pkg::b"


def test_background_edges_have_background_role():
    """Background premises get role='background'."""
    ir = _make_ir(
        knowledges=[
            {"id": "github:test_pkg::a", "label": "a", "type": "claim", "content": "A.", "module": "m1"},
            {"id": "github:test_pkg::bg", "label": "bg", "type": "setting", "content": "BG.", "module": "m1"},
            {"id": "github:test_pkg::b", "label": "b", "type": "claim", "content": "B.", "module": "m1"},
        ],
        strategies=[
            {"type": "deduction", "premises": ["github:test_pkg::a"],
             "background": ["github:test_pkg::bg"],
             "conclusion": "github:test_pkg::b", "reason": ""},
        ],
        module_order=["m1"],
    )

    data = json.loads(generate_graph_json(ir))
    bg_edges = [e for e in data["edges"] if e["role"] == "background"]
    assert len(bg_edges) == 1
    assert bg_edges[0]["source"] == "github:test_pkg::bg"


def test_operator_becomes_node():
    """Operator entries produce intermediate nodes."""
    ir = _make_ir(
        knowledges=[
            {"id": "github:test_pkg::x", "label": "x", "type": "claim", "content": "X.", "module": "m1"},
            {"id": "github:test_pkg::not_x", "label": "not_x", "type": "claim", "content": "NOT X.", "module": "m1"},
        ],
        operators=[
            {"operator": "NOT", "variables": ["github:test_pkg::x"],
             "conclusion": "github:test_pkg::not_x", "reason": "negation"},
        ],
        module_order=["m1"],
    )

    data = json.loads(generate_graph_json(ir))
    op_nodes = [n for n in data["nodes"] if n["type"] == "operator"]
    assert len(op_nodes) == 1
    assert op_nodes[0]["operator_type"] == "NOT"

    var_edges = [e for e in data["edges"] if e["role"] == "variable"]
    concl_edges = [e for e in data["edges"] if e["role"] == "conclusion"]
    assert len(var_edges) == 1
    assert len(concl_edges) == 1


def test_modules_array():
    """Top-level 'modules' array computed from knowledges and module_order."""
    ir = _make_ir(
        knowledges=[
            {"id": "github:test_pkg::a", "label": "a", "type": "claim", "content": "A.", "module": "m1"},
            {"id": "github:test_pkg::b", "label": "b", "type": "claim", "content": "B.", "module": "m1"},
            {"id": "github:test_pkg::c", "label": "c", "type": "claim", "content": "C.", "module": "m2"},
        ],
        strategies=[
            {"type": "deduction", "premises": ["github:test_pkg::a"],
             "background": [], "conclusion": "github:test_pkg::b", "reason": ""},
        ],
        module_order=["m1", "m2"],
    )

    data = json.loads(generate_graph_json(ir))
    modules = data["modules"]
    assert len(modules) == 2
    m1 = next(m for m in modules if m["id"] == "m1")
    assert m1["order"] == 0
    assert m1["node_count"] == 2
    assert m1["strategy_count"] == 1
    m2 = next(m for m in modules if m["id"] == "m2")
    assert m2["order"] == 1
    assert m2["node_count"] == 1
    assert m2["strategy_count"] == 0


def test_cross_module_edges():
    """Cross-module reasoning produces cross_module_edges."""
    ir = _make_ir(
        knowledges=[
            {"id": "github:test_pkg::a", "label": "a", "type": "claim", "content": "A.", "module": "m1"},
            {"id": "github:test_pkg::b", "label": "b", "type": "claim", "content": "B.", "module": "m2"},
        ],
        strategies=[
            {"type": "deduction", "premises": ["github:test_pkg::a"],
             "background": [], "conclusion": "github:test_pkg::b", "reason": ""},
        ],
        module_order=["m1", "m2"],
    )

    data = json.loads(generate_graph_json(ir))
    xmod = data["cross_module_edges"]
    assert len(xmod) == 1
    assert xmod[0]["from_module"] == "m1"
    assert xmod[0]["to_module"] == "m2"
    assert xmod[0]["count"] == 1


def test_helper_nodes_filtered():
    """Nodes with labels starting with __ are excluded."""
    ir = _make_ir(
        knowledges=[
            {"id": "github:test_pkg::a", "label": "a", "type": "claim", "content": "A.", "module": "m1"},
            {"id": "github:test_pkg::__helper", "label": "__helper", "type": "claim",
             "content": "Helper.", "module": "m1"},
        ],
        module_order=["m1"],
    )

    data = json.loads(generate_graph_json(ir))
    knowledge_nodes = [n for n in data["nodes"] if n["type"] not in ("strategy", "operator")]
    assert len(knowledge_nodes) == 1
    assert knowledge_nodes[0]["label"] == "a"


def test_no_beliefs_or_params():
    """Works with no beliefs or param data — priors/beliefs are None."""
    ir = _make_ir(
        knowledges=[
            {"id": "github:test_pkg::a", "label": "a", "type": "claim", "content": "A.", "module": "m1"},
        ],
        module_order=["m1"],
    )

    data = json.loads(generate_graph_json(ir))
    assert data["nodes"][0]["belief"] is None
    assert data["nodes"][0]["prior"] is None
    assert data["nodes"][0]["exported"] is False
```

- [ ] **Step 2: Run tests — verify they fail**

Run: `pytest tests/cli/test_graph_json.py -v`
Expected: Multiple FAILs (no `modules` key, no strategy nodes, no `role` on edges)

- [ ] **Step 3: Rewrite `_graph_json.py`**

Replace `gaia/cli/commands/_graph_json.py` with:

```python
"""Generate graph.json for interactive visualization (v2).

Strategy and operator entries are promoted to intermediate nodes.
Edges carry a ``role`` field (premise/background/conclusion/variable).
Top-level ``modules`` and ``cross_module_edges`` arrays are computed.
"""

from __future__ import annotations

import json
from collections import Counter


def generate_graph_json(
    ir: dict,
    beliefs_data: dict | None = None,
    param_data: dict | None = None,
    exported_ids: set[str] | None = None,
) -> str:
    """Return JSON string with nodes, edges, modules, and cross_module_edges."""
    beliefs: dict[str, float] = {}
    if beliefs_data:
        beliefs = {b["knowledge_id"]: b["belief"] for b in beliefs_data.get("beliefs", [])}
    priors: dict[str, float] = {}
    if param_data:
        priors = {p["knowledge_id"]: p["value"] for p in param_data.get("priors", [])}
    exported = exported_ids or set()

    # Knowledge-id → module lookup
    kid_module: dict[str, str] = {}
    for k in ir.get("knowledges", []):
        if k.get("module"):
            kid_module[k["id"]] = k["module"]

    module_order: list[str] = ir.get("module_order", [])
    module_order_map = {m: i for i, m in enumerate(module_order)}

    # --- Knowledge nodes ---
    nodes: list[dict] = []
    for k in ir["knowledges"]:
        label = k.get("label", "")
        if label.startswith("__"):
            continue
        kid = k["id"]
        nodes.append({
            "id": kid,
            "label": label,
            "title": k.get("title"),
            "type": k["type"],
            "module": k.get("module"),
            "content": k.get("content", ""),
            "prior": priors.get(kid),
            "belief": beliefs.get(kid),
            "exported": kid in exported,
            "metadata": k.get("metadata", {}),
        })

    edges: list[dict] = []
    strategy_counts: Counter[str] = Counter()
    cross_module: Counter[tuple[str, str]] = Counter()

    # --- Strategy nodes ---
    for i, s in enumerate(ir.get("strategies", [])):
        conc = s.get("conclusion")
        if not conc:
            continue
        conc_mod = kid_module.get(conc, "")
        strat_id = f"strat_{i}"

        nodes.append({
            "id": strat_id,
            "type": "strategy",
            "strategy_type": s.get("type", ""),
            "module": conc_mod,
            "reason": s.get("reason", ""),
        })
        strategy_counts[conc_mod] += 1

        for p in s.get("premises", []):
            edges.append({"source": p, "target": strat_id, "role": "premise"})
            p_mod = kid_module.get(p, "")
            if p_mod and conc_mod and p_mod != conc_mod:
                cross_module[(p_mod, conc_mod)] += 1
        for bg in s.get("background", []):
            edges.append({"source": bg, "target": strat_id, "role": "background"})
        edges.append({"source": strat_id, "target": conc, "role": "conclusion"})

    # --- Operator nodes ---
    for i, o in enumerate(ir.get("operators", [])):
        conc = o.get("conclusion")
        oper_id = f"oper_{i}"
        conc_mod = kid_module.get(conc, "") if conc else ""

        nodes.append({
            "id": oper_id,
            "type": "operator",
            "operator_type": o.get("operator", ""),
            "module": conc_mod,
        })

        for v in o.get("variables", []):
            edges.append({"source": v, "target": oper_id, "role": "variable"})
        if conc:
            edges.append({"source": oper_id, "target": conc, "role": "conclusion"})

    # --- Modules array ---
    module_node_counts: Counter[str] = Counter()
    for n in nodes:
        mod = n.get("module")
        if mod and n["type"] not in ("strategy", "operator"):
            module_node_counts[mod] += 1

    # Use module_order for ordering; append any unseen modules at end
    seen = set(module_order)
    all_mods = list(module_order)
    for mod in sorted(module_node_counts.keys()):
        if mod not in seen:
            all_mods.append(mod)

    modules = [
        {
            "id": mod,
            "order": idx,
            "node_count": module_node_counts.get(mod, 0),
            "strategy_count": strategy_counts.get(mod, 0),
        }
        for idx, mod in enumerate(all_mods)
        if module_node_counts.get(mod, 0) > 0 or strategy_counts.get(mod, 0) > 0
    ]

    # --- Cross-module edges ---
    cross_module_edges = [
        {"from_module": fm, "to_module": tm, "count": cnt}
        for (fm, tm), cnt in sorted(cross_module.items())
    ]

    return json.dumps(
        {
            "modules": modules,
            "cross_module_edges": cross_module_edges,
            "nodes": nodes,
            "edges": edges,
        },
        indent=2,
        ensure_ascii=False,
    )
```

- [ ] **Step 4: Run tests — verify all pass**

Run: `pytest tests/cli/test_graph_json.py -v`
Expected: All 8 tests PASS

- [ ] **Step 5: Run full test suite to check for regressions**

Run: `pytest tests/ -x -q`
Expected: No new failures. Existing tests that reference the old graph.json format (particularly in `tests/cli/` or integration tests) may need updating if they exist. The `_github.py` caller doesn't assert on graph.json structure so it should still pass.

- [ ] **Step 6: Commit**

```bash
git add gaia/cli/commands/_graph_json.py tests/cli/test_graph_json.py
git commit -m "feat(viz): rewrite graph.json — strategy/operator as nodes, role edges, modules array"
```

---

## Chunk 2: React Template — Types, Hooks, Package Config

### Task 2: Update `package.json` and `types.ts`

**Files:**
- Modify: `gaia/cli/templates/pages/package.json`
- Modify: `gaia/cli/templates/pages/src/types.ts`

- [ ] **Step 1: Update `package.json` — remove cytoscape, add elkjs**

Replace `gaia/cli/templates/pages/package.json` with:

```json
{
  "name": "gaia-knowledge-paper",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "vitest run"
  },
  "dependencies": {
    "elkjs": "^0.9",
    "react": "^18.3",
    "react-dom": "^18.3",
    "react-markdown": "^9",
    "remark-gfm": "^4"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6",
    "@testing-library/react": "^16",
    "@types/node": "^25.5.2",
    "@types/react": "^18",
    "@types/react-dom": "^18",
    "@vitejs/plugin-react": "^4",
    "jsdom": "^25",
    "typescript": "^5.5",
    "vite": "^6",
    "vitest": "^3"
  }
}
```

Changes: removed `cytoscape`, `cytoscape-dagre`, `@types/cytoscape`. Added `elkjs`.

- [ ] **Step 2: Rewrite `types.ts` with new schema**

Replace `gaia/cli/templates/pages/src/types.ts` with:

```typescript
// --- Node types ---

export interface KnowledgeNode {
  id: string
  label: string
  title?: string
  type: 'claim' | 'setting' | 'question' | 'action'
  module?: string
  content: string
  prior?: number | null
  belief?: number | null
  exported: boolean
  metadata: Record<string, unknown>
}

export interface StrategyNode {
  id: string
  type: 'strategy'
  strategy_type: string
  module?: string
  reason?: string
}

export interface OperatorNode {
  id: string
  type: 'operator'
  operator_type: string
  module?: string
}

export type GraphNode = KnowledgeNode | StrategyNode | OperatorNode

// --- Edge types ---

export interface GraphEdge {
  source: string
  target: string
  role: 'premise' | 'background' | 'conclusion' | 'variable'
}

// --- Module types ---

export interface ModuleInfo {
  id: string
  order: number
  node_count: number
  strategy_count: number
}

export interface CrossModuleEdge {
  from_module: string
  to_module: string
  count: number
}

// --- Top-level data ---

export interface GraphData {
  modules: ModuleInfo[]
  cross_module_edges: CrossModuleEdge[]
  nodes: GraphNode[]
  edges: GraphEdge[]
}

export interface MetaData {
  package_name: string
  namespace: string
  description?: string
}

// --- Type guards ---

export function isKnowledgeNode(n: GraphNode): n is KnowledgeNode {
  return n.type === 'claim' || n.type === 'setting' || n.type === 'question'
}

export function isStrategyNode(n: GraphNode): n is StrategyNode {
  return n.type === 'strategy'
}

export function isOperatorNode(n: GraphNode): n is OperatorNode {
  return n.type === 'operator'
}
```

- [ ] **Step 3: Commit**

```bash
git add gaia/cli/templates/pages/package.json gaia/cli/templates/pages/src/types.ts
git commit -m "feat(viz): update package.json (elkjs) and types.ts (new graph schema)"
```

### Task 3: Create `useGraphData` hook

**Files:**
- Create: `gaia/cli/templates/pages/src/hooks/useGraphData.ts`
- Create: `gaia/cli/templates/pages/src/__tests__/useGraphData.test.ts`

- [ ] **Step 1: Write failing test**

Create `gaia/cli/templates/pages/src/__tests__/useGraphData.test.ts`:

```typescript
import { describe, it, expect } from 'vitest'
import { filterNodesByModule, getExternalRefs } from '../hooks/useGraphData'
import type { GraphNode, GraphEdge } from '../types'

const nodes: GraphNode[] = [
  { id: 'a', label: 'a', type: 'claim', module: 'm1', content: '', exported: false, metadata: {} },
  { id: 'b', label: 'b', type: 'claim', module: 'm1', content: '', exported: false, metadata: {} },
  { id: 'c', label: 'c', type: 'claim', module: 'm2', content: '', exported: false, metadata: {} },
  { id: 'strat_0', type: 'strategy', strategy_type: 'deduction', module: 'm1' },
]

const edges: GraphEdge[] = [
  { source: 'a', target: 'strat_0', role: 'premise' },
  { source: 'c', target: 'strat_0', role: 'premise' },  // cross-module
  { source: 'strat_0', target: 'b', role: 'conclusion' },
]

describe('filterNodesByModule', () => {
  it('returns only nodes belonging to the given module', () => {
    const result = filterNodesByModule(nodes, 'm1')
    expect(result.map(n => n.id)).toEqual(['a', 'b', 'strat_0'])
  })
})

describe('getExternalRefs', () => {
  it('finds nodes referenced by edges but not in the module', () => {
    const moduleNodes = filterNodesByModule(nodes, 'm1')
    const moduleNodeIds = new Set(moduleNodes.map(n => n.id))
    const refs = getExternalRefs(edges, moduleNodeIds, nodes)
    expect(refs).toHaveLength(1)
    expect(refs[0].id).toBe('c')
    expect(refs[0].sourceModule).toBe('m2')
  })
})
```

- [ ] **Step 2: Run test — verify it fails**

Run: `cd gaia/cli/templates/pages && npx vitest run src/__tests__/useGraphData.test.ts`
Expected: FAIL — module not found

- [ ] **Step 3: Create `useGraphData.ts`**

Create `gaia/cli/templates/pages/src/hooks/useGraphData.ts`:

```typescript
import { useState, useEffect, useMemo } from 'react'
import type { GraphData, GraphNode, GraphEdge, MetaData } from '../types'

export interface ExternalRef {
  id: string
  label: string
  sourceModule: string
}

/** Filter nodes to those belonging to a specific module. */
export function filterNodesByModule(nodes: GraphNode[], moduleId: string): GraphNode[] {
  return nodes.filter(n => 'module' in n && n.module === moduleId)
}

/** Find nodes referenced by edges that are not in the module node set. */
export function getExternalRefs(
  edges: GraphEdge[],
  moduleNodeIds: Set<string>,
  allNodes: GraphNode[],
): ExternalRef[] {
  const nodesById = new Map(allNodes.map(n => [n.id, n]))
  const externalIds = new Set<string>()
  const refs: ExternalRef[] = []

  for (const e of edges) {
    for (const endpoint of [e.source, e.target]) {
      if (!moduleNodeIds.has(endpoint) && !externalIds.has(endpoint)) {
        externalIds.add(endpoint)
        const node = nodesById.get(endpoint)
        if (node) {
          refs.push({
            id: node.id,
            label: 'label' in node ? node.label : node.id,
            sourceModule: ('module' in node && node.module) || '',
          })
        }
      }
    }
  }
  return refs
}

/** Filter edges to those where at least one endpoint is in the node set. */
export function filterEdgesForModule(edges: GraphEdge[], nodeIds: Set<string>): GraphEdge[] {
  return edges.filter(e => nodeIds.has(e.source) || nodeIds.has(e.target))
}

export type LoadState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; graph: GraphData; meta: MetaData }

export function useGraphData(): LoadState {
  const [state, setState] = useState<LoadState>({ status: 'loading' })

  useEffect(() => {
    Promise.all([
      fetch('data/graph.json').then(r => {
        if (!r.ok) throw new Error(`graph.json: ${r.status}`)
        return r.json() as Promise<GraphData>
      }),
      fetch('data/meta.json').then(r => {
        if (!r.ok) throw new Error(`meta.json: ${r.status}`)
        return r.json() as Promise<MetaData>
      }),
    ])
      .then(([graph, meta]) => setState({ status: 'ready', graph, meta }))
      .catch((err: Error) => setState({ status: 'error', message: err.message }))
  }, [])

  return state
}
```

- [ ] **Step 4: Run test — verify it passes**

Run: `cd gaia/cli/templates/pages && npx vitest run src/__tests__/useGraphData.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add gaia/cli/templates/pages/src/hooks/useGraphData.ts \
       gaia/cli/templates/pages/src/__tests__/useGraphData.test.ts
git commit -m "feat(viz): add useGraphData hook with module filtering helpers"
```

### Task 4: Create `useChainHighlight` hook

**Files:**
- Create: `gaia/cli/templates/pages/src/hooks/useChainHighlight.ts`
- Create: `gaia/cli/templates/pages/src/__tests__/useChainHighlight.test.ts`

- [ ] **Step 1: Write failing test**

Create `gaia/cli/templates/pages/src/__tests__/useChainHighlight.test.ts`:

```typescript
import { describe, it, expect } from 'vitest'
import { computeUpstreamChain } from '../hooks/useChainHighlight'
import type { GraphEdge } from '../types'

/**
 * Test graph:
 *   a ──premise──→ strat_0 ──conclusion──→ b
 *   b ──premise──→ strat_1 ──conclusion──→ c
 *   d (disconnected)
 */
const edges: GraphEdge[] = [
  { source: 'a', target: 'strat_0', role: 'premise' },
  { source: 'strat_0', target: 'b', role: 'conclusion' },
  { source: 'b', target: 'strat_1', role: 'premise' },
  { source: 'strat_1', target: 'c', role: 'conclusion' },
]

describe('computeUpstreamChain', () => {
  it('returns the clicked node itself when it has no premises', () => {
    const chain = computeUpstreamChain('a', edges)
    expect(chain).toEqual(new Set(['a']))
  })

  it('traces back one step from a conclusion', () => {
    const chain = computeUpstreamChain('b', edges)
    expect(chain).toEqual(new Set(['a', 'strat_0', 'b']))
  })

  it('traces back multiple steps', () => {
    const chain = computeUpstreamChain('c', edges)
    expect(chain).toEqual(new Set(['a', 'strat_0', 'b', 'strat_1', 'c']))
  })

  it('returns only the node for disconnected nodes', () => {
    const chain = computeUpstreamChain('d', edges)
    expect(chain).toEqual(new Set(['d']))
  })
})
```

- [ ] **Step 2: Run test — verify it fails**

Run: `cd gaia/cli/templates/pages && npx vitest run src/__tests__/useChainHighlight.test.ts`
Expected: FAIL — module not found

- [ ] **Step 3: Create `useChainHighlight.ts`**

Create `gaia/cli/templates/pages/src/hooks/useChainHighlight.ts`:

```typescript
import { useState, useCallback } from 'react'
import type { GraphEdge } from '../types'

/**
 * BFS upstream from a node following edges in reverse direction.
 * Returns the set of all node IDs in the upstream chain.
 */
export function computeUpstreamChain(nodeId: string, edges: GraphEdge[]): Set<string> {
  // Build reverse adjacency: target → sources
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
```

- [ ] **Step 4: Run test — verify it passes**

Run: `cd gaia/cli/templates/pages && npx vitest run src/__tests__/useChainHighlight.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add gaia/cli/templates/pages/src/hooks/useChainHighlight.ts \
       gaia/cli/templates/pages/src/__tests__/useChainHighlight.test.ts
git commit -m "feat(viz): add useChainHighlight hook with BFS upstream traversal"
```

### Task 5: Create `useElkLayout` hook

**Files:**
- Create: `gaia/cli/templates/pages/src/hooks/useElkLayout.ts`
- Create: `gaia/cli/templates/pages/src/__tests__/useElkLayout.test.ts`

- [ ] **Step 1: Write failing test**

Create `gaia/cli/templates/pages/src/__tests__/useElkLayout.test.ts`:

```typescript
import { describe, it, expect } from 'vitest'
import { buildElkGraph } from '../hooks/useElkLayout'
import type { GraphNode, GraphEdge } from '../types'

const nodes: GraphNode[] = [
  { id: 'a', label: 'a', type: 'setting', module: 'm1', content: '', exported: false, metadata: {} },
  { id: 'strat_0', type: 'strategy', strategy_type: 'deduction', module: 'm1' },
  { id: 'b', label: 'b', type: 'claim', module: 'm1', content: '', exported: false, metadata: {} },
]

const edges: GraphEdge[] = [
  { source: 'a', target: 'strat_0', role: 'premise' },
  { source: 'strat_0', target: 'b', role: 'conclusion' },
]

describe('buildElkGraph', () => {
  it('produces ELK-compatible graph with children and edges', () => {
    const elk = buildElkGraph(nodes, edges)
    expect(elk.id).toBe('root')
    expect(elk.children).toHaveLength(3)
    expect(elk.edges).toHaveLength(2)
  })

  it('assigns different dimensions by node type', () => {
    const elk = buildElkGraph(nodes, edges)
    const setting = elk.children!.find(c => c.id === 'a')!
    const strategy = elk.children!.find(c => c.id === 'strat_0')!
    // Settings are wider (for label text)
    expect(setting.width).toBeGreaterThan(strategy.width!)
  })
})
```

- [ ] **Step 2: Run test — verify it fails**

Run: `cd gaia/cli/templates/pages && npx vitest run src/__tests__/useElkLayout.test.ts`
Expected: FAIL

- [ ] **Step 3: Create `useElkLayout.ts`**

Create `gaia/cli/templates/pages/src/hooks/useElkLayout.ts`:

```typescript
import { useState, useEffect } from 'react'
import ELK from 'elkjs/lib/elk.bundled.js'
import type { GraphNode, GraphEdge } from '../types'

const elk = new ELK()

export interface ElkNode {
  id: string
  x: number
  y: number
  width: number
  height: number
}

export interface ElkEdge {
  id: string
  source: string
  target: string
  sections?: Array<{ startPoint: { x: number; y: number }; endPoint: { x: number; y: number } }>
}

export interface LayoutResult {
  nodes: ElkNode[]
  edges: ElkEdge[]
  width: number
  height: number
}

function nodeDimensions(node: GraphNode): { width: number; height: number } {
  if (node.type === 'strategy') return { width: 100, height: 40 }
  if (node.type === 'operator') return { width: 48, height: 48 }
  // Knowledge nodes: estimate width from label length
  const label = 'label' in node ? node.label : node.id
  const charWidth = 8
  const padding = 32
  return { width: Math.max(120, Math.min(label.length * charWidth + padding, 240)), height: 48 }
}

/** Build an ELK-compatible graph input object. Exported for testing. */
export function buildElkGraph(
  nodes: GraphNode[],
  edges: GraphEdge[],
) {
  const nodeIds = new Set(nodes.map(n => n.id))
  return {
    id: 'root',
    layoutOptions: {
      'elk.algorithm': 'layered',
      'elk.direction': 'DOWN',
      'elk.spacing.nodeNode': '30',
      'elk.layered.spacing.nodeNodeBetweenLayers': '60',
      'elk.layered.crossingMinimization.strategy': 'LAYER_SWEEP',
    },
    children: nodes.map(n => {
      const dims = nodeDimensions(n)
      return { id: n.id, width: dims.width, height: dims.height }
    }),
    edges: edges
      .filter(e => nodeIds.has(e.source) && nodeIds.has(e.target))
      .map((e, i) => ({
        id: `e${i}`,
        sources: [e.source],
        targets: [e.target],
      })),
  }
}

export function useElkLayout(
  nodes: GraphNode[],
  edges: GraphEdge[],
): LayoutResult | null {
  const [layout, setLayout] = useState<LayoutResult | null>(null)

  useEffect(() => {
    if (nodes.length === 0) {
      setLayout(null)
      return
    }

    const graph = buildElkGraph(nodes, edges)

    elk.layout(graph).then(result => {
      const layoutNodes: ElkNode[] = (result.children ?? []).map(c => ({
        id: c.id,
        x: c.x ?? 0,
        y: c.y ?? 0,
        width: c.width ?? 100,
        height: c.height ?? 40,
      }))
      const layoutEdges: ElkEdge[] = (result.edges ?? []).map(e => ({
        id: e.id,
        source: (e.sources ?? [])[0] ?? '',
        target: (e.targets ?? [])[0] ?? '',
        sections: e.sections,
      }))
      setLayout({
        nodes: layoutNodes,
        edges: layoutEdges,
        width: result.width ?? 800,
        height: result.height ?? 600,
      })
    })
  }, [nodes, edges])

  return layout
}
```

- [ ] **Step 4: Run test — verify it passes**

Run: `cd gaia/cli/templates/pages && npx vitest run src/__tests__/useElkLayout.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add gaia/cli/templates/pages/src/hooks/useElkLayout.ts \
       gaia/cli/templates/pages/src/__tests__/useElkLayout.test.ts
git commit -m "feat(viz): add useElkLayout hook with ELK layered algorithm"
```

---

## Chunk 3: React Template — Components

### Task 6: Create `NodeRenderer` component

**Files:**
- Create: `gaia/cli/templates/pages/src/components/NodeRenderer.tsx`

This is a pure SVG rendering component — no interaction logic. No test needed (visual output only).

- [ ] **Step 1: Create `NodeRenderer.tsx`**

```typescript
import type { GraphNode } from '../types'
import { isKnowledgeNode, isStrategyNode, isOperatorNode } from '../types'

interface Props {
  node: GraphNode
  x: number
  y: number
  width: number
  height: number
  highlighted: boolean | null  // null = no highlight mode, true = in chain, false = dimmed
  onSelect: (id: string) => void
}

const BELIEF_COLORS = {
  high: '#4caf50',
  mid: '#ff9800',
  low: '#f44336',
  none: '#999',
} as const

function beliefColor(belief?: number | null): string {
  if (belief == null) return BELIEF_COLORS.none
  if (belief >= 0.7) return BELIEF_COLORS.high
  if (belief >= 0.4) return BELIEF_COLORS.mid
  return BELIEF_COLORS.low
}

const DETERMINISTIC = new Set(['deduction', 'reductio', 'elimination', 'mathematical_induction', 'case_analysis'])

const OP_SYMBOLS: Record<string, string> = {
  contradiction: '\u2297',
  equivalence: '\u2261',
  complement: '\u2295',
  disjunction: '\u2228',
  conjunction: '\u2227',
  implication: '\u2192',
}

export default function NodeRenderer({ node, x, y, width, height, highlighted, onSelect }: Props) {
  const opacity = highlighted === false ? 0.2 : 1
  const cursor = 'pointer'

  if (isKnowledgeNode(node)) {
    const isExternal = node.metadata?._external === true
    const fill = isExternal ? '#fff'
      : node.type === 'setting' ? '#f0f0f0'
      : node.type === 'question' ? '#fff3dd'
      : '#ddeeff'
    const stroke = isExternal ? '#aaa'
      : node.type === 'setting' ? '#999'
      : node.type === 'question' ? '#cc9944'
      : '#4488bb'
    const dashArray = isExternal ? '5,3' : undefined
    const rx = isExternal ? 8
      : node.type === 'setting' ? 2
      : node.type === 'question' ? height / 2
      : 8
    const label = node.title || node.label
    const truncated = label.length > 28 ? label.slice(0, 25) + '...' : label

    return (
      <g opacity={opacity} cursor={cursor} onClick={() => onSelect(node.id)}>
        <rect x={x} y={y} width={width} height={height} rx={rx} ry={rx}
          fill={fill} stroke={stroke} strokeWidth={node.exported ? 3 : 1.5}
          strokeDasharray={dashArray} />
        <text x={x + width / 2} y={y + height / 2 + 1} textAnchor="middle"
          dominantBaseline="middle" fontSize={11} fill="#333">
          {truncated}
        </text>
        {node.belief != null && (
          <g>
            <circle cx={x + width - 6} cy={y + 6} r={8} fill={beliefColor(node.belief)} />
            <text x={x + width - 6} y={y + 6 + 1} textAnchor="middle"
              dominantBaseline="middle" fontSize={7} fill="#fff" fontWeight="bold">
              {node.belief.toFixed(1)}
            </text>
          </g>
        )}
        <title>{`${label}\nPrior: ${node.prior ?? '—'} → Belief: ${node.belief ?? '—'}`}</title>
      </g>
    )
  }

  if (isStrategyNode(node)) {
    const isDeterministic = DETERMINISTIC.has(node.strategy_type)
    const fill = isDeterministic ? '#e8f5e9' : '#fff9c4'
    const stroke = isDeterministic ? '#44bb44' : '#f9a825'
    const dashArray = isDeterministic ? undefined : '5,3'
    // Hexagon points
    const cx = x + width / 2
    const cy = y + height / 2
    const hw = width / 2
    const hh = height / 2
    const inset = hw * 0.25
    const points = [
      `${x + inset},${y}`,
      `${x + width - inset},${y}`,
      `${x + width},${cy}`,
      `${x + width - inset},${y + height}`,
      `${x + inset},${y + height}`,
      `${x},${cy}`,
    ].join(' ')

    return (
      <g opacity={opacity} cursor={cursor} onClick={() => onSelect(node.id)}>
        <polygon points={points} fill={fill} stroke={stroke} strokeWidth={1.5}
          strokeDasharray={dashArray} />
        <text x={cx} y={cy + 1} textAnchor="middle" dominantBaseline="middle"
          fontSize={10} fill="#333">
          {node.strategy_type}
        </text>
        {node.reason && <title>{node.reason}</title>}
      </g>
    )
  }

  if (isOperatorNode(node)) {
    const cx = x + width / 2
    const cy = y + height / 2
    const r = Math.min(width, height) / 2
    const isContra = node.operator_type === 'contradiction'
    const symbol = OP_SYMBOLS[node.operator_type] ?? node.operator_type

    return (
      <g opacity={opacity} cursor={cursor} onClick={() => onSelect(node.id)}>
        <circle cx={cx} cy={cy} r={r} fill={isContra ? '#ffebee' : '#fff'}
          stroke={isContra ? '#c62828' : '#999'} strokeWidth={1.5} />
        <text x={cx} y={cy + 1} textAnchor="middle" dominantBaseline="middle"
          fontSize={16} fill="#333">
          {symbol}
        </text>
      </g>
    )
  }

  return null
}
```

- [ ] **Step 2: Commit**

```bash
git add gaia/cli/templates/pages/src/components/NodeRenderer.tsx
git commit -m "feat(viz): add NodeRenderer — SVG shapes by node type"
```

### Task 7: Create `EdgeRenderer` component

**Files:**
- Create: `gaia/cli/templates/pages/src/components/EdgeRenderer.tsx`

- [ ] **Step 1: Create `EdgeRenderer.tsx`**

```typescript
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
  const isContradiction = graphEdge?.role === 'variable'
    && false // operators handle contradiction via node color, not edge

  const stroke = isBackground ? '#999' : '#666'
  const dashArray = isBackground ? '6,4' : undefined

  // Use ELK section routing if available, otherwise straight line
  const section = layoutEdge.sections?.[0]
  if (!section) return null

  const { startPoint: sp, endPoint: ep } = section

  // Arrow marker ID
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
```

- [ ] **Step 2: Commit**

```bash
git add gaia/cli/templates/pages/src/components/EdgeRenderer.tsx
git commit -m "feat(viz): add EdgeRenderer — SVG edges with role-based styling"
```

### Task 8: Create `ModuleOverview` component (Level 1)

**Files:**
- Create: `gaia/cli/templates/pages/src/components/ModuleOverview.tsx`

- [ ] **Step 1: Create `ModuleOverview.tsx`**

```typescript
import { useMemo } from 'react'
import { useElkLayout, buildElkGraph } from '../hooks/useElkLayout'
import type { ModuleInfo, CrossModuleEdge, GraphNode, GraphEdge } from '../types'

interface Props {
  modules: ModuleInfo[]
  crossModuleEdges: CrossModuleEdge[]
  onSelectModule: (moduleId: string) => void
}

const MODULE_COLORS = [
  { fill: '#ddeeff', stroke: '#4488bb' },
  { fill: '#ddffdd', stroke: '#44bb44' },
  { fill: '#fff3dd', stroke: '#cc9944' },
  { fill: '#f3e8ff', stroke: '#7c3aed' },
  { fill: '#fce4ec', stroke: '#c62828' },
  { fill: '#e0f7fa', stroke: '#00838f' },
]

export default function ModuleOverview({ modules, crossModuleEdges, onSelectModule }: Props) {
  // Convert modules into pseudo-nodes for ELK layout
  const { pseudoNodes, pseudoEdges } = useMemo(() => {
    const pNodes: GraphNode[] = modules.map(m => ({
      id: m.id,
      label: m.id,
      type: 'setting' as const,
      module: m.id,
      content: '',
      exported: false,
      metadata: {},
    }))
    const pEdges: GraphEdge[] = crossModuleEdges.map(e => ({
      source: e.from_module,
      target: e.to_module,
      role: 'premise' as const,
    }))
    return { pseudoNodes: pNodes, pseudoEdges: pEdges }
  }, [modules, crossModuleEdges])

  const layout = useElkLayout(pseudoNodes, pseudoEdges)

  if (!layout) return <div style={{ padding: 40, textAlign: 'center', color: '#888' }}>Computing layout...</div>

  const padding = 40

  return (
    <svg
      width="100%"
      height="100%"
      viewBox={`${-padding} ${-padding} ${layout.width + padding * 2} ${layout.height + padding * 2}`}
      style={{ maxHeight: '80vh' }}
    >
      {/* Edges */}
      {layout.edges.map(e => {
        const section = e.sections?.[0]
        if (!section) return null
        return (
          <g key={e.id}>
            <defs>
              <marker id={`mo-${e.id}`} viewBox="0 0 10 10" refX="9" refY="5"
                markerWidth="6" markerHeight="6" orient="auto">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#999" />
              </marker>
            </defs>
            <line
              x1={section.startPoint.x} y1={section.startPoint.y}
              x2={section.endPoint.x} y2={section.endPoint.y}
              stroke="#999" strokeWidth={2} markerEnd={`url(#mo-${e.id})`}
            />
          </g>
        )
      })}

      {/* Module boxes */}
      {layout.nodes.map((ln, i) => {
        const mod = modules.find(m => m.id === ln.id)
        if (!mod) return null
        const color = MODULE_COLORS[i % MODULE_COLORS.length]
        return (
          <g key={ln.id} cursor="pointer" onClick={() => onSelectModule(ln.id)}>
            <rect
              x={ln.x} y={ln.y} width={ln.width} height={ln.height}
              rx={8} ry={8} fill={color.fill} stroke={color.stroke} strokeWidth={2}
            />
            <text x={ln.x + ln.width / 2} y={ln.y + 20} textAnchor="middle"
              fontSize={13} fontWeight="bold" fill="#333">
              {mod.id}
            </text>
            <text x={ln.x + ln.width / 2} y={ln.y + 36} textAnchor="middle"
              fontSize={11} fill="#666">
              {mod.node_count} nodes, {mod.strategy_count} strategies
            </text>
          </g>
        )
      })}
    </svg>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add gaia/cli/templates/pages/src/components/ModuleOverview.tsx
git commit -m "feat(viz): add ModuleOverview component (Level 1)"
```

### Task 9: Create `ModuleSubgraph` component (Level 2)

**Files:**
- Create: `gaia/cli/templates/pages/src/components/ModuleSubgraph.tsx`

- [ ] **Step 1: Create `ModuleSubgraph.tsx`**

```typescript
import { useMemo, useRef, useState, useCallback } from 'react'
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

  // Filter nodes/edges for this module + external refs
  const { moduleNodes, moduleEdges, externalRefs } = useMemo(() => {
    const mNodes = filterNodesByModule(allNodes, moduleId)
    const mNodeIds = new Set(mNodes.map(n => n.id))
    const mEdges = filterEdgesForModule(allEdges, mNodeIds)
    const refs = getExternalRefs(mEdges, mNodeIds, allNodes)
    // Add external ref as pseudo-nodes
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
    // Check if it's an external ref
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

  // Build edge lookup for EdgeRenderer
  const edgeByKey = new Map<string, GraphEdge>()
  for (const e of moduleEdges) {
    edgeByKey.set(`${e.source}->${e.target}`, e)
  }

  return (
    <div style={{ display: 'flex', height: '100%' }}>
      <div style={{ flex: 1, overflow: 'auto', position: 'relative' }}>
        {/* Breadcrumb */}
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
          {/* Edges */}
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
          {/* Nodes */}
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

      {/* Detail panel */}
      <DetailPanel
        node={selectedNode}
        edges={allEdges}
        nodesById={Object.fromEntries(nodesById)}
        onClose={clearSelection}
      />
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add gaia/cli/templates/pages/src/components/ModuleSubgraph.tsx
git commit -m "feat(viz): add ModuleSubgraph component (Level 2 with chain highlighting)"
```

### Task 10: Update `DetailPanel` (rename from ClaimDetail)

**Files:**
- Modify: `gaia/cli/templates/pages/src/components/ClaimDetail.tsx` → rename to `DetailPanel.tsx`
- Keep: `gaia/cli/templates/pages/src/components/ClaimDetail.module.css` → rename to `DetailPanel.module.css`

- [ ] **Step 1: Rename and update**

Rename `ClaimDetail.tsx` → `DetailPanel.tsx` and `ClaimDetail.module.css` → `DetailPanel.module.css`.

Update the import in `DetailPanel.tsx`:
- Change `import styles from './ClaimDetail.module.css'` to `import styles from './DetailPanel.module.css'`
- Update `Props` to accept the new `GraphNode` union type. The component already uses `node.label`, `node.type` etc. which are common fields. For strategy/operator nodes it should show type-specific info.
- Add a guard: if node is strategy/operator type, render simplified info.

Replace the `ClaimDetail.tsx` content with:

```typescript
import type { GraphNode, GraphEdge } from '../types'
import { isKnowledgeNode, isStrategyNode, isOperatorNode } from '../types'
import styles from './DetailPanel.module.css'

interface Props {
  node: GraphNode | null
  edges: GraphEdge[]
  nodesById: Record<string, GraphNode>
  onClose: () => void
}

function formatProb(v: number | null | undefined): string {
  return v != null ? v.toFixed(2) : '\u2014'
}

export default function DetailPanel({ node, edges, nodesById, onClose }: Props) {
  const incomingEdges = node ? edges.filter(e => e.target === node.id) : []
  const outgoingEdges = node ? edges.filter(e => e.source === node.id) : []

  return (
    <div className={`${styles.panel} ${node ? '' : styles.hidden}`}>
      {node && (
        <>
          <button className={styles.closeBtn} onClick={onClose} aria-label="close">
            &times;
          </button>

          <div className={styles.header}>
            <h2>{'label' in node ? node.label : node.id}</h2>
            <span className={styles.badge}>{node.type}</span>
            {isKnowledgeNode(node) && node.exported && (
              <span className={styles.exported}>{'\u2605'}</span>
            )}
          </div>

          {isKnowledgeNode(node) && (
            <>
              <div className={styles.probBar}>
                <span>Prior:</span>
                <span className={styles.probValue}>{formatProb(node.prior)}</span>
                <span>&rarr;</span>
                <span>Belief:</span>
                <span className={styles.probValue}>{formatProb(node.belief)}</span>
              </div>
              <div className={styles.content}>
                <p>{node.content}</p>
              </div>
            </>
          )}

          {isStrategyNode(node) && (
            <div className={styles.content}>
              <p><strong>Strategy:</strong> {node.strategy_type}</p>
              {node.reason && <p>{node.reason}</p>}
            </div>
          )}

          {isOperatorNode(node) && (
            <div className={styles.content}>
              <p><strong>Operator:</strong> {node.operator_type}</p>
            </div>
          )}

          {incomingEdges.length > 0 && (
            <div className={styles.reasoning}>
              <h3>Incoming</h3>
              {incomingEdges.map((edge, i) => {
                const src = nodesById[edge.source]
                return (
                  <div key={i} className={styles.chainItem}>
                    <span className={styles.strategyType}>{edge.role}</span>
                    {' from '}
                    <span>{src && 'label' in src ? src.label : edge.source}</span>
                  </div>
                )
              })}
            </div>
          )}

          {outgoingEdges.length > 0 && (
            <div className={styles.reasoning}>
              <h3>Outgoing</h3>
              {outgoingEdges.map((edge, i) => {
                const tgt = nodesById[edge.target]
                return (
                  <div key={i} className={styles.chainItem}>
                    <span className={styles.strategyType}>{edge.role}</span>
                    {' to '}
                    <span>{tgt && 'label' in tgt ? tgt.label : edge.target}</span>
                  </div>
                )
              })}
            </div>
          )}

          {isKnowledgeNode(node) && typeof node.metadata.figure === 'string' && (
            <div className={styles.figure}>
              <img src={node.metadata.figure} alt={`${node.label} figure`} />
            </div>
          )}
        </>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add gaia/cli/templates/pages/src/components/DetailPanel.tsx \
       gaia/cli/templates/pages/src/components/DetailPanel.module.css
git rm gaia/cli/templates/pages/src/components/ClaimDetail.tsx \
      gaia/cli/templates/pages/src/components/ClaimDetail.module.css
git commit -m "refactor(viz): rename ClaimDetail → DetailPanel, support all node types"
```

---

## Chunk 4: React Template — App Wiring, CSS, Cleanup

### Task 11: Rewrite `App.tsx`

**Files:**
- Modify: `gaia/cli/templates/pages/src/App.tsx`

- [ ] **Step 1: Replace `App.tsx`**

```typescript
import { useState, useCallback } from 'react'
import { useGraphData } from './hooks/useGraphData'
import ModuleOverview from './components/ModuleOverview'
import ModuleSubgraph from './components/ModuleSubgraph'
import LanguageSwitch from './components/LanguageSwitch'
import SectionView from './components/SectionView'

type ViewState =
  | { level: 'overview' }
  | { level: 'module'; moduleId: string; focusNodeId?: string }

export default function App() {
  const state = useGraphData()
  const [view, setView] = useState<ViewState>({ level: 'overview' })
  const [lang, setLang] = useState<'en' | 'zh'>('en')

  const sections = state.status === 'ready'
    ? state.graph.modules.map(m => m.id)
    : []

  const handleSelectModule = useCallback((moduleId: string) => {
    setView({ level: 'module', moduleId })
  }, [])

  const handleBack = useCallback(() => {
    setView({ level: 'overview' })
  }, [])

  const handleNavigateToModule = useCallback((moduleId: string, nodeId: string) => {
    setView({ level: 'module', moduleId, focusNodeId: nodeId })
  }, [])

  if (state.status === 'loading') {
    return <div style={{ padding: 40, textAlign: 'center' }}>Loading...</div>
  }

  if (state.status === 'error') {
    return <div role="alert" style={{ padding: 40, color: '#c00' }}>{state.message}</div>
  }

  const { graph, meta } = state

  return (
    <div className="app-layout">
      <div className="app-header">
        <h1>{meta.package_name}</h1>
        <LanguageSwitch lang={lang} onChange={setLang} />
      </div>

      <div className="graph-panel">
        {view.level === 'overview' ? (
          <ModuleOverview
            modules={graph.modules}
            crossModuleEdges={graph.cross_module_edges}
            onSelectModule={handleSelectModule}
          />
        ) : (
          <ModuleSubgraph
            moduleId={view.moduleId}
            allNodes={graph.nodes}
            allEdges={graph.edges}
            onBack={handleBack}
            onNavigateToModule={handleNavigateToModule}
          />
        )}
      </div>

      <div className="section-panel">
        <SectionView sections={sections} lang={lang} />
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add gaia/cli/templates/pages/src/App.tsx
git commit -m "feat(viz): rewrite App.tsx with two-level module navigation"
```

### Task 12: Update CSS layout

**Files:**
- Modify: `gaia/cli/templates/pages/src/index.css`

- [ ] **Step 1: Replace `index.css`**

```css
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }

.app-layout {
  display: grid;
  grid-template-columns: 1fr;
  grid-template-rows: auto 1fr auto;
  grid-template-areas: "header" "graph" "sections";
  min-height: 100vh;
}
.app-header {
  grid-area: header;
  padding: 1rem 2rem;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.graph-panel {
  grid-area: graph;
  min-height: 500px;
  position: relative;
}
.section-panel {
  grid-area: sections;
  padding: 2rem;
}
```

The detail panel column is gone from the grid — `DetailPanel` is now rendered inside `ModuleSubgraph` as a sliding overlay.

- [ ] **Step 2: Commit**

```bash
git add gaia/cli/templates/pages/src/index.css
git commit -m "refactor(viz): simplify CSS grid — detail panel now inside ModuleSubgraph"
```

### Task 13: Remove old `KnowledgeGraph.tsx` and update tests

**Files:**
- Delete: `gaia/cli/templates/pages/src/components/KnowledgeGraph.tsx`
- Delete: `gaia/cli/templates/pages/src/components/KnowledgeGraph.module.css`
- Delete: `gaia/cli/templates/pages/src/__tests__/KnowledgeGraph.test.tsx`
- Delete: `gaia/cli/templates/pages/src/__tests__/ClaimDetail.test.tsx`
- Modify: `gaia/cli/templates/pages/src/__tests__/App.test.tsx`
- Delete: `gaia/cli/templates/pages/src/__tests__/scaffold.test.tsx` (references old structure)

- [ ] **Step 1: Delete old files**

```bash
git rm gaia/cli/templates/pages/src/components/KnowledgeGraph.tsx \
      gaia/cli/templates/pages/src/components/KnowledgeGraph.module.css \
      gaia/cli/templates/pages/src/__tests__/KnowledgeGraph.test.tsx \
      gaia/cli/templates/pages/src/__tests__/ClaimDetail.test.tsx \
      gaia/cli/templates/pages/src/__tests__/scaffold.test.tsx
```

- [ ] **Step 2: Rewrite `App.test.tsx`**

Replace `gaia/cli/templates/pages/src/__tests__/App.test.tsx`:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'

// Mock elkjs (no WASM in jsdom)
vi.mock('elkjs/lib/elk.bundled.js', () => ({
  default: class {
    layout(graph: { children?: { id: string; width: number; height: number }[] }) {
      return Promise.resolve({
        ...graph,
        width: 800,
        height: 600,
        children: (graph.children ?? []).map((c, i) => ({
          ...c,
          x: i * 150,
          y: i * 80,
        })),
        edges: [],
      })
    }
  },
}))

import App from '../App'

const mockGraph = {
  modules: [{ id: 'm1', order: 0, node_count: 1, strategy_count: 0 }],
  cross_module_edges: [],
  nodes: [
    { id: 'a', label: 'A', type: 'claim', module: 'm1', content: 'Test',
      exported: false, metadata: {}, prior: null, belief: null },
  ],
  edges: [],
}
const mockMeta = { package_name: 'test-pkg', namespace: 'github' }

beforeEach(() => {
  vi.stubGlobal(
    'fetch',
    vi.fn((url: string) => {
      let data: unknown = {}
      if (url.includes('graph.json')) data = mockGraph
      if (url.includes('meta.json')) data = mockMeta
      return Promise.resolve({ ok: true, json: () => Promise.resolve(data) })
    }),
  )
})

describe('App', () => {
  it('shows loading then title', async () => {
    render(<App />)
    expect(screen.getByText(/loading/i)).toBeInTheDocument()
    await waitFor(() => expect(screen.getByText('test-pkg')).toBeInTheDocument())
  })

  it('renders module overview when ready', async () => {
    render(<App />)
    await waitFor(() => expect(screen.getByText('test-pkg')).toBeInTheDocument())
    // Module overview should show module name
    await waitFor(() => expect(screen.getByText('m1')).toBeInTheDocument())
  })

  it('shows error on fetch failure', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.resolve({ ok: false, status: 500, json: () => Promise.resolve({}) })),
    )
    render(<App />)
    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument())
  })
})
```

- [ ] **Step 3: Run all React tests**

Run: `cd gaia/cli/templates/pages && npx vitest run`
Expected: All tests PASS (App, useGraphData, useChainHighlight, useElkLayout, LanguageSwitch, SectionView, pages-workflow)

- [ ] **Step 4: Commit**

```bash
git add -A gaia/cli/templates/pages/
git commit -m "refactor(viz): remove old cytoscape components, update App test for new architecture"
```

---

## Chunk 5: Integration Test & Manual Verification

### Task 14: Run Python tests end-to-end

- [ ] **Step 1: Run full Python test suite**

Run: `pytest tests/ -x -q`
Expected: All pass. If any integration tests reference old `graph.json` format, update them to expect new schema.

- [ ] **Step 2: Test with real package**

Run:

```bash
cd /Users/z/Kali-Server/md/rydberg-qh-gaia
gaia render . --target github
```

Expected: `.github-output/docs/public/data/graph.json` contains `modules`, `cross_module_edges`, strategy nodes, role-tagged edges.

- [ ] **Step 3: Verify graph.json structure**

```bash
python3 -c "
import json
d = json.load(open('.github-output/docs/public/data/graph.json'))
print('modules:', len(d['modules']))
print('cross_module_edges:', len(d['cross_module_edges']))
strat = [n for n in d['nodes'] if n['type'] == 'strategy']
print('strategy nodes:', len(strat))
roles = set(e['role'] for e in d['edges'])
print('edge roles:', roles)
"
```

Expected output (approximately):
```
modules: 5
cross_module_edges: N (>0)
strategy nodes: 10
edge roles: {'premise', 'background', 'conclusion'}
```

- [ ] **Step 4: Commit any fixes**

### Task 15: Manual browser verification

- [ ] **Step 1: Install and start dev server**

```bash
cd /Users/z/Kali-Server/md/rydberg-qh-gaia/.github-output/docs
npm install
npm run dev
```

- [ ] **Step 2: Verify Level 1 (Module Overview)**

Open browser at `http://localhost:5173`. Check:
- All 5 modules displayed as boxes with names and counts
- Cross-module arrows visible between modules
- Click any module → navigates to Level 2

- [ ] **Step 3: Verify Level 2 (Module Subgraph)**

Click `s2_laser_assisted_dipole`. Check:
- Breadcrumb shows `← All Modules / s2_laser_assisted_dipole`
- Strategy nodes (hexagons) visible between premise and conclusion nodes
- Settings are gray rectangles, claims are blue rounded rectangles
- Belief badges visible on claim nodes
- External reference nodes (dashed) visible for cross-module premises

- [ ] **Step 4: Verify chain highlighting**

Click any conclusion node (e.g., `effective_exchange_y`). Check:
- Upstream chain highlighted (premises, strategy, their premises)
- Non-chain nodes dimmed to ~20% opacity
- Detail panel slides in from right with node info

- [ ] **Step 5: Verify cross-module navigation**

Click an external reference node. Check:
- Navigates to the source module
- Referenced node is visible in the new subgraph

- [ ] **Step 6: Final commit**

```bash
git add -A
git commit -m "test(viz): verify knowledge graph viz redesign end-to-end"
```

### Task 16: Lint, format, push, and create PR

- [ ] **Step 1: Lint and format**

```bash
ruff check .
ruff format .
```

- [ ] **Step 2: Push and create PR**

```bash
git push -u origin feat/knowledge-graph-viz-redesign
gh pr create --title "feat(viz): module-first knowledge graph with ELK layout" \
  --body "$(cat <<'EOF'
## Summary
- Rewrite graph.json: strategy/operator as intermediate nodes, role-tagged edges, modules array
- Replace Cytoscape+dagre with ELK layered layout + React SVG rendering
- Two-level navigation: module overview → per-module reasoning subgraph
- Chain highlighting: click node to BFS-highlight upstream reasoning chain
- New node shapes by type: setting (rect), claim (rounded), question (ellipse), strategy (hexagon)

## Spec
docs/specs/2026-04-12-knowledge-graph-viz-redesign.md

## Test plan
- [ ] `pytest tests/cli/test_graph_json.py` — new graph.json schema tests
- [ ] `vitest run` — React hooks and component tests
- [ ] Manual: `gaia render` on rydberg-qh-gaia, `npm run dev`, verify two-level navigation
- [ ] Manual: verify chain highlighting, cross-module navigation, belief badges

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 3: Check CI**

```bash
gh run list --branch feat/knowledge-graph-viz-redesign --limit 1
```

If CI fails, check logs and fix:

```bash
gh run view <run-id> --log-failed
```
