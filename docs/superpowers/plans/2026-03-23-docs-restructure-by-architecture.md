# Docs Restructure: Three-Layer Architecture

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorganize `docs/foundations/` from document-type-based organization (theory / concepts / interfaces / implementations) to architecture-layer-based organization (theory / rationale / graph-ir / bp / cli / lkm), eliminating content duplication and enforcing clean layer boundaries.

**Architecture:** The new structure mirrors Gaia's three-layer compilation pipeline (Gaia Lang → Graph IR → BP), with two product surfaces (CLI, LKM) that share Graph IR and BP as their common contract. Each doc belongs to exactly one layer; cross-layer references use relative links but never duplicate definitions.

**Principles:**
1. FactorNode defined once in `graph-ir/factor-nodes.md` — BP references it, Lang doesn't mention it
2. Theory contains zero Gaia-specific content
3. Each layer only references downward: Lang doesn't know Graph IR, Graph IR doesn't know BP
4. CLI and LKM are sibling product surfaces sharing graph-ir/ and bp/

---

## Current → New Directory Mapping

```
NEW STRUCTURE                     SOURCE(S)
─────────────────────────────────────────────────────────────────

foundations/
  theory/
    plausible-reasoning.md      ← theory/theoretical-foundation.md (purge Gaia content)
    belief-propagation.md       ← theory/belief-propagation.md (purge Gaia factor types)
    scientific-ontology.md      ← theory/scientific-ontology.md (keep, minor edits)

  rationale/
    product-scope.md            ← product-scope.md (remove theory duplication)
    architecture-overview.md    ← NEW (three-layer arch + CLI↔LKM contract via Graph IR)
    domain-vocabulary.md        ← gaia-concepts/package-model.md (high-level terms only)
    type-system-direction.md    ← gaia-concepts/type-system-direction.md (move as-is)
    documentation-policy.md     ← documentation-policy.md (move as-is)

  graph-ir/
    overview.md                 ← interfaces/graph-ir.md (three identity layers, purpose)
    knowledge-nodes.md          ← interfaces/graph-ir.md (node schemas extracted)
    factor-nodes.md             ← gaia-concepts/factor-design.md (schema + compilation rules)
                                  + gaia-concepts/reasoning-relations.md (compilation rules)
                                  REMOVE: potential functions → bp/potentials.md
    canonicalization.md         ← implementations/engines/canonicalization-engine.md (local part)
                                  + graph-ir archive (canonicalization sections)
    parameterization.md         ← interfaces/graph-ir.md (LocalParameterization section)

  bp/
    potentials.md               ← gaia-concepts/factor-design.md (potential sections)
                                  + gaia-concepts/reasoning-relations.md (potential sections)
                                  + theory/belief-propagation.md (Gaia factor type potentials)
    inference.md                ← theory/belief-propagation.md (sum-product algorithm)
                                  + implementations/engines/bp-engine.md
    local-vs-global.md          ← interfaces/lifecycle.md (inference parts)
                                  + implementations/engines/bp-engine.md (global sections)

  cli/
    gaia-lang/
      spec.md                   ← interfaces/language-spec.md (move)
      knowledge-types.md        ← gaia-concepts/knowledge-types.md
                                  REMOVE: BP role, Graph IR mapping → other layers
      package-model.md          ← gaia-concepts/package-model.md (authoring concepts)
                                  REMOVE: identity layers → graph-ir/
      proof-state.md            ← gaia-concepts/knowledge-types.md (proof state sections)
    lifecycle.md                ← interfaces/lifecycle.md (CLI sections)
                                  + implementations/entry-points/cli.md
    local-inference.md          ← implementations/engines/bp-engine.md (local sections)
    local-storage.md            ← implementations/storage.md (LanceDB + Kuzu embedded parts)
    compiler.md                 ← implementations/engines/graph-ir-compiler.md

  lkm/
    overview.md                 ← implementations/entry-points/server.md
                                  + implementations/overview.md (LKM parts)
    review-pipeline.md          ← implementations/engines/review-engine.md
    global-canonicalization.md  ← implementations/engines/canonicalization-engine.md (global part)
    curation.md                 ← implementations/engines/curation-engine.md
    global-inference.md         ← implementations/engines/bp-engine.md (global parts)
                                  + interfaces/lifecycle.md (LKM inference sections)
    pipeline.md                 ← implementations/entry-points/pipeline.md
    storage.md                  ← implementations/storage.md (server parts)
    api.md                      ← interfaces/api.md
    agent-credit.md             ← interfaces/agent-credit.md
    lifecycle.md                ← interfaces/lifecycle.md (LKM sections)

DELETED (merged into above):
  gaia-concepts/                ← entire directory removed
  interfaces/                   ← entire directory removed
  implementations/              ← entire directory removed

MOVED TO archive/:
  foundations_archive/          ← merge into docs/archive/foundations-v2/
```

