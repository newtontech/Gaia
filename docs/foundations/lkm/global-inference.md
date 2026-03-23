# Global Inference

> **Status:** Current canonical

This document describes server-side belief propagation on the global canonical graph. For the BP algorithm details, see the [BP layer](../bp/inference.md). For factor potential definitions, see [potentials](../bp/potentials.md).

## Overview

Global inference runs the same sum-product loopy BP algorithm as local inference, but on a different scope:

| Aspect | Local BP (`gaia infer`) | Global BP (server) |
|--------|------------------------|--------------------|
| **Graph** | `LocalCanonicalGraph` (one package) | Global canonical graph (all packages) |
| **Parameterization** | `LocalParameterization` / `ReviewOutput` | `GlobalInferenceState` |
| **Trigger** | `gaia infer` CLI command | After integration or curation |
| **Output** | Local belief preview (`.gaia/infer/`) | Updated `GlobalInferenceState.node_beliefs` |

The algorithm, message schedule, and factor potentials are identical. See [../bp/local-vs-global.md](../bp/local-vs-global.md) for the comparison.

## GlobalInferenceState as Parameterization Source

`GlobalInferenceState` is a registry-managed singleton that stores all runtime parameters for the global graph:

- **`node_priors`** -- `dict[str, float]` keyed by `global_canonical_id`. Aggregated from review outputs of all integrated packages.
- **`factor_parameters`** -- `dict[str, FactorParams]` keyed by `factor_id`. Each contains `conditional_probability`.
- **`node_beliefs`** -- `dict[str, float]` keyed by `global_canonical_id`. Updated after each BP run.
- **`graph_hash`** -- integrity check binding the state to a specific graph structure.

Probability and structure are strictly separated: Graph IR stores only structure; `GlobalInferenceState` stores all runtime parameters. See [../graph-ir/parameterization.md](../graph-ir/parameterization.md).

## When Global BP Runs

Global BP is triggered after:

1. **Integration** -- a new package is merged into the global graph, adding new nodes and factors.
2. **Curation** -- the curation engine modifies the graph (merges duplicates, adds abstraction factors, removes stale entries).

In both cases, the graph structure has changed and beliefs need to be recomputed.

## Execution Flow

1. Load the global canonical graph (all `GlobalCanonicalNode`s and global `FactorNode`s) from storage.
2. Build a `FactorGraph` from the global nodes and factors, using `GlobalInferenceState.node_priors` and `factor_parameters`.
3. Run `BeliefPropagation` with standard parameters (damping=0.5, max_iterations=50, threshold=1e-6).
4. Write updated beliefs to `GlobalInferenceState.node_beliefs`.
5. Optionally write `BeliefSnapshot` history records.

## Code Paths

| Component | File |
|-----------|------|
| Global BP script | `scripts/pipeline/run_global_bp_db.py` |
| BP algorithm | `libs/inference/bp.py:BeliefPropagation` |
| Factor graph | `libs/inference/factor_graph.py:FactorGraph` |
| Global inference state | `libs/storage/models.py:GlobalInferenceState` |
| Storage manager | `libs/storage/manager.py:StorageManager` |

## Current State

Global BP is functional as a batch pipeline script (`run_global_bp_db.py`). It reads from and writes to LanceDB via `StorageManager`. The same `BeliefPropagation` class used for local inference is reused with no modifications.

## Target State

- Expose global BP as a server-side `BPService` triggered asynchronously after integration.
- Add incremental BP (re-run only on the subgraph affected by newly integrated packages).
