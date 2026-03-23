# Local Inference

> **Status:** Current canonical

This document describes how `gaia infer` runs local belief propagation on a single package. For the BP algorithm and factor potential definitions, see the [BP layer](../bp/inference.md).

## Overview

`gaia infer` provides a local belief preview -- it runs BP on the package's local canonical graph with locally derived parameterization. The scope is strictly one package; it does not query or modify the global graph.

## How `gaia infer` Works

The command chains three pipeline functions:

1. **Build** (`pipeline_build()`) -- rebuild the package, producing a `LocalCanonicalGraph`.
2. **Review** (`pipeline_review(build, mock=True)`) -- derive priors and factor params via `MockReviewClient`, producing a `ReviewOutput` with `node_priors` and `factor_params`.
3. **Infer** (`pipeline_infer(build, review)`) -- adapt graph to factor graph, run BP, output beliefs.

## The Adapter Layer

See `libs/graph_ir/adapter.py`.

The adapter builds a `FactorGraph` from Graph IR by:

1. Mapping each `LocalCanonicalNode` ID to an integer variable ID.
2. Setting priors from the `LocalParameterization` (or `ReviewOutput.node_priors`).
3. Mapping each `FactorNode` to a factor dict with `premises`, `conclusions`, `probability`, and `edge_type`.
4. Applying Cromwell's rule: all priors and factor probabilities clamped to `[epsilon, 1 - epsilon]`.

The result is a `FactorGraph` ready for the BP engine.

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `damping` | 0.5 | Blending factor; 1.0 = fully replace, 0.0 = keep old |
| `max_iterations` | 50 | Upper bound on sweeps |
| `convergence_threshold` | 1e-6 | Stop when max belief change is below this |

These are the default BP parameters. The CLI does not currently expose them as command-line arguments.

## Output

Results are saved to `.gaia/infer/infer_result.json`, containing:

- Per-node beliefs (posterior probabilities)
- Convergence diagnostics (iterations run, converged status, max change at stop)
- Belief history traces for conflict detection

## Cross-Layer References

- **BP algorithm** (message passing, convergence, diagnostics): see [../bp/inference.md](../bp/inference.md)
- **Factor potentials** (how each factor type constrains beliefs): see [../bp/potentials.md](../bp/potentials.md)
- **Local vs global BP** (same algorithm, different scope): see [../bp/local-vs-global.md](../bp/local-vs-global.md)
- **Parameterization model** (structure vs. probabilities separation): see [../graph-ir/parameterization.md](../graph-ir/parameterization.md)

## Code Paths

| Component | File |
|-----------|------|
| Pipeline infer function | `libs/pipeline.py:pipeline_infer()` |
| Graph IR adapter | `libs/graph_ir/adapter.py` |
| Factor graph | `libs/inference/factor_graph.py` |
| BP algorithm | `libs/inference/bp.py:BeliefPropagation` |
| CLI command | `cli/main.py` (`infer` command) |
| Mock review client | `cli/llm_client.py:MockReviewClient` |

## Current State

Local inference is fully functional. The CLI always uses `MockReviewClient` (deterministic priors: `setting = 1.0`, others = `0.5`; factor conditional probability = `0.85`). Real LLM review is only available via the pipeline scripts.