---

## Chunk 1: Scaffold + Theory + Rationale

### Task 1.1: Create new directory structure

**Files:**
- Create: `docs/foundations/rationale/` (new dir)
- Create: `docs/foundations/graph-ir/` (new dir)
- Create: `docs/foundations/bp/` (new dir)
- Create: `docs/foundations/cli/` (new dir)
- Create: `docs/foundations/cli/gaia-lang/` (new dir)
- Create: `docs/foundations/lkm/` (new dir)

- [ ] **Step 1: Create all new directories**

```bash
mkdir -p docs/foundations/{rationale,graph-ir,bp,cli/gaia-lang,lkm}
```

- [ ] **Step 2: Commit scaffold**

```bash
# Add .gitkeep files so empty dirs are tracked
touch docs/foundations/{rationale,graph-ir,bp,cli/gaia-lang,lkm}/.gitkeep
git add docs/foundations/
git commit -m "docs: scaffold new architecture-layer directory structure"
```

### Task 1.2: Theory — purify plausible-reasoning.md

`theory/theoretical-foundation.md` currently mixes Jaynes theory with Gaia product descriptions ("Gaia 是什么", "Language → CLI → Cloud" diagram). Extract pure theory.

**Files:**
- Read: `docs/foundations/theory/theoretical-foundation.md`
- Create: `docs/foundations/theory/plausible-reasoning.md`
- Delete: `docs/foundations/theory/theoretical-foundation.md`

- [ ] **Step 1: Read full source file**
- [ ] **Step 2: Write `plausible-reasoning.md`**

Content rules:
- Keep: §2 Jaynes 纲领 (Cox theorem, three rules, four syllogisms), §3 MaxEnt, §4 Cromwell's Rule, §5 Jaynes's Robot
- Remove: §1 "Gaia 是什么" (product description → rationale/product-scope.md)
- Remove: "Language → CLI → Cloud" architecture diagram
- Remove: all `#claim`, `#setting`, Gaia DSL syntax references
- Header: `# Plausible Reasoning — Jaynes Framework`
- Add note: "This document describes the mathematical foundations. For how Gaia applies these principles, see `../rationale/product-scope.md`."

- [ ] **Step 3: Delete old file, commit**

```bash
git rm docs/foundations/theory/theoretical-foundation.md
git add docs/foundations/theory/plausible-reasoning.md
git commit -m "docs(theory): extract pure Jaynes theory, remove Gaia-specific content"
```

### Task 1.3: Theory — purify belief-propagation.md

Current `belief-propagation.md` starts with pure BP algorithm but then defines Gaia-specific factor types and their potentials.

**Files:**
- Read: `docs/foundations/theory/belief-propagation.md`
- Modify: `docs/foundations/theory/belief-propagation.md`

- [ ] **Step 1: Read full source file**
- [ ] **Step 2: Edit to keep only pure algorithm**

Content rules:
- Keep: §1 Factor Graphs (general definition), §2 Sum-Product Message Passing (algorithm), §3 Convergence/Damping
- Remove: §4+ any Gaia-specific factor type definitions (reasoning, mutex_constraint, equiv_constraint, instantiation, retraction) → these go to `bp/potentials.md` later
- Remove: references to `libs/inference/bp.py`, `libs/storage/models.py`
- Add note: "For Gaia's specific factor potentials, see `../bp/potentials.md`."

- [ ] **Step 3: Commit**

```bash
git add docs/foundations/theory/belief-propagation.md
git commit -m "docs(theory): remove Gaia-specific factor types from pure BP theory"
```

### Task 1.4: Theory — verify scientific-ontology.md

**Files:**
- Read: `docs/foundations/theory/scientific-ontology.md`

- [ ] **Step 1: Read and verify it's Gaia-independent**

