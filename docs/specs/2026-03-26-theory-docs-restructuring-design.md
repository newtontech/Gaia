# Theory Documents Restructuring — Design Spec

**Status:** Target design
**Date:** 2026-03-26
**Scope:** `docs/foundations/theory/` — 7 documents restructured into three logical layers

## Motivation

Current theory documents embed factor graphs and BP into the derivation chain as if they follow logically from Jaynes' theory:

```
Cox/Jaynes → MaxEnt → Factor Graph → Coarse Reasoning → BP → Ontology → Formalization
```

This is misleading. Jaynes' theory is self-contained — factor graphs and BP are one computational approximation for large-scale inference, not a theoretical necessity. The documents should reflect this separation.

Additionally, the "noisy-AND" / coarse reasoning operator needs reframing. Its essence is a strict conjunction (∧) followed by a plausible implication (↝), and its two parameters have clear semantic roles.

## Core Theoretical Insights

### 1. Minimal Ingredients: {¬, ∧, π}

To specify a joint distribution over binary propositions in Jaynes' framework, exactly three ingredients are needed — two propositional operations and one numerical assignment:

| Ingredient | Kind | Source | Role |
|------------|------|--------|------|
| ¬ (negation) | Propositional operation | Addition rule: P(¬A\|I) = 1 − P(A\|I) | Construct complement propositions |
| ∧ (conjunction) | Propositional operation | Multiplication rule: P(A∧B\|I) = P(A\|I)·P(B\|A,I) | Construct joint propositions |
| π ∈ [0,1] | Numerical assignment | Prior probability | Initial belief in each proposition |

Note: ¬ and ∧ are logical operations on propositions; π is a numerical parameter. "Minimal ingredients" means these are the minimum needed to fully specify any joint distribution — not that they are the same kind of object.

All other logical operators are derived:

- **→** (entailment): A→B ≡ P(A ∧ ¬B) = 0 — a compound proposition with prior zero
- **∨** (disjunction): A∨B ≡ ¬(¬A ∧ ¬B)
- **↔** (equivalence): P(A ∧ ¬B) = 0 ∧ P(¬A ∧ B) = 0
- **⊗** (contradiction): P(A ∧ B) = 0

Hard constraints are simply "certain compound propositions have prior zero." No new primitives needed.

### 2. Plausible Implication ↝ — The Only Parameterized Operator

**Definition:** A ↝ B with parameters (p₁, p₂):

| A | B | P(B\|A) |
|---|---|---------|
| 1 | 1 | p₁ |
| 1 | 0 | 1−p₁ |
| 0 | 0 | p₂ |
| 0 | 1 | 1−p₂ |

- **p₁** = inference reliability (how likely B is true when A is true)
- **p₂** = condition relevance (how likely B is false when A is false)

**Status in the theory:**

- **Theoretically reducible**: ↝ can be decomposed into a network of {¬, ∧, π} with auxiliary propositions bearing uncertain priors. After full decomposition, (p₁, p₂) disappear.
- **Practically essential**: The only tool for representing incompletely formalized reasoning. Formalization always starts with ↝ links.
- **Unique**: The only operator carrying conditional probability parameters. All other operators are deterministic or parameter-free.

**Degenerate cases:**
- p₁=1, p₂=1 → equivalence (A↔B)
- p₁=1, p₂ free → entailment-like (strict forward, contextual reverse)
- p₁ free, p₂=0.5 → "no opinion when A is false" (maximally uninformative reverse)

**Relationship to current single-parameter coarse reasoning operator:**
The current `03-coarse-reasoning.md` defines a single-parameter operator with potential ψ(0,\*)=1 ("no opinion when premise is false"). This corresponds to ↝ with p₂=0.5 (maximally uninformative when A is false), and p₁ as the single "reasoning strength" parameter. The new two-parameter ↝ generalizes this: p₂ ≠ 0.5 captures "condition relevance" — whether A being false actively affects B's plausibility. The concrete mapping from (p₁, p₂) to factor graph potential functions will be defined in doc 06 (Factor Graphs layer).

**Origin in Jaynes:** Jaynes' theory has no fundamental "soft link" between propositions. All logical relationships are strict. Apparent softness arises from uncertain priors on intermediate propositions. ↝ is a macro view of an unexpanded micro-structure of strict operators.

