# Package Model

> **Status:** Current canonical

This document defines the structural layers of a Gaia knowledge container as they appear in the authoring surface: Package, Module, Knowledge, and Chain.

## Package

A Package is a complete, versioned knowledge container. It is analogous to a git repository or a published paper.

- **Identity**: `(package_id, version)` -- semver string (e.g., `"4.0.0"`).
- **Authored form**: a Typst project directory with `typst.toml` manifest, `lib.typ` entrypoint, and module files.
- **Status values**: `preparing` | `submitted` | `merged` | `rejected`.

A package is the unit of submission, review, and integration. Packages are ingested atomically -- all modules succeed or none do.

## Module

A Module is a logical grouping within a package. In the authoring surface, each `.typ` file (other than `lib.typ` and `gaia.typ`) is implicitly a module.

- **Identity**: `module_id` scoped to the package.
- **Roles**: `reasoning` | `setting` | `motivation` | `follow_up_question` | `other`.
- **Contains**: references to knowledge objects and chains (`chain_ids[]`, `export_ids[]`).
- **Imports**: cross-module dependencies via `ImportRef(knowledge_id, version, strength)`.

Modules exist for organizational clarity. They do not create independent inference boundaries -- all knowledge within a package participates in the same factor graph.

## Knowledge

A Knowledge object is a versioned proposition -- the fundamental unit of the knowledge graph.

- **Identity**: `(knowledge_id, version)`. The `knowledge_id` is scoped to the package; the version is an integer that increments with edits.
- **Type**: `claim | question | setting | action | contradiction | equivalence` (see [knowledge-types.md](knowledge-types.md)).
- **Content**: the proposition text.
- **Prior**: author-assigned plausibility in (epsilon, 1 - epsilon), required for inference-bearing types.
- **Parameters**: optional list of `Parameter(name, constraint)` for schema/universal nodes.
- **Keywords**: extracted terms for search.

## Chain

A Chain is a display-layer multi-step reasoning structure. Each chain represents one complete reasoning unit from premises to conclusion.

- **Identity**: `chain_id` scoped to the module.
- **Type**: `deduction | induction | abstraction | contradiction | retraction | equivalence`.
- **Steps**: ordered list of `ChainStep(step_index, premises[], reasoning, conclusion)`. Each step connects premise `KnowledgeRef`s to a conclusion `KnowledgeRef`.
- **Factor mapping**: each Chain produces one factor in the Graph IR. The chain preserves the author's multi-step argument; the factor collapses it into a single constraint.

## Package Lifecycle (Authoring View)

```
authored   -> author writes Typst source
built      -> gaia build: deterministic lowering to Graph IR
inferred   -> gaia infer: local BP preview with local parameterization
published  -> gaia publish: submitted to registry for peer review
```

For what happens after publish, see [../../lkm/lifecycle.md](../../lkm/lifecycle.md).

## Relationship Between Layers

```
Package (1)
  contains -> Module (1..n)
    contains -> Knowledge (0..n)
    contains -> Chain (0..n)
      references -> Knowledge via KnowledgeRef (premises, conclusions)
```

## Cross-Layer References

- **Node identity layers** (raw, local canonical, global canonical): see [../../graph-ir/knowledge-nodes.md](../../graph-ir/knowledge-nodes.md)
- **Graph IR representation** of packages: see [../../graph-ir/overview.md](../../graph-ir/overview.md)
- **Storage schema** for persisted models: see [../../lkm/storage.md](../../lkm/storage.md)

## Source

- `libs/storage/models.py` -- `Package`, `Module`, `Knowledge`, `Chain`, `ChainStep` models