If it references `#claim`, `#setting`, or Gaia DSL syntax → remove those references and add a forward pointer to `../cli/gaia-lang/knowledge-types.md`.

- [ ] **Step 2: Commit if changed**

### Task 1.5: Rationale — move and clean product-scope.md

**Files:**
- Read: `docs/foundations/product-scope.md`
- Create: `docs/foundations/rationale/product-scope.md`
- Delete: `docs/foundations/product-scope.md`

- [ ] **Step 1: Read full source**
- [ ] **Step 2: Write `rationale/product-scope.md`**

Content rules:
- Keep: product positioning, "what Gaia is", "why existing tools can't replace it", product direction, current baseline, roadmap
- Remove: detailed Jaynes theory (§2.2 Cox theorem derivation etc.) — replace with link to `../theory/plausible-reasoning.md`
- Keep the comparison table (Pyro/Stan vs Gaia) — this is a design rationale, not theory
- Update cross-references to new paths

- [ ] **Step 3: Delete old, commit**

```bash
git rm docs/foundations/product-scope.md
git add docs/foundations/rationale/product-scope.md
git commit -m "docs(rationale): move product-scope, remove theory duplication"
```

### Task 1.6: Rationale — create architecture-overview.md

**Files:**
- Create: `docs/foundations/rationale/architecture-overview.md`
- Reference: `docs/foundations/implementations/overview.md` (for current architecture)

- [ ] **Step 1: Write `rationale/architecture-overview.md`**

This is the most important new document. Content:

```markdown
# Architecture Overview

## Three-Layer Pipeline

Gaia's core is a compilation pipeline with three layers:

1. **Gaia Lang** — the authored surface (Typst DSL)
2. **Graph IR** — the structural factor graph intermediate representation
3. **BP** — belief propagation computation on Graph IR

Each layer has a clean boundary:
- Gaia Lang compiles to Graph IR (deterministic, auditable)
- Graph IR is the submission format — the contract between CLI and LKM
- BP runs on Graph IR + parameterization overlay

## Two Product Surfaces

| | CLI | LKM |
|---|---|---|
| Scope | Local, single package | Global, multi-package |
| Input | Gaia Lang source | Published Graph IR |
| Computation | Local BP | Review + Canonicalization + Curation + Global BP |
| Storage | LanceDB + Kuzu (embedded) | LanceDB + Neo4j + Vector |

The CLI is a frontend for Graph IR (like Clang is a frontend for LLVM IR).
The LKM never sees Gaia Lang — it operates purely on Graph IR.

## Why This Decomposition

Graph IR as the contract layer provides:
- **Auditable lowering** — the mapping from source to factor graph is explicit
- **Frontend independence** — future frontends can produce Graph IR without Typst
- **CLI↔LKM decoupling** — the LKM only validates and operates on Graph IR
```

- [ ] **Step 2: Commit**

```bash
git add docs/foundations/rationale/architecture-overview.md
git commit -m "docs(rationale): add architecture overview — three-layer pipeline + two product surfaces"
```

### Task 1.7: Rationale — move remaining files

**Files:**
- Move: `gaia-concepts/type-system-direction.md` → `rationale/type-system-direction.md`
- Move: `documentation-policy.md` → `rationale/documentation-policy.md`
- Create: `rationale/domain-vocabulary.md` (extract from `gaia-concepts/package-model.md`)

- [ ] **Step 1: Move type-system-direction.md**

```bash
git mv docs/foundations/gaia-concepts/type-system-direction.md docs/foundations/rationale/type-system-direction.md
```

- [ ] **Step 2: Move documentation-policy.md**

```bash
git mv docs/foundations/documentation-policy.md docs/foundations/rationale/documentation-policy.md
```

- [ ] **Step 3: Write `rationale/domain-vocabulary.md`**

Extract high-level vocabulary definitions from `gaia-concepts/package-model.md`:
- Knowledge, Chain, Module, Package — one paragraph each, no schema
- Link to `graph-ir/` for structural definitions, `cli/gaia-lang/` for language surface

- [ ] **Step 4: Commit**

```bash
git add docs/foundations/rationale/
git commit -m "docs(rationale): move type-system, doc-policy, add domain vocabulary"
```

---

## Chunk 2: Graph IR + BP layers

### Task 2.1: Graph IR — overview.md (three identity layers)

**Files:**
- Read: `docs/foundations/interfaces/graph-ir.md`
- Create: `docs/foundations/graph-ir/overview.md`

