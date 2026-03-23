# Local vs Global Inference

> **Status:** Current canonical

The same `BeliefPropagation` class is used for both local and global inference. This document describes what is shared, what differs, and how each mode is configured.

## Local Inference (`gaia infer`)

**Scope**: one package.

Local inference runs on the **Local Canonical Graph** with a **LocalParameterization** overlay as the probability source.

- **Graph**: `graph_ir/local_canonical_graph.json` from `gaia build`.
- **Parameterization**: author-generated `LocalParameterization` overlay with node priors and factor conditional probabilities.
- **Output**: belief preview under `.gaia/infer/`. These are preview-only and not submitted during publish.
- **Purpose**: lets the author see how BP evaluates their reasoning structure before publishing. A low belief on a conclusion may indicate missing premises or weak reasoning.

Local inference does not query or modify the global graph. It is entirely package-local.

## Global Inference (server BP)

**Scope**: all ingested packages.

Global inference runs on the **Global Canonical Graph** with **GlobalInferenceState** as the probability source.

- **Graph**: the global canonical graph assembled from all canonicalized packages.
- **Parameterization**: registry-managed `GlobalInferenceState` with node priors, factor parameters, and persisted beliefs.
- **Output**: updated `GlobalInferenceState` with new node beliefs.
- **Purpose**: produces the system's best estimate of every proposition's credibility given all available evidence across all packages.

Global inference may be seeded from approved review-report judgments. The `BPService` on the server manages scheduling and execution.

## What's Shared

| Aspect | Shared? |
|---|---|
| Algorithm | Yes -- same `BeliefPropagation` class |
| Message schedule | Yes -- synchronous sum-product |
| Factor potentials | Yes -- same potential functions for all factor types |
| Damping, convergence, Cromwell's rule | Yes -- same parameters |
| Diagnostics | Yes -- `belief_history`, `direction_changes` available in both modes |

## What Differs

| Aspect | Local | Global |
|---|---|---|
| **Graph scope** | One package's local canonical graph | All packages' global canonical graph |
| **ID namespace** | `local_canonical_id` | `global_canonical_id` |
| **Parameterization source** | `LocalParameterization` (author-generated overlay) | `GlobalInferenceState` (registry-managed) |
| **Cross-package evidence** | None (isolated) | Yes (shared schema nodes, canonicalized claims) |
| **Persistence** | Ephemeral preview | Persisted `GlobalInferenceState` |
| **Trigger** | `gaia infer` CLI command | Server `BPService` (after integration or curation) |

## Parameterization Source Details

### Local

The `LocalParameterization` overlay is keyed by `local_canonical_id` for node priors and by `factor_id` for factor parameters. It references the local canonical graph by `graph_hash`. The overlay is generated locally (by agent skills or manually) and is not submitted during publish.

### Global

The `GlobalInferenceState` is keyed by `global_canonical_id` for both priors and beliefs, and by `factor_id` for factor parameters. It is maintained by the registry. After each global BP run, the resulting beliefs are persisted back into `GlobalInferenceState` for the next run.

## Related Documents

- [../graph-ir/parameterization.md](../graph-ir/parameterization.md) -- overlay schemas and integrity checks
- [inference.md](inference.md) -- how BP runs on Graph IR (algorithm details)
- [potentials.md](potentials.md) -- factor potential functions

## Source

- `libs/inference/bp.py` -- `BeliefPropagation` (shared class)
- `libs/graph_ir/adapter.py` -- builds `FactorGraph` from either local or global graph
- `libs/graph_ir/models.py` -- `LocalParameterization`
