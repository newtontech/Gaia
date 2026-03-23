# Factor Potentials

> **Status:** Current canonical

This document defines the computational semantics (potential functions) for each factor type. For structural definitions (schema, fields, compilation rules), see [../graph-ir/factor-nodes.md](../graph-ir/factor-nodes.md).

A factor potential is a function that takes a joint assignment of its connected variables and returns a non-negative weight encoding how compatible that assignment is with the constraint. Potentials are not probabilities -- they need not normalize. Only ratios matter.

## Reasoning Factor

Covers deduction (high p), induction (moderate p), and abstraction (transitional). All use the same potential shape; the chain type determines the expected range of the conditional probability parameter, not a different potential function.

### Current implementation -- conditional potential

| All premises true? | Conclusion value | Potential |
|---|---|---|
| Yes | 1 | `p` (conditional probability) |
| Yes | 0 | `1 - p` |
| No | any | `1.0` (unconstrained) |

When any premise is false, the current runtime imposes no constraint -- the factor is silent and the conclusion stays at its prior. This is the **current** local BP contract.

Parameterization input: `factor_parameters[factor_id].conditional_probability`

### Target model -- Noisy-AND + Leak

The current all-or-nothing gating violates Jaynes's fourth syllogism (weak denial): when premises are false, the conclusion should become less credible, not just return to its prior. The target model replaces the silent fallback with a leak probability:

| All premises true? | Conclusion value | Potential |
|---|---|---|
| Yes | 1 | `p` |
| Yes | 0 | `1 - p` |
| No | 1 | `epsilon` (leak -- near zero) |
| No | 0 | `1 - epsilon` |

**Leak probability** (Henrion 1989) encodes "the background probability that the conclusion holds even when premises are not all true." For Gaia's reasoning chains, premises are approximate necessary conditions for the conclusion, so leak should be minimal. Default: `epsilon = Cromwell lower bound (1e-3)`.

**Noisy-AND** is the dual of noisy-OR (Pearl 1988, Henrion 1989). Noisy-OR is for disjunctive causal models (any cause can produce the effect); noisy-AND is for conjunctive causal models (all conditions must hold). Full CPT requires 2^n parameters for n premises; noisy-AND + leak requires only 2: `p` and `epsilon`.

### Four syllogisms verification

With `pi_1=0.9, pi_2=0.8, p=0.9, epsilon=0.001`:

**Marginal probability of C**:
```
P(C=1) = p * pi_1 * pi_2 + epsilon * (1 - pi_1 * pi_2)
       = 0.9 * 0.72 + 0.001 * 0.28
       = 0.648
```

- **Syllogism 1** (modus ponens): P(C=1 | P1=1, P2=1) = p = 0.9
- **Syllogism 2** (weak confirmation): P(P1=1 | C=1) = 0.9997 > 0.9 (conclusion true raises premise belief)
- **Syllogism 3** (modus tollens): P(P1=1 | C=0) = 0.716 < 0.9 (conclusion false lowers premise belief)
- **Syllogism 4** (weak denial): P(C=1 | P1=0) = epsilon = 0.001 (premise false strongly lowers conclusion -- old model would give 0.5)

## Contradiction (mutex_constraint)

Generated from: `#relation(type: "contradiction", between: (<A>, <B>))`. The relation node R participates as `premises[0]`.

### Potential

| R (relation) | All constrained claims | Potential |
|---|---|---|
| 1 | All true | `epsilon` (near zero -- almost impossible) |
| any other combination | | `1.0` (unconstrained) |

Where `epsilon = CROMWELL_EPS (1e-3)`.

### BP behavior

When the relation is active (R has high belief) and two contradicted claims both have evidence, the factor sends inhibitory backward messages:

1. **Weaker-evidence-yields-first**: the claim with lower prior odds is suppressed more strongly by the same inhibitory message, because the likelihood ratio operates in odds space.
2. **Overwhelming evidence on both sides**: when both claims have very strong evidence, the factor lowers the relation node's own belief -- "questioning the contradiction itself." The likelihood ratio for R approaches `1 - b_A * b_B`, which goes to zero when both beliefs approach 1.
3. **Relation node as participant**: in the target design, R is a full BP participant (not a read-only gate), enabling bidirectional information flow. The current runtime already places R in `premises[0]`, permitting this behavior.

## Equivalence (equiv_constraint)

Generated from: `#relation(type: "equivalence", between: (<A>, <B>))`. The relation node R participates as `premises[0]`.

### Potential

| R (relation) | Claim A | Claim B | Potential |
|---|---|---|---|
| 1 | A = B (agree) | | `1 - epsilon` (high compatibility) |
| 1 | A != B (disagree) | | `epsilon` (low compatibility) |
| 0 | any | any | `1.0` (unconstrained) |

### BP behavior

