# Plausible Reasoning — Jaynes Framework

> **Status:** Current canonical
>
> This document describes pure mathematical foundations. For how Gaia applies these, see `../rationale/product-scope.md`.

## 1. Jaynes's Programme: Probability as Logic

Jaynes (*Probability Theory: The Logic of Science*, 2003) defines probability not as frequency but as **degree of plausibility**: P(A|X) is how believable proposition A is given information X. Every probability is conditional. Change the information, change the probability -- this is logical necessity, not subjective preference.

### Cox's Theorem

Cox (1946) proved that any system of plausible reasoning satisfying three requirements is isomorphic to probability theory:

1. **Real-valued**: plausibility is represented by real numbers
2. **Common-sense consistent**: evidence supporting A continuously increases A's plausibility
3. **Consistent**: equivalent reasoning paths yield the same answer; no information is ignored

From these, three rules are **derived** (not assumed):

- **Product rule**: P(AB|X) = P(A|BX) * P(B|X)
- **Sum rule**: P(A|X) + P(not-A|X) = 1
- **Bayes' theorem**: P(H|DX) = P(D|HX) * P(H|X) / P(D|X)

Probability theory is not one method among many -- it is the only consistent system.

### MaxEnt and Cromwell's Rule

Two principles constrain how beliefs are initialized:

- **Maximum entropy**: when information is incomplete, choose the distribution with maximum entropy subject to known constraints. The default prior is 0.5 (maximum ignorance for a binary variable).
- **Cromwell's rule**: never assign probability 0 or 1 to an empirical proposition. If P(H) = 0, no amount of evidence can update it. All priors and probabilities should be clamped to the open interval (epsilon, 1 - epsilon).

## 2. Jaynes's Robot

Jaynes frames his entire programme as designing a **robot** that:

- receives propositions and evidence, outputs plausibilities
- follows the three rules strictly (Cox's theorem)
- has no intuition or bias -- only structure and probabilities
- satisfies consistency -- the same question asked differently yields the same answer

This robot paradigm motivates systems like Gaia. A factor graph serves as the robot's reasoning engine. The content of propositions is opaque to the engine -- it only sees graph structure and probability parameters. Semantic understanding is handled by humans and LLMs at the content layer.

This motivates a two-layer architecture:

| Layer | Role | Handled by |
|---|---|---|
| **Content layer** | Proposition semantics -- what claims mean | Humans + LLMs |
| **Graph structure layer** | Reasoning topology -- how claims relate | BP algorithm (automatic) |

## 3. Curry-Howard Analogy

Just as functional programming languages (Haskell, Lean) are grounded in the Curry-Howard correspondence between proofs and programs, there is an aspiration to extend this from deductive certainty to plausible belief. This is an open research direction, not an established theorem -- the full Curry-Howard correspondence for probabilistic computation remains an active area of study.

The key architectural borrowing from Lean is **construction/verification separation**: construction agents may hallucinate or err, while BP independently verifies belief consistency. A wrong construction does not corrupt the system -- verification catches it.

## 4. Contradiction as First-Class Citizen

In classical logic, contradiction triggers the explosion principle (ex falso quodlibet) -- from a contradiction, anything follows. In Jaynes's framework, contradiction is **evidence of conflict**: P(A and B | I) is near 0, meaning A and B cannot both be true. The system does not crash; it adjusts beliefs.

The weaker-evidence-yields-first principle emerges automatically: when a contradiction factor penalizes the all-true configuration, backward messages suppress all premises, but premises with lower prior are suppressed more (their prior odds are smaller, so the same likelihood ratio has a larger effect in odds space).

Science advances through contradictions between experiments, theories, and predictions. Treating contradiction as a first-class reasoning primitive -- rather than a data quality problem -- aligns formal systems with how scientific knowledge actually evolves.

## Source

- Jaynes, E.T. *Probability Theory: The Logic of Science* (2003)
- Cox, R.T. "Probability, Frequency and Reasonable Expectation" (1946)
- Polya, G. *Mathematics and Plausible Reasoning* (1954)
