# BP Inference on Graph IR

> **Status:** Current canonical

This document describes how belief propagation runs on Graph IR. For the pure BP algorithm (sum-product message passing, damping, convergence), see [../theory/belief-propagation.md](../theory/belief-propagation.md). For factor potential functions, see [potentials.md](potentials.md). For the distinction between local and global inference, see [local-vs-global.md](local-vs-global.md).

## Factor Graph Construction

See `libs/inference/factor_graph.py`.

BP does not run on raw Graph IR. It runs on a `FactorGraph` constructed from the local canonical graph (or global canonical graph) plus a parameterization overlay.

### FactorGraph structure

`FactorGraph` is a bipartite graph between variable nodes and factor nodes:

- **Variables**: `dict[int, float]` mapping integer node ID to prior belief `p(x=1)`. Each knowledge node becomes a binary variable.
- **Factors**: `list[dict]` where each factor has `edge_id`, `premises: list[int]`, `conclusions: list[int]`, `probability: float`, `edge_type: str`, and optional `gate_var: int`.

### Adapter layer

The adapter (`libs/graph_ir/adapter.py`) builds a `FactorGraph` from Graph IR:

1. Map `LocalCanonicalNode` IDs to integer variable IDs.
2. Map each `FactorNode` to a factor dict with integer-keyed premises and conclusions.
3. Look up parameterization: node priors from the overlay, factor conditional probabilities from the overlay.
4. Apply Cromwell clamping to all priors and probabilities.

### Cromwell's rule

All priors and factor probabilities are clamped to `[epsilon, 1 - epsilon]` where `epsilon = 1e-3` (see `factor_graph.py:CROMWELL_EPS`). This prevents degenerate zero-partition states during BP where a zero probability would block all future evidence updates.

## Message Computation

Messages are 2-vectors `[p(x=0), p(x=1)]`, always normalized to sum to 1. This is the `Msg` type (NumPy `NDArray[float64]` of shape `(2,)`).

### Synchronous schedule

Each iteration:

1. **Variable-to-factor messages**: for each `(variable, factor)` edge, the message is the variable's prior times the product of all incoming factor-to-var messages except from this factor (exclude-self rule).

2. **Factor-to-variable messages**: for each `(factor, variable)` edge, marginalize over all 2^(n-1) assignments of other variables, weighting by factor potential and incoming var-to-factor messages.

3. **Damp and normalize**: new messages are blended with old via `damping * new + (1 - damping) * old`, then normalized.

4. **Compute beliefs**: each variable's belief is its prior times the product of all incoming factor-to-var messages, normalized.

5. **Check convergence**: if the maximum absolute change in any belief is below the threshold, stop.

### Read-only gate variables

Relation factors support an optional `gate_var` -- a variable whose current belief is used as the effective constraint strength `p`, but which does not receive messages from the factor. This prevents feedback loops between the relation node and its constraint in the current runtime. In the target design, gate variables are removed and relation nodes become full BP participants.

## Parameters

| Parameter | Default | Description |
|---|---|---|
| `damping` | 0.5 | Blending factor for message updates. 1.0 = fully replace, 0.0 = keep old. |
| `max_iterations` | 50 | Upper bound on message passing sweeps. |
| `convergence_threshold` | 1e-6 | Stop when max belief change is below this. |

## Diagnostics

`run_with_diagnostics()` returns a `BPDiagnostics` object containing:

- **`iterations_run`**: how many iterations were executed.
- **`converged`**: whether the convergence threshold was met.
- **`max_change_at_stop`**: the maximum belief change in the final iteration.
- **`belief_history: dict[int, list[float]]`**: per-variable belief trace across iterations. Useful for visualization and debugging.
- **`direction_changes: dict[int, int]`**: count of sign reversals in belief deltas per variable. A high count indicates oscillation, which is a signal for conflict detection -- the variable is receiving contradictory evidence from different parts of the graph.

## Schema/Ground Interaction

### Local package BP

Within a single package, schema and ground nodes interact through binary instantiation factors:

```
V_schema
    |-- F_inst_1: premises=[V_schema], conclusion=V_ground_1
    |-- F_inst_2: premises=[V_schema], conclusion=V_ground_2
```

BP computes beliefs for all local canonical nodes simultaneously. Forward messages flow schema -> instance (deductive support). Backward messages flow instance -> schema (inductive evidence). See [potentials.md](potentials.md) for the instantiation potential function.

### Global graph BP

After packages are published, schema nodes from different packages may share one global canonical node. Evidence for one package's ground instance indirectly supports ground instances from other packages through the shared schema:

```
Package A:  F_inst_a: premises=[V_schema], conclusion=V_ground_a
Package B:  F_inst_b: premises=[V_schema], conclusion=V_ground_b
                               ^ shared schema node
```

This is cross-package evidence propagation via shared abstract knowledge.

## Source

- `libs/inference/bp.py` -- `BeliefPropagation`, `run_with_diagnostics()`
- `libs/inference/factor_graph.py` -- `FactorGraph`, `CROMWELL_EPS`
- `libs/graph_ir/adapter.py` -- builds `FactorGraph` from Graph IR
