# Graph IR Compiler

> **Status:** Current canonical

This document describes the Graph IR compilation pipeline that powers `gaia build`. For the Graph IR schema definitions, see [../graph-ir/overview.md](../graph-ir/overview.md).

## Overview

The compiler is a deterministic pipeline that transforms Typst source into Graph IR. It produces a factor graph intermediate representation with no LLM calls, no search, and no probability assignment.

```
Typst source  ->  Typst loading  ->  Raw graph  ->  Local canonical graph  ->  Local parameterization
```

Each step adds an identity layer. The raw graph preserves exact source traceability. The local canonical graph allows within-package merging. The local parameterization assigns default probability values.

## Step 1: Typst Loading

See `libs/lang/typst_loader.py`.

The Typst loader runs `typst query` to extract `gaia-node` figures from compiled Typst documents:

```bash
typst query --root <repo-root> lib.typ 'figure.where(kind: "gaia-node")'
typst query --root <repo-root> lib.typ 'figure.where(kind: "gaia-ext")'
```

This produces a dict with `nodes`, `factors`, `constraints`, `package`, and `version`.

## Step 2: Raw Graph Compilation

See `libs/graph_ir/typst_compiler.py:compile_v4_to_raw_graph()`.

The compiler processes the loader output into a `RawGraph`:

1. **Knowledge nodes**: Each non-external node becomes a `RawKnowledgeNode`. The v4 type map resolves `setting`, `question`, `claim`, `action`. Relation nodes (`contradiction`, `equivalence`) get their type from the constraint map.

2. **External nodes**: Nodes from `gaia-bibliography` become `RawKnowledgeNode` with `ext:package/node` IDs, preserving cross-package references.

3. **Reasoning factors**: Each `from:` parameter generates a `FactorNode` of type `infer` linking premise nodes to the conclusion.

4. **Constraint factors**: `#relation` declarations with `between:` generate `contradiction` or `equivalence` factors.

For factor type definitions: see [../graph-ir/factor-nodes.md](../graph-ir/factor-nodes.md).

## Step 3: Local Canonicalization

See `libs/graph_ir/build_utils.py:build_singleton_local_graph()`.

Currently implements singleton canonicalization: each raw node maps to exactly one `LocalCanonicalNode` with no merging. The raw-to-local mapping is recorded in a `CanonicalizationLogEntry` for auditability.

For the canonicalization identity model: see [../graph-ir/canonicalization.md](../graph-ir/canonicalization.md).

## Step 4: Local Parameterization

See `libs/graph_ir/build_utils.py:derive_local_parameterization_from_raw()`.

Derives the probability overlay for local BP:

- **Node priors**: From explicit metadata if present, otherwise defaults by type (`setting` = 1.0, everything else = 0.5).
- **Factor parameters**: `infer`, `abstraction`, and `reasoning` factors get `conditional_probability = 1.0` by default.

The parameterization is bound to a specific graph via `graph_hash`.

For the parameterization model: see [../graph-ir/parameterization.md](../graph-ir/parameterization.md).

## Node Identity

Three ID schemes, each deterministic:

| ID type | Format | Generation |
|---------|--------|------------|
| `raw_node_id` | `raw_{sha256[:16]}` | SHA-256 of `(package, version, module, name, type, kind, content, parameters)` |
| `local_canonical_id` | `lcn_{sha256[:16]}` | SHA-256 of the raw_node_id |
| `factor_id` | `f_{sha256[:16]}` | SHA-256 of `(kind, module, name[, suffix])` |

External nodes use the format `ext:{package}/{node}` instead of a hash-based ID.

For global canonical IDs (`gcn_`): see [../graph-ir/knowledge-nodes.md](../graph-ir/knowledge-nodes.md).

## Code Paths

| Component | File |
|-----------|------|
| Typst loader | `libs/lang/typst_loader.py` |
| Raw graph compiler | `libs/graph_ir/typst_compiler.py` |
| Local canonicalization | `libs/graph_ir/build_utils.py` |
| Graph IR models | `libs/graph_ir/models.py` |
| CLI integration | `libs/pipeline.py:pipeline_build()` |

## Current State

The compiler works for v3 and v4 Typst packages. The full pipeline (load, compile, canonicalize, parameterize) is exercised by `gaia build` and `gaia infer` CLI commands and by the server ingestion pipeline. Test coverage exists in `tests/libs/graph_ir/`.

## Target State

The Graph IR compiler is stable. No major changes are planned. The singleton local canonicalization may eventually support semantic merging within a package, but this is not prioritized.