- **Agreement strengthens relation**: when A and B have similar beliefs, the equivalence relation is confirmed and R's belief is pushed up.
- **Disagreement weakens relation**: when A and B diverge, BP lowers R's belief -- the system questions whether the equivalence holds.
- **N-ary decomposition**: for equivalence of 3+ nodes, decomposed into pairwise factors `(R, A, B)`, `(R, A, C)`, `(R, B, C)`, all sharing the same relation node R. This means disagreement between any pair weakens the overall equivalence.

## Retraction

Generated from: chains with `type: "retraction"`. Premises are evidence arguing against the conclusion.

### Potential

| All premises true? | Conclusion value | Potential |
|---|---|---|
| Yes | 1 | `1 - p` (suppressed) |
| Yes | 0 | `p` |
| No | any | `1.0` (unconstrained) |

Retraction is an inverted conditional: when retraction evidence is present, the conclusion is suppressed rather than supported. Absence of retraction evidence is not evidence of support -- the factor falls silent.

**Why silence is correct for retraction C4**: retraction evidence E not being present means this particular argument against C disappears. C's belief is then determined by its other supporting/opposing factors. "No evidence against" does not equal "evidence for."

## Instantiation

Generated from: elaboration of schema nodes (parameterized knowledge) into ground instances. Models the logical implication forall x.P(x) -> P(a).

### Potential

| Schema (premise) | Instance (conclusion) | Potential |
|---|---|---|
| 1 (forall x.P(x) holds) | 1 (P(a) holds) | `1.0` |
| 1 (forall x.P(x) holds) | 0 (P(a) fails) | `0.0` (contradiction) |
| 0 (forall x.P(x) fails) | 1 (P(a) holds) | `1.0` (instance can hold independently) |
| 0 (forall x.P(x) fails) | 0 (P(a) fails) | `1.0` |

This is a deterministic implication -- no parameterized `conditional_probability` is needed. It enforces:

- **Forward (deductive)**: schema believed -> instance must be believed.
- **Backward (counterexample)**: instance disbelieved -> schema must be disbelieved.
- **No reverse induction**: instance believed -> no constraint on schema (one example does not prove the universal).

### Inductive strengthening via BP message aggregation

```
V_schema ---- F_inst_1 ---- V_ground_1 (belief=0.9)
         ---- F_inst_2 ---- V_ground_2 (belief=0.85)
         ---- F_inst_3 ---- V_ground_3 (belief=0.1)   <-- counterexample
```

Each instantiation factor sends a backward message to V_schema. BP aggregates these at the shared schema node:

- V_ground_3 has low belief -> backward message through F_inst_3 pushes V_schema down.
- V_schema belief drops -> forward messages through F_inst_1, F_inst_2 weaken those instances.
- Net effect: one strong counterexample weakens the universal and all its instances.

Inductive reasoning emerges naturally from BP's message aggregation -- no special-case logic needed. This is the Popper/Jaynes view: a single counterexample strongly falsifies the universal, but any number of confirming instances only incrementally support it.

## Factor Type Summary

| Factor type | Current runtime name | Target BP family | Potential shape |
|---|---|---|---|
| `reasoning` | `infer` / `deduction` / `induction` | `reasoning_support` | Conditional (current) / Noisy-AND + leak (target) |
| `abstraction` | `abstraction` | `deterministic_entailment` (transitional) | Same as reasoning (current) |
| `instantiation` | `instantiation` | `deterministic_entailment` | Deterministic implication |
| `mutex_constraint` | `contradiction` / `relation_contradiction` | `constraint` | Penalty on all-true |
| `equiv_constraint` | `equivalence` / `relation_equivalence` | `constraint` | Agreement/disagreement |
| `retraction` | `retraction` | `reasoning_support` (inverted) | Inverted conditional |

## Current vs Target

| Aspect | Current | Target |
|---|---|---|
| Reasoning potential | All-or-nothing gating (silent when any premise false) | Noisy-AND + leak (suppresses conclusion when premises false) |
| Relation nodes | Gate variable (current runtime has `gate_var` mechanism) | Full BP participant (no gate; bidirectional messages) |
| Constraint strength | Fixed by relation node's current belief | Dynamic, updated by BP evidence |
| Abstraction | Separate factor type with infer-like kernel | Accepted abstractions lower to `deterministic_entailment` |

The core message-passing framework is unchanged between current and target. Only factor potential functions and the gate mechanism differ.

## Source

- `libs/inference/bp.py` -- `_evaluate_potential()`, `BeliefPropagation`
- `libs/inference/factor_graph.py` -- `FactorGraph`, `CROMWELL_EPS`
- `docs/foundations/theory/belief-propagation.md` -- pure BP algorithm
- [../graph-ir/factor-nodes.md](../graph-ir/factor-nodes.md) -- factor structure definitions
