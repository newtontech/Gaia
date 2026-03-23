# Global Canonicalization

> **Status:** Current canonical

Global canonicalization maps local canonical nodes (package-scoped) to global canonical nodes (cross-package). This enables the global knowledge graph to recognize that semantically equivalent propositions across packages refer to the same claim.

For the canonicalization identity model (raw, local canonical, global canonical): see [../graph-ir/canonicalization.md](../graph-ir/canonicalization.md).

## What Canonicalization Does

When a new package is ingested, each of its local nodes is either:

- **match_existing**: bound to an existing `GlobalCanonicalNode` that expresses the same proposition.
- **create_new**: a new `GlobalCanonicalNode` is created for this previously unseen proposition.

After node canonicalization, local factors are lifted to the global graph by replacing local canonical IDs with global canonical IDs, including resolution of `ext:` cross-package references.

## Pipeline

See `libs/global_graph/canonicalize.py:canonicalize_package()`.

```
Input:
  LocalCanonicalGraph  (from gaia build)
  LocalParameterization
  GlobalGraph  (current global state)

Steps:
  1. Filter to canonicalizable types (default: claims only)
  2. For each local node, find best match in global graph
  3. If match >= threshold -> bind to existing global node
  4. If no match -> create new global node
  5. Lift local factors to global IDs (resolve lcn_ and ext: references)

Output:
  CanonicalizationResult:
    bindings: list[CanonicalBinding]
    new_global_nodes: list[GlobalCanonicalNode]
    matched_global_nodes: list[str]
    global_factors: list[FactorNode]
    unresolved_cross_refs: list[str]
```

## Match Strategies

See `libs/global_graph/similarity.py:find_best_match()`.

### Embedding Similarity (primary)

When an `EmbeddingModel` is provided, the engine:
1. Batch-embeds the query content and all candidate contents.
2. Computes cosine similarity between the query embedding and each candidate.
3. Returns the best match above the threshold.

### TF-IDF Fallback

When no embedding model is available, the engine uses scikit-learn's `TfidfVectorizer` to compute pairwise cosine similarity. This is slower and less accurate but requires no external API.

### Match Threshold

The default threshold is `0.90` (see `canonicalize.py:MATCH_THRESHOLD`). A match must exceed this threshold to be accepted.

## Filtering Rules

Before similarity computation, candidates are filtered:

- **Type match required**: only candidates with the same `knowledge_type` are eligible.
- **Kind match for some types**: `question` and `action` types additionally require matching `kind`.
- **Relation types excluded**: `contradiction` and `equivalence` are package-local relations and never match across packages.

## Claims-Only Default

By default, only `claim` nodes are canonicalized. This is configurable via the `canonicalizable_types` parameter (typically set in `pipeline.toml`).

The rationale: claims are truth-apt propositions that participate in BP and benefit from cross-package identity. Settings define context; questions frame inquiry; actions describe procedures -- these are typically package-specific.

## Factor Lifting

After node canonicalization, local factors are rewritten with global IDs:

1. Build `lcn_ -> gcn_` mapping from bindings.
2. Build `ext: -> gcn_` mapping from global node metadata (`source_knowledge_names`).
3. For each local factor, resolve all premise, context, and conclusion IDs.
4. Factors with unresolved references are dropped (logged in `unresolved_cross_refs`).

For factor node schema: see [../graph-ir/factor-nodes.md](../graph-ir/factor-nodes.md).

## Code Paths

| Component | File |
|-----------|------|
| Canonicalization entry | `libs/global_graph/canonicalize.py:canonicalize_package()` |
| Similarity matching | `libs/global_graph/similarity.py:find_best_match()` |
| Global node model | `libs/storage/models.py:GlobalCanonicalNode` |
| Canonical binding model | `libs/storage/models.py:CanonicalBinding` |
| Pipeline integration | `scripts/pipeline/canonicalize_global.py` |

## Current State

The canonicalization engine works for claims-only default mode with both embedding and TF-IDF similarity. Factor lifting resolves both local and cross-package references. The engine is exercised by the server ingestion pipeline and tested in `tests/libs/global_graph/`.

## Target State

The canonicalization engine is stable. Potential minor improvements include smarter representative content selection when multiple local nodes merge into one global node, and caching of embeddings to avoid recomputation.