### 3. What Was Called "Noisy-AND"

The noisy-AND in multi-premise reasoning is actually two distinct components:

1. **Strict conjunction** ∧: All premises must hold — M = A₁ ∧ A₂ ∧ ... ∧ Aₖ
2. **Plausible implication** ↝: The joint premise plausibly implies the conclusion — M ↝ C with (p₁, p₂)

This decomposition clarifies the semantics: ∧ handles premise combination (deterministic), ↝ handles inference uncertainty (parameterized).

### 4. Completeness

**Claim:** {¬, ∧, π, ↝} with auxiliary variables can represent any joint probability distribution over binary variables.

**Proof sketch:**
1. Deterministic completeness: {¬, ∧} is functionally complete for Boolean functions (classical result).
2. Single-link probabilistic: ↝ with (p₁, p₂) parameterizes any binary conditional P(B|A) (2 free parameters, 2 parameters — exact match).
3. Multi-variable conditional: For P(C | A₁,...,Aₖ) with 2^k free parameters:
   - Construct 2^k pattern detectors Dᵢ using {¬, ∧}, each detecting exactly one input combination. **The Dᵢ are mutually exclusive** (exactly one is true for any input), which is critical for correctness.
   - Each Dᵢ ↝ Eᵢ with p₁ = P(C=1 | pattern i), p₂ = 1 (so Eᵢ is deterministically false when Dᵢ=0)
   - C = E₁ ∨ ... ∨ E_{2^k} (derived from ¬, ∧). Since exactly one Dᵢ=1 at a time, exactly one Eᵢ can be non-zero, so the disjunction correctly selects the active Eᵢ.
   - This step introduces O(2^k) auxiliary variables (Dᵢ and Eᵢ).
4. Any joint distribution decomposes into conditional probability tables (chain rule), each handled by step 3.

Worst case requires exponentially many auxiliaries, but scientific reasoning patterns (deduction, induction, abduction, etc.) need only a few.

### 5. Reasoning Strategies as Micro-Structures of ↝

Each reasoning strategy decomposes a ↝ link into a network of strict operators with uncertain intermediates. The effective (p₁, p₂) of the macro ↝ can be derived from Bayes' law on the micro-structure.

**Abduction — coarse vs fine view:**
- **Coarse (macro) view:** Observation ↝ Hypothesis — "this observation plausibly supports that hypothesis"
- **Fine (micro) decomposition:** H → O (hypothesis entails observable prediction) + O ↔ Obs (prediction matches observation)
- These are consistent: the micro-structure IS the internal mechanism; the macro ↝ IS the effective relationship. The direction of ↝ reflects the epistemic direction (from evidence to conclusion), while the micro-structure may contain strict entailments in either direction.

**Worked example — Abduction:**

Micro-structure: H → O (hypothesis H strictly entails prediction O), observed Obs = 1, with O ↔ Obs (equivalence).

