# Belief Propagation

> **Status:** Current canonical

## 1. Factor Graphs

A factor graph is a bipartite graph with two kinds of nodes:

- **Variable nodes**: unknown quantities with prior distributions. For binary variables: state true (1) or false (0).
- **Factor nodes**: constraints or relationships between variables. Each factor connects a subset of variables and encodes how they interact.

```
Variable nodes = propositions or unknown quantities
  prior  -> initial plausibility, in (epsilon, 1 - epsilon)
  belief -> posterior plausibility computed by BP

Factor nodes = constraints or reasoning links
  connects a subset of variables
  potential function encodes constraint semantics
```

The joint probability over all variables factorizes as:

```
P(x1, ..., xn | I) proportional to  prod_j phi_j(x_j) * prod_a psi_a(x_S_a)
```

where phi_j is the prior (unary factor) for variable j, and psi_a is the potential function for factor a over its connected variable subset S_a. Potentials are not probabilities -- they need not normalize. Only ratios matter.

## 2. Sum-Product Message Passing

Messages are 2-vectors `[p(x=0), p(x=1)]`, always normalized to sum to 1.

### Algorithm

```
Initialize: all messages = [0.5, 0.5] (uniform, MaxEnt)
            priors = {var_id: [1-prior, prior]}

Repeat (up to max_iterations):

  1. Compute all variable -> factor messages (exclude-self rule):
     msg(v -> f) = prior(v) * prod_{f' != f} msg(f' -> v)
     Then normalize.

  2. Compute all factor -> variable messages (marginalize):
     msg(f -> v) = sum_{other vars} potential(assignment) * prod_{v' != v} msg(v' -> f)
     Then normalize.

  3. Damp and normalize:
     msg = alpha * new_msg + (1 - alpha) * old_msg
     Default alpha = 0.5.

  4. Compute beliefs:
     b(v) = normalize(prior(v) * prod_f msg(f -> v))
     Output belief = b(v)[1], i.e., p(x=1).

  5. Check convergence:
     If max |new_belief - old_belief| < threshold: stop.
```

Key design points:

- **Bidirectional messages**: variable-to-factor and factor-to-variable. Backward inhibition (modus tollens) emerges naturally.
- **Exclude-self rule**: when variable v sends a message to factor f, it excludes f's own incoming message. This prevents circular self-reinforcement.
- **Synchronous schedule**: all new messages are computed from old messages, then swapped simultaneously. Factor ordering does not affect results.
- **2-vector normalization**: messages always sum to 1, preventing numerical decay in long chains.

### Correspondence with Jaynes's Rules

| BP operation | Jaynes rule |
|---|---|
| Joint = product of potentials and priors | Product rule |
| Message normalization [p(0) + p(1) = 1] | Sum rule |
| belief = prior * product of factor-to-var messages | Bayes' theorem (posterior proportional to prior * likelihood) |
| Variable-to-factor message (exclude-self) | Background information P(H\|X) excluding current factor |
| Factor-to-variable message (marginalize) | Likelihood P(D\|HX) marginalized over other variables |

On tree-structured graphs, BP is exact. On loopy graphs, it is an approximation.

## 3. Loopy BP and Convergence

Real-world factor graphs often have cycles. Loopy BP handles this by iterating message passing until beliefs stabilize.

**Damping** prevents oscillation on cyclic graphs:

```
msg_new = alpha * computed_msg + (1 - alpha) * msg_old
```

With alpha = 0.5 (default), each update moves halfway toward the new value. Damping trades convergence speed for stability.

Loopy BP minimizes the **Bethe free energy**, a variational approximation to the true free energy. On sparse graphs, this approximation is generally good. The system always produces a set of beliefs -- there is no "unsatisfiable" state. Incomplete information yields uncertain beliefs, not system failure.

**Cromwell's rule** is enforced at two points:

1. **At construction**: all priors and conditional probabilities are clamped to [epsilon, 1-epsilon], with epsilon = 10^-3.
2. **In potentials**: the leak parameter in noisy-AND factors is itself the Cromwell lower bound, ensuring no state combination has zero potential.

This prevents degenerate updates where a zero probability blocks all future evidence.

For Gaia's specific factor type potentials, see `../bp/potentials.md`.

## Source

- Jaynes, E.T. *Probability Theory: The Logic of Science* (2003)
- Pearl, J. *Probabilistic Reasoning in Intelligent Systems* (1988)
- Yedidia, Freeman, Weiss. "Understanding Belief Propagation and its Generalizations" (2003)