- [ ] **Step 1: Read interfaces/graph-ir.md**
- [ ] **Step 2: Write `graph-ir/overview.md`**

Content:
- Purpose: what Graph IR is, why it exists
- Three identity layers: Raw → Local Canonical → Global Canonical (descriptions only)
- Canonical JSON and graph hash
- Build-time generation rules summary table
- Forward links to `knowledge-nodes.md`, `factor-nodes.md`
- Remove: FactorNode schema (→ factor-nodes.md), LocalParameterization (→ parameterization.md)
- Remove: implementation table (→ cli/compiler.md or lkm/)

- [ ] **Step 3: Commit**

### Task 2.2: Graph IR — knowledge-nodes.md

**Files:**
- Read: `docs/foundations/interfaces/graph-ir.md` (node schemas)
- Create: `docs/foundations/graph-ir/knowledge-nodes.md`

- [ ] **Step 1: Write `graph-ir/knowledge-nodes.md`**

Content — the single definition point for knowledge node schemas:
- `RawKnowledgeNode` schema (fields, identity rule: sha256)
- `LocalCanonicalNode` schema (member_raw_node_ids, representative_content)
- `GlobalCanonicalNode` schema (registry-assigned, member_local_nodes)
- `CanonicalBinding` schema
- Output artifact paths (`graph_ir/raw_graph.json`, etc.)
- NO potential functions, NO BP behavior

- [ ] **Step 2: Commit**

### Task 2.3: Graph IR — factor-nodes.md (THE single definition)

This is the most important file in the restructure. Currently FactorNode is defined in three places: `gaia-concepts/factor-design.md`, `interfaces/graph-ir.md`, and `gaia-concepts/reasoning-relations.md`.

**Files:**
- Read: `docs/foundations/gaia-concepts/factor-design.md`
- Read: `docs/foundations/gaia-concepts/reasoning-relations.md`
- Read: `docs/foundations/interfaces/graph-ir.md`
- Create: `docs/foundations/graph-ir/factor-nodes.md`

- [ ] **Step 1: Read all three source files**
- [ ] **Step 2: Write `graph-ir/factor-nodes.md`**

Content — **FactorNode defined ONCE**:
```markdown
# Factor Nodes

## FactorNode Schema

(Single canonical schema — referenced by all other docs)

## Factor Types

### reasoning
- Generated from: `#claim(from: ...)` or `#action(from: ...)`
- Structure: premises (from: labels), conclusion (the claim/action)
- Covers: deduction, induction, abstraction (same structure, different conditional probability range)

### instantiation
- Generated from: schema elaboration
- Structure: premises = [schema_node], conclusion = ground instance

### mutex_constraint
- Generated from: `#relation(type: "contradiction", between: ...)`
- Structure: premises = [R, A, B], conclusion = R

### equiv_constraint
- Generated from: `#relation(type: "equivalence", between: ...)`
- Structure: premises = [R, A, B], conclusion = R

### retraction
- Generated from: chains with type: "retraction"
- Structure: premises = evidence nodes, conclusion = retracted claim

## Compilation Rules

| Source construct | Knowledge node(s) | Factor node(s) |
(comprehensive table)

## Note on potential functions

For the computational semantics (potential functions) of each factor type, see `../bp/potentials.md`. This document defines structure only.
```

- [ ] **Step 3: Commit**

```bash
git add docs/foundations/graph-ir/factor-nodes.md
git commit -m "docs(graph-ir): single canonical FactorNode definition, remove duplication"
```

### Task 2.4: Graph IR — canonicalization.md

**Files:**
- Read: `docs/foundations/implementations/engines/canonicalization-engine.md`
- Read: `docs/foundations_archive/graph-ir.md` (canonicalization sections)
- Create: `docs/foundations/graph-ir/canonicalization.md`

- [ ] **Step 1: Write `graph-ir/canonicalization.md`**

Content:
- Local canonicalization: what it is, when it runs (during `gaia build`)
- Global canonicalization: what it is, when it runs (during LKM review)
- Canonicalization log format
- Link to `../lkm/global-canonicalization.md` for server-side implementation details

- [ ] **Step 2: Commit**

### Task 2.5: Graph IR — parameterization.md

**Files:**
- Read: `docs/foundations/interfaces/graph-ir.md` (LocalParameterization section)
- Create: `docs/foundations/graph-ir/parameterization.md`

- [ ] **Step 1: Write `graph-ir/parameterization.md`**

Content:
- LocalParameterization overlay schema
- FactorParams schema
- GlobalInferenceState schema
- Graph hash integrity check
- "Structure is separated from parameters" principle

- [ ] **Step 2: Commit**

### Task 2.6: BP — potentials.md

**Files:**
- Read: `docs/foundations/gaia-concepts/factor-design.md` (potential sections)
- Read: `docs/foundations/gaia-concepts/reasoning-relations.md` (potential sections)
- Read: `docs/foundations/theory/belief-propagation.md` (Gaia factor type sections, now removed from theory)
- Create: `docs/foundations/bp/potentials.md`

- [ ] **Step 1: Write `bp/potentials.md`**

Content — potential functions for each factor type:
```markdown
# Factor Potentials