Applying Bayes' law to derive the effective macro ↝ from Obs to H:
- P(H=1 | Obs=1) = P(Obs=1 | H=1)·π(H) / P(Obs=1)
- Given H=1: H→O forces O=1, and O↔Obs forces Obs=1, so P(Obs=1 | H=1) = 1
- Given H=0: O is not entailed, so P(Obs=1 | H=0) = π(O) (observation's base rate)
- Therefore: P(H=1 | Obs=1) = π(H) / [π(H) + π(O)·(1−π(H))]
- When Obs=0: O↔Obs forces O=0, and O=0 with H→O means H must be 0 (modus tollens)
- Therefore: P(H=0 | Obs=0) = 1

**Effective macro parameters:** p₁ = π(H) / [π(H) + π(O)(1−π(H))], **p₂ = 1** (observation false → hypothesis certainly false).

This demonstrates the derivation pattern: start with micro-structure, apply Bayes' law, extract effective (p₁, p₂). Doc 04 must provide analogous derivations for all seven strategies.

### 6. Factor Graphs and BP as Computational Approximation

Factor graphs and BP are NOT part of Jaynes' theory. They are one method for approximating exact Bayesian inference at scale:

- **Exact Jaynes inference**: Compute P(A|evidence, I) by summing over all configurations — exponential cost
- **Factor graph**: Encode the propositional network as a bipartite graph with potential functions
- **BP**: Approximate marginals via message-passing — polynomial per iteration

The documents must clearly position BP as "an efficient approximation" rather than "the theory."

## Document Structure (7 Documents, 3 Layers)

### Layer 1: Jaynes Theory (pure, no factor graphs or BP)

**01 — Plausible Reasoning** (minor revision of current 01)
- Cox theorem → probability as unique consistent formalism
- Weak syllogisms C1-C4
- Three rules: multiplication, addition, Bayes
- Positioning: foundation for everything that follows

**02 — MaxEnt Grounding** (minor revision of current 01a)
- From abstract principles to computable posteriors
- Hard constraints define feasible set, MaxEnt/Min-KL selects distribution
- Local factorization → exponential family
- Positioning: bridges Jaynes axioms to concrete computation

### Layer 2: Scientific Ontology (propositions and operators, no factor graphs or BP)

**03 — Propositional Operators** (REWRITE of current 02)
- **Primitives {¬, ∧, π}**: derived directly from Jaynes' addition/multiplication rules
- **Derived hard constraints**: →, ∨, ↔, ⊗ — all defined via ¬ and ∧, hard constraints as "compound proposition with π=0"
- **Three relation types** (structural definitions using derived operators):
  - Equivalence (↔): P(A ∧ ¬B) = 0 ∧ P(¬A ∧ B) = 0
  - Contradiction (⊗): P(A ∧ B) = 0
  - Negation (⊕): A and B are truth-complements — equivalence between A and ¬B
- **Plausible implication ↝** (featured introduction):
  - Definition with (p₁, p₂) conditional probability table
  - Semantic: p₁ = reliability, p₂ = relevance
  - Unique status: only parameterized operator
  - Reducibility: ↝ decomposes into {¬, ∧, π} micro-structure
  - Degenerate cases
  - Relationship to current single-parameter coarse reasoning operator
- **Completeness argument**: {¬, ∧, π, ↝} + auxiliary variables → any joint distribution
- All discussion in propositional/probabilistic language, NO factor graph terminology

**04 — Reasoning Strategies** (REWRITE, merging parts of current 03 + 05)
- **Four knowledge types**: claim, setting, question, template
- **Seven strategies as ↝ micro-structures**:
  - Each strategy: propositional network diagram (using proposition + operator language)
  - **Derive effective (p₁, p₂) under Bayes' law** for each micro-structure
  - Deduction: direct →, p₁=1
  - Abduction: Observation ↝ Hypothesis (note direction)
  - Induction: multiple instances with equivalence to observations → aggregate evidence
  - Analogy, extrapolation, reductio, elimination: similarly
- All in proposition-network language, NO factor graph terminology

**05 — Formalization Methodology** (revision of current 06)
- Step 1: Extract propositions from scientific text
- Step 2: Identify weakpoints, build "coarse propositional network" (contains ↝)
  - Terminology change: "粗命题网络" not "粗因子图"
- Step 3: Refine ↝ into strict operator micro-structures
- Objectivity argument: after sufficient formalization, ↝ disappears, belief determined by network topology
- NO factor graph terminology in this document

### Layer 3: Computational Methods (factor graphs + BP as large-scale approximation)

**06 — Factor Graphs** (NEW, drawing from parts of current 02 + 04)
- **Positioning**: computational representation of propositional networks, NOT the theory itself
- Mapping: propositions → variable nodes, operators → factor nodes
- Potential functions for each operator (¬, ∧, →, ↝, etc.)
- Hypergraph structure for multi-variable constraints
- Joint distribution factorization
- Relationship to exact Jaynes inference: factor graph encodes the same joint distribution

**07 — Belief Propagation** (revision of current 04)
- **Positioning**: approximate inference algorithm on factor graphs
- Sum-product message passing
- Message semantics for each operator type
- Correspondence to Jaynes rules (product rule ↔ multiplication, normalization ↔ addition, belief ↔ Bayes)
- Convergence: exact on trees, approximate (Bethe free energy) on loopy graphs
- Damping, synchronous updates
- Explicitly state: BP is an approximation, not the theory

## Derivation Chain (New)

```
Jaynes/Cox (probability is unique)
  → MaxEnt/Min-KL (posteriors from constraints)
    → Propositional primitives {¬, ∧, π} (from the two rules)
      → Derived operators (→, ∨, ↔, ⊗)
      → Plausible implication ↝ (macro view of incomplete formalization)
        → Reasoning strategies (↝ micro-structures + Bayes derivation)
          → Formalization methodology (scientific text → propositional network)
            ─ ─ ─ [computational boundary] ─ ─ ─
              → Factor graphs (propositional network → bipartite graph)
                → BP (approximate inference on factor graphs)
```

The dashed line marks the separation: above is theory and ontology (exact, always correct), below is computational method (approximate, one possible implementation).

## Mapping from Current Documents

| New | Source | Change Level |
|-----|--------|-------------|
| 01 plausible-reasoning | Current 01 | Minor — add theory stack positioning |
| 02 maxent-grounding | Current 01a | Medium — rewrite sections that use factor graph language (§5, §8) |
| 03 propositional-operators | Current 02 | **Full rewrite** — Jaynes language, not factor graph |
| 04 reasoning-strategies | Current 05 + parts of 03 | **Full rewrite** — add Bayes derivations, fix abduction direction |
| 05 formalization-methodology | Current 06 | Medium — remove factor graph terminology |
| 06 factor-graphs | Parts of current 02 + 04 | **New document** — mapping theory to computation |
| 07 belief-propagation | Current 04 | Medium — reposition as approximation |

## Downstream Impact

Files outside `theory/` that reference theory documents will need reference updates:
- `docs/foundations/bp/` — potentials.md, inference.md
- `docs/foundations/gaia-lang/` — spec.md, knowledge-types.md, package-model.md
- `docs/foundations/graph-ir/` — overview.md, graph-ir.md (reference only, no content change)
- `docs/foundations/rationale/` — architecture-overview.md, domain-vocabulary.md, product-scope.md
- `docs/foundations/README.md` — index update
- `docs/ideas/` — various idea docs

## Non-Goals

This restructuring is documentation-only. It does NOT change:
- **BP algorithm** — `docs/foundations/bp/` content is unchanged (only cross-references updated)
- **Graph IR schema** — `docs/foundations/graph-ir/` is a protected layer, no content changes
- **Gaia Language** — `docs/foundations/gaia-lang/` content unchanged (only terminology alignment)
- **Any code** — `libs/`, `services/`, `tests/` are untouched
- **Negation reasoning_type in Graph IR** — reductio and elimination strategies reference this, but adding it to Graph IR is a separate task (requires its own PR per change control rules)

## Migration Strategy

**Writing order** (respects dependency chain):
1. Doc 01 (minor edits) + Doc 02 (medium edits) — independent, can be parallel
2. Doc 03 (full rewrite) — depends on 01+02 for Jaynes foundation references
3. Doc 04 (full rewrite) — depends on 03 for operator definitions
4. Doc 05 (medium revision) — depends on 03+04 for terminology
5. Doc 06 (new) + Doc 07 (medium revision) — depend on 03 for what to map to computation
6. Downstream reference updates — after all theory docs are stable
7. Archive old documents, update `docs/foundations/README.md` index

**Filename handling:** Old filenames (e.g., `02-reasoning-factor-graph.md`) will be deleted and replaced. Cross-references in downstream files will be updated in step 6. No redirect files needed since this is all within one branch/PR.

## Validation Checklist

After writing all documents, verify:

1. **No factor graph / BP terminology in Layer 1 or Layer 2** (theory and ontology docs)
2. **↝ properly introduced** in doc 03 with (p₁, p₂) semantics, uniqueness, and reducibility
3. **Bayes-law derivations present** for each reasoning strategy's effective (p₁, p₂) in doc 04
4. **Abduction direction** is Observation ↝ Hypothesis throughout
5. **Completeness argument** present in doc 03
6. **Layer 3 explicitly positioned** as "computational approximation" not "the theory"
7. **Derivation chain consistent** across all 7 documents (each doc references what it depends on)
8. **No stale references** to old document names/sections in downstream files
9. **"粗命题网络" terminology** used instead of "粗因子图" in doc 05
10. **Minimal ingredients {¬, ∧, π}** — no operator presented as primitive that is derivable
11. **↝ relationship to old single-parameter model** explained in doc 03
12. **Abduction**: coarse view (O ↝ H) and fine decomposition (H→O + equivalence) both presented consistently
