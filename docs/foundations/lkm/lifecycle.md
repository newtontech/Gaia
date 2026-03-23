# LKM Lifecycle

> **Status:** Current canonical

This document describes the server-side lifecycle after a package is published. For the local CLI lifecycle (init through publish), see [../cli/lifecycle.md](../cli/lifecycle.md).

## Overview

After a package is published via `gaia publish`, the LKM lifecycle takes over:

```
validate  ->  canonicalize  ->  review  ->  [rebuttal cycle]  ->  integrate  ->  curate  ->  global BP
```

## Stages

### Validate

The review engine re-compiles the raw graph from submitted source. Any mismatch with the submitted `raw_graph.json` is a blocking finding.

- **Input**: submitted package source + submitted `raw_graph.json`.
- **Output**: pass/fail. On mismatch, the submission is rejected.
- **What it does**: deterministic re-compilation for integrity verification.

### Canonicalize (global)

The canonicalization engine maps each `LocalCanonicalNode` to a `GlobalCanonicalNode`:

- **Input**: `LocalCanonicalGraph` + current global graph.
- **Output**: `CanonicalBinding` records + new/updated `GlobalCanonicalNode`s.
- **What it does**: embed each local node, search global graph for matches. For each local node: match to existing global node or create new one.

See [global-canonicalization.md](global-canonicalization.md) for details.

### Review

Independent peer review evaluates reasoning quality, duplicate detection, missing references, and conflict identification.

- **Input**: package source + raw graph + local canonical graph.
- **Output**: `ReviewOutput` with `node_priors`, `factor_params`, and per-chain assessments.
- **What it does**: produces probability judgments for BP parameterization.

See [review-pipeline.md](review-pipeline.md) for details.

### Rebuttal Cycle

If blocking findings exist, the author may accept revisions or write rebuttals. The cycle repeats up to 5 rounds. Unresolved after 5 rounds escalates to human review (`under_debate`).

> **Aspirational**: the full review -> rebuttal -> editor cycle is target architecture. Current implementation uses simplified automatic canonicalization at publish time.

### Integrate

Approved packages are merged into the global graph:

- **Input**: `CanonicalBinding` records + `ReviewOutput` + global factors.
- **Output**: updated global graph, refreshed `GlobalInferenceState`.
- **What it does**: finalizes bindings, creates/updates `GlobalCanonicalNode` entries, writes global `FactorNode` records (remapping premises/conclusion to `global_canonical_id`), refreshes inference state from review output, marks package `merged`.

### Curate

Offline graph maintenance by the curation engine:

- Similarity clustering (find near-duplicate global nodes)
- Deduplication (merge exact duplicates)
- Abstraction discovery (propose schema nodes)
- Contradiction discovery (detect conflicts across packages)
- Structure audit (graph health checks)
- Cleanup (execute approved merge/delete operations)

See [curation.md](curation.md) for the full 6-step pipeline.

### Global BP

The BP engine runs sum-product BP on the global canonical graph with registry-managed `GlobalInferenceState`. Same algorithm as local BP, different scope and parameterization source.

- **Input**: global canonical graph + `GlobalInferenceState`.
- **Output**: updated `GlobalInferenceState.node_beliefs` + `BeliefSnapshot` history.
- **Trigger**: after integration or curation completes.

See [global-inference.md](global-inference.md) for details. For the BP algorithm: see [../bp/inference.md](../bp/inference.md).

## Artifacts at Each Stage

| Stage | Key artifacts |
|---|---|
| Validate | pass/fail (blocking if mismatch) |
| Canonicalize | `CanonicalBinding` records, new/updated `GlobalCanonicalNode`s |
| Review | peer review report (findings + probability judgments) |
| Integrate | finalized bindings, updated global graph, refreshed `GlobalInferenceState` |
| Curate | clustering results, conflict reports, cleanup actions |
| Global BP | updated `GlobalInferenceState` (node beliefs), `BeliefSnapshot` history |

## Source

- `libs/global_graph/canonicalize.py` -- global canonicalization
- `libs/pipeline.py` -- review pipeline
- `libs/curation/` -- curation engine
- `libs/inference/bp.py` -- BP engine
- `libs/storage/manager.py` -- storage integration