This document defines the computational semantics (potential functions) for each factor type defined in `../graph-ir/factor-nodes.md`.

## Reasoning Factor Potential
(all-premises-true → conditional probability p; any premise false → unconstrained)

## Instantiation Factor Potential
(deterministic implication)

## Mutex Constraint Potential
(penalizes all-true configuration)

## Equivalence Constraint Potential
(rewards agreement, penalizes disagreement)

## Retraction Factor Potential
(inverted conditional)
```

- [ ] **Step 2: Commit**

### Task 2.7: BP — inference.md

**Files:**
- Read: `docs/foundations/implementations/engines/bp-engine.md`
- Create: `docs/foundations/bp/inference.md`

- [ ] **Step 1: Write `bp/inference.md`**

Content:
- How BP runs on Graph IR (references `../graph-ir/` for structure)
- Factor graph construction from Graph IR
- Message computation (references `../theory/belief-propagation.md` for pure algorithm)
- Damping, convergence, scheduling
- Code pointers: `libs/inference/bp.py`, `libs/graph_ir/adapter.py`

- [ ] **Step 2: Commit**

### Task 2.8: BP — local-vs-global.md

**Files:**
- Read: `docs/foundations/interfaces/lifecycle.md` (inference sections)
- Create: `docs/foundations/bp/local-vs-global.md`

- [ ] **Step 1: Write `bp/local-vs-global.md`**

Content:
- Local inference: local canonical graph + author parameterization overlay → `gaia infer`
- Global inference: global canonical graph + GlobalInferenceState → server BP service
- What's shared (algorithm, potentials), what differs (graph scope, parameter source)
- Links to `../cli/local-inference.md` and `../lkm/global-inference.md` for product-specific details

- [ ] **Step 2: Commit all graph-ir + bp**

```bash
git add docs/foundations/graph-ir/ docs/foundations/bp/
git commit -m "docs: add graph-ir and bp layers — clean architectural separation"
```

---

## Chunk 3: CLI + LKM product surfaces

### Task 3.1: CLI — gaia-lang/spec.md

**Files:**
- Move: `docs/foundations/interfaces/language-spec.md` → `docs/foundations/cli/gaia-lang/spec.md`

- [ ] **Step 1: Move file**

```bash
git mv docs/foundations/interfaces/language-spec.md docs/foundations/cli/gaia-lang/spec.md
```

- [ ] **Step 2: Update internal cross-references**
- [ ] **Step 3: Commit**

### Task 3.2: CLI — gaia-lang/knowledge-types.md

**Files:**
- Read: `docs/foundations/gaia-concepts/knowledge-types.md`
- Create: `docs/foundations/cli/gaia-lang/knowledge-types.md`

- [ ] **Step 1: Write language-only knowledge-types.md**

Content rules:
- Keep: declaration type descriptions (#claim, #setting, #question, #action, #relation)
- Keep: surface syntax examples, `kind:` parameter
- Keep: proof state classification (theorem, assumption, hole, conjecture)
- Remove: "BP role" column/sections → link to `../../bp/potentials.md`
- Remove: "Graph IR mapping" → link to `../../graph-ir/factor-nodes.md`
- Remove: FactorNode schemas and compilation rules

- [ ] **Step 2: Commit**

### Task 3.3: CLI — gaia-lang/package-model.md

**Files:**
- Read: `docs/foundations/gaia-concepts/package-model.md`
- Create: `docs/foundations/cli/gaia-lang/package-model.md`

- [ ] **Step 1: Write authoring-level package-model.md**

Content rules:
- Keep: what is a Package (typst.toml + modules), Module (grouping), Chain (reasoning structure)
- Keep: how imports/exports work in the language
- Remove: identity layer details (raw/local canonical/global canonical) → link to `../../graph-ir/knowledge-nodes.md`
- Remove: storage schema details

- [ ] **Step 2: Commit**

### Task 3.4: CLI — lifecycle.md

**Files:**
- Read: `docs/foundations/interfaces/lifecycle.md` (§1 CLI Lifecycle)
- Read: `docs/foundations/implementations/entry-points/cli.md`
- Create: `docs/foundations/cli/lifecycle.md`

- [ ] **Step 1: Write `cli/lifecycle.md`**

Content: merge CLI lifecycle + CLI entry point into one document:
- `gaia init` → `gaia build` → [agent skills] → `gaia infer` → `gaia publish`
- Each command: input, output, what it does, what it does NOT do
- Agent skills (self-review, graph-construction) as optional steps
- `gaia show`, `gaia search`, `gaia clean`

- [ ] **Step 2: Commit**

### Task 3.5: CLI — compiler.md

**Files:**
- Read: `docs/foundations/implementations/engines/graph-ir-compiler.md`
- Create: `docs/foundations/cli/compiler.md`

- [ ] **Step 1: Write `cli/compiler.md`**

Content:
- Typst loading (typst query)
- Raw graph compilation (compile_v4_to_raw_graph)
- Local canonicalization (build_singleton_local_graph)
- Local parameterization (derive_local_parameterization)
- Code pointers to `libs/graph_ir/` and `libs/lang/`

- [ ] **Step 2: Commit**

### Task 3.6: CLI — local-inference.md + local-storage.md

**Files:**
- Create: `docs/foundations/cli/local-inference.md`
- Create: `docs/foundations/cli/local-storage.md`
- Reference: `implementations/engines/bp-engine.md` (local sections)
- Reference: `implementations/storage.md` (embedded DB sections)

- [ ] **Step 1: Write `cli/local-inference.md`**

Content: how `gaia infer` works locally — loads local canonical graph, applies parameterization overlay, runs BP, outputs beliefs.

- [ ] **Step 2: Write `cli/local-storage.md`**

Content: LanceDB + Kuzu embedded, `gaia publish --local` triple-write, local search via `gaia search`.

- [ ] **Step 3: Commit**

```bash
git add docs/foundations/cli/
git commit -m "docs(cli): add CLI product surface — gaia-lang, lifecycle, compiler, local inference"
```

### Task 3.7: LKM — overview.md

**Files:**
- Read: `docs/foundations/implementations/entry-points/server.md`
- Read: `docs/foundations/implementations/overview.md` (LKM parts)
- Create: `docs/foundations/lkm/overview.md`

- [ ] **Step 1: Write `lkm/overview.md`**

Content:
- LKM is a computational registry (not just storage)
- Write Side / Read Side architecture
- Write Side: Review Service → Storage → BP Service → Curation Service
- Read Side: Query Service for agent research
- FastAPI gateway, dependency injection
- The LKM never sees Gaia Lang — it operates on Graph IR

- [ ] **Step 2: Commit**

### Task 3.8: LKM — review-pipeline.md

**Files:**
- Read: `docs/foundations/implementations/engines/review-engine.md`
- Create: `docs/foundations/lkm/review-pipeline.md`

- [ ] **Step 1: Write `lkm/review-pipeline.md`**

Content: validation → canonicalization → agent review → gatekeeper. ReviewClient interface, mock review, pipeline integration.

- [ ] **Step 2: Commit**

### Task 3.9: LKM — remaining files

**Files:**
- Create: `docs/foundations/lkm/global-canonicalization.md` ← `implementations/engines/canonicalization-engine.md` (global part)
- Create: `docs/foundations/lkm/curation.md` ← `implementations/engines/curation-engine.md`
- Create: `docs/foundations/lkm/global-inference.md` ← bp-engine global parts + lifecycle LKM inference
- Create: `docs/foundations/lkm/pipeline.md` ← `implementations/entry-points/pipeline.md`
- Create: `docs/foundations/lkm/storage.md` ← `implementations/storage.md` (server parts)
- Move: `docs/foundations/interfaces/api.md` → `docs/foundations/lkm/api.md`
- Move: `docs/foundations/interfaces/agent-credit.md` → `docs/foundations/lkm/agent-credit.md`
- Create: `docs/foundations/lkm/lifecycle.md` ← `interfaces/lifecycle.md` (LKM sections)

- [ ] **Step 1: Write global-canonicalization.md** — server-side global node mapping, embedding + BM25 matching, CanonicalBinding
- [ ] **Step 2: Write curation.md** — 6-step curation pipeline, clustering, dedup, conflict detection
- [ ] **Step 3: Write global-inference.md** — server-side BP, GlobalInferenceState, periodic re-computation
- [ ] **Step 4: Write pipeline.md** — 7-stage batch pipeline, config, CLI invocation
- [ ] **Step 5: Write storage.md** — three-backend architecture, three-write atomicity, StorageManager
- [ ] **Step 6: Move api.md and agent-credit.md**

```bash
git mv docs/foundations/interfaces/api.md docs/foundations/lkm/api.md
git mv docs/foundations/interfaces/agent-credit.md docs/foundations/lkm/agent-credit.md
```

- [ ] **Step 7: Write lifecycle.md** — LKM lifecycle: review → curate → integrate

- [ ] **Step 8: Commit**

```bash
git add docs/foundations/lkm/
git commit -m "docs(lkm): add LKM product surface — review, curation, global inference, storage, API"
```

---

## Chunk 4: Cleanup + README + CLAUDE.md

### Task 4.1: Remove old directories

**Files:**
- Delete: `docs/foundations/gaia-concepts/` (all content redistributed)
- Delete: `docs/foundations/interfaces/` (all content redistributed)
- Delete: `docs/foundations/implementations/` (all content redistributed)

- [ ] **Step 1: Verify all content has been migrated**

Check that every file in the old directories has a corresponding new location.

- [ ] **Step 2: Remove old directories**

```bash
git rm -r docs/foundations/gaia-concepts/
git rm -r docs/foundations/interfaces/
git rm -r docs/foundations/implementations/
```

- [ ] **Step 3: Commit**

```bash
git commit -m "docs: remove old directory structure (content migrated to architecture layers)"
```

### Task 4.2: Merge foundations_archive into archive

**Files:**
- Move: `docs/foundations_archive/` → `docs/archive/foundations-v2/`

- [ ] **Step 1: Move**

```bash
git mv docs/foundations_archive docs/archive/foundations-v2
```

- [ ] **Step 2: Commit**

### Task 4.3: Archive completed plans and specs

**Files:**
- Move completed plans from `docs/plans/` and `docs/superpowers/plans/` to `docs/archive/plans/`
- Move completed specs from `docs/superpowers/specs/` to `docs/archive/specs/`

- [ ] **Step 1: Identify completed items**

Check git log for merged PRs corresponding to each plan. Plans for: factor-type-cleanup (merged), typst-dsl-v4 (merged), unified-graph-viewer (merged), multi-step-chains (merged), typst-graph-ir-compiler (merged).

- [ ] **Step 2: Move completed items to archive**
- [ ] **Step 3: Commit**

### Task 4.4: Archive top-level orphans

**Files:**
- Move: `docs/architecture-rebaseline.md` → `docs/archive/`
- Move: `docs/module-map.md` → `docs/archive/`
- Move: `docs/docs-restructure-proposal.md` → `docs/archive/`

- [ ] **Step 1: Move**

```bash
git mv docs/architecture-rebaseline.md docs/archive/
git mv docs/module-map.md docs/archive/
git mv docs/docs-restructure-proposal.md docs/archive/
```

- [ ] **Step 2: Commit**

### Task 4.5: Update foundations/README.md

**Files:**
- Rewrite: `docs/foundations/README.md`

- [ ] **Step 1: Write new README**

```markdown
# Foundations

Canonical reference docs for Gaia, organized by architectural layer.

## Theory — pure math, Gaia-independent (never changes)

- [Plausible Reasoning](theory/plausible-reasoning.md) — Jaynes, Cox theorem, probability as logic
- [Belief Propagation](theory/belief-propagation.md) — sum-product algorithm, convergence, damping
- [Scientific Ontology](theory/scientific-ontology.md) — scientific knowledge classification

## Rationale — design philosophy (rarely changes)

- [Product Scope](rationale/product-scope.md) — what Gaia is, why it exists
- [Architecture Overview](rationale/architecture-overview.md) — three-layer pipeline, CLI↔LKM contract
- [Domain Vocabulary](rationale/domain-vocabulary.md) — Knowledge, Chain, Module, Package
- [Type System Direction](rationale/type-system-direction.md) — Jaynes + Lean hybrid
- [Documentation Policy](rationale/documentation-policy.md) — doc maintenance rules

## Graph IR — the shared contract between CLI and LKM

- [Overview](graph-ir/overview.md) — purpose, three identity layers
- [Knowledge Nodes](graph-ir/knowledge-nodes.md) — Raw, LocalCanonical, GlobalCanonical schemas
- [Factor Nodes](graph-ir/factor-nodes.md) — FactorNode schema (single definition), types, compilation rules
- [Canonicalization](graph-ir/canonicalization.md) — local and global canonicalization
- [Parameterization](graph-ir/parameterization.md) — overlay schemas, graph hash

## BP — computation on Graph IR

- [Factor Potentials](bp/potentials.md) — potential functions for each factor type
- [Inference](bp/inference.md) — BP algorithm applied to Graph IR
- [Local vs Global](bp/local-vs-global.md) — CLI local inference vs LKM global inference

## CLI — local authoring and inference

- **Gaia Lang** (the CLI's frontend for Graph IR):
  - [Language Spec](cli/gaia-lang/spec.md) — Typst DSL syntax
  - [Knowledge Types](cli/gaia-lang/knowledge-types.md) — declaration types
  - [Package Model](cli/gaia-lang/package-model.md) — package/module/chain
- [Lifecycle](cli/lifecycle.md) — build → infer → publish
- [Compiler](cli/compiler.md) — Typst → Graph IR compilation
- [Local Inference](cli/local-inference.md) — `gaia infer` internals
- [Local Storage](cli/local-storage.md) — LanceDB + Kuzu embedded

## LKM — computational registry (server)

- [Overview](lkm/overview.md) — Write/Read side architecture
- [Review Pipeline](lkm/review-pipeline.md) — validation → review → gatekeeper
- [Global Canonicalization](lkm/global-canonicalization.md) — cross-package node mapping
- [Curation](lkm/curation.md) — clustering, dedup, conflict detection
- [Global Inference](lkm/global-inference.md) — server-side BP
- [Pipeline](lkm/pipeline.md) — 7-stage batch orchestration
- [Storage](lkm/storage.md) — three-backend architecture
- [API](lkm/api.md) — HTTP API contract
- [Agent Credit](lkm/agent-credit.md) — agent reliability tracking
- [Lifecycle](lkm/lifecycle.md) — review → curate → integrate
```

- [ ] **Step 2: Commit**

### Task 4.6: Update docs/README.md

**Files:**
- Rewrite: `docs/README.md`

- [ ] **Step 1: Update to reflect new structure**

Update the "Directory Map" table and entry points to match the new six-directory layout.

- [ ] **Step 2: Commit**

### Task 4.7: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update docs section**

Update the "Design Documents" section to reference the new structure:
```
docs/foundations/theory/       → Pure theory (Jaynes, BP algorithm)
docs/foundations/rationale/    → Design philosophy, product scope
docs/foundations/graph-ir/     → Graph IR structural contract (CLI↔LKM ABI)
docs/foundations/bp/           → BP computation semantics
docs/foundations/cli/          → CLI + Gaia Lang (local workflow)
docs/foundations/lkm/          → LKM server (review, curation, global inference)
```

- [ ] **Step 2: Commit**

### Task 4.8: Fix all cross-references

- [ ] **Step 1: Search for broken links**

```bash
grep -r 'gaia-concepts/' docs/foundations/ --include='*.md'
grep -r 'interfaces/' docs/foundations/ --include='*.md'
grep -r 'implementations/' docs/foundations/ --include='*.md'
```

- [ ] **Step 2: Fix all broken references to point to new paths**
- [ ] **Step 3: Final commit**

```bash
git add -A docs/
git commit -m "docs: fix all cross-references after restructure"
```

### Task 4.9: Remove .gitkeep files

- [ ] **Step 1: Clean up**

```bash
find docs/foundations -name '.gitkeep' -delete
git add -A
git commit -m "chore: remove .gitkeep scaffold files"
```
