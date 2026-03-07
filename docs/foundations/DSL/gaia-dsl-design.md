# Gaia DSL Design

## Purpose

This document defines the language design of Gaia — a probabilistic functional programming language for knowledge representation and epistemic inference.

It is the top-level language blueprint. The V1/V2/V3 documents define specific layer implementations of this language:

- **V1** — FP language core (types, values, functions, expressions, modules)
- **V2** — Package management system (Gaia.toml, dependency resolution, registry, publish)
- **V3** — Probabilistic layer (prior, posterior, belief propagation)

## Design Approach

**Layered language kernel.** Gaia follows the same architecture as Church (extending Scheme) and Pyro (extending Python): a deterministic host language with a probabilistic layer on top. Each version layer adds primitives to the kernel:

```
V1 kernel:   Knowledge, Action, Expression, Module      (FP: values, functions, composition, modules)
V2 extension: Package, Dependency, Registry              (package management: Cargo/Cabal)
V3 extension: Prior, Posterior, Strength, Propagate       (probability: Church's sample/observe)
```

**Formality level.** Semi-formal — natural language + pseudo-BNF + semantic rule tables.

**Primary user.** AI agents. The language prioritizes machine-parsability, unambiguous rules, and ease of automatic generation and validation.

**Abstract vs concrete syntax.** This document defines the abstract syntax (language concepts). The concrete syntax (serialization format, likely YAML) is defined separately.

## Type System

### Design principles

- **Subtyping**: the type system is a tree with inheritance. Rules defined at any level apply to all subtypes.
- **Extensible**: new subtypes can be added without changing existing rules.
- **Knowledge as root type**: all objects in the language are knowledge.

### Type hierarchy

```
Knowledge                          (root type)
├── Claim                          (assertive knowledge — truth-apt)
│   ├── ...                        (future: Observation, Conjecture, Theorem...)
├── Question                       (interrogative knowledge — not truth-apt)
│   ├── ...
├── Setting                        (contextual knowledge — conditions, definitions, environments)
│   ├── ...                        (future: Definition, Assumption, Environment...)
└── Action                         (procedural knowledge — process descriptions)
    ├── Reasoning                  (natural language reasoning — inherently probabilistic)
    ├── ToolCall                   (executable in external language — deterministic given env)
    │   ├── ...                    (future: PythonCall, LeanProof...)
    └── ...
```

### Base types

**Claim** — assertive, truth-apt knowledge. Statements, results, conclusions.

**Question** — interrogative knowledge. Not truth-apt (has no truth value). Inquiries, open problems.

**Setting** — contextual knowledge. Definitions, assumptions, execution environments, experimental conditions. Establishes the background under which reasoning is interpreted.

**Action** — procedural knowledge. Describes a process, method, or tool. Functions in the language — can be "called" in expressions. Two subtypes:

- **Reasoning**: natural language method description. Executed by AI agents reading and applying the described method. Inherently probabilistic — NL reasoning has error space.
- **ToolCall**: executable code in an external language (Python, Lean, etc.). Requires an execution environment (Setting). Deterministic given correct environment — uncertainty comes from the environment/inputs, not the code itself.

### Subtyping rules

- Any rule defined for a parent type automatically applies to all subtypes.
- Example: "Claim participates in BP" → Observation (future subtype of Claim) also participates in BP.
- Adding a new subtype never requires updating existing rules.

### Key type distinctions

| Property | Claim | Question | Setting | Action |
|----------|-------|----------|---------|--------|
| Truth-apt? | Yes | **No** | Yes (stipulative) | No (procedural) |
| Participates in BP? | Yes | No | Yes | Via application |
| Can be "called"? | No | No | No | **Yes** |
| Requires environment? | No | No | No | ToolCall: **Yes** |

## Value and Variable

### Knowledge as value

A **value** is an instance of a type. In Gaia, every value is a knowledge object.

```
claim drag_explains_falling :=
  "Air resistance, not mass, explains differential fall rates"
```

- `drag_explains_falling` is the **variable** (name bound to the value)
- `Claim` is the **type**
- The quoted content is the **value** (an instance of Claim)

### Immutability

Values are immutable and referentially transparent. A name always refers to the same content. There is no assignment or mutable state in the deterministic layer (V1).

### Probabilistic state

Each value carries probabilistic state in the V3 layer:

```
Value = Deterministic part (V1, immutable): type, content, metadata
      + Probabilistic part (V3, computed):   prior (input), posterior (output of BP)
```

```
claim drag_explains_falling (prior = 0.8) :=
  "Air resistance, not mass, explains differential fall rates"
-- After BP: posterior = 0.85
```

### No private scope

**All knowledge is globally visible.** This is a fundamental difference from code languages:

| | Code (Rust) | Knowledge (Gaia) |
|---|---|---|
| Private | External cannot see | **Does not exist** — all knowledge is visible |
| Non-exported | Crate-internal | In LKM, visible, referenceable, but **does not participate in BP** |
| Exported | Globally available | Registered in LKM, **participates in BP** |

Knowledge is objective — there is no reason to hide intermediate reasoning steps. The only distinction is whether knowledge enters the probabilistic inference layer.

### Naming and identity

**Local (authoring):** human-readable names. No global ID needed.

```
-- Within a module: just the name
drag_explains_falling

-- Within a package, cross-module: module.name
reasoning.drag_explains_falling

-- Cross-package: package.module.name
physics.reasoning.drag_explains_falling
```

**Global (LKM):** identity is assigned at publish time by the registry (V2), not at creation time. Identity is content-driven, not ownership-driven.

**Identity and provenance are separated:**

| Aspect | What it is | Who manages it |
|--------|-----------|---------------|
| Local name | Human-readable variable name | Author |
| Global identity | Content-driven ID in LKM | Registry (V2) |
| Provenance | Which packages contributed this knowledge | Metadata |

This preserves objectivity: if two packages independently derive the same conclusion, the registry merges them into one global identity with two provenance records. Knowledge does not "belong to" any package.

## Function

### Action as function

Action is a Knowledge type that has function semantics. Like Haskell, functions are values — an Action is a piece of knowledge that can also be "called."

**Definition:**

```
action contrastive_analysis(env: Setting, hyp: Claim) -> Claim :=
  "Contrast behavior under two different conditions to test the hypothesis"
```

**Application (traditional call syntax):**

```
conclusion = contrastive_analysis(vacuum_setting, premise)
```

### Functions are not pure

Unlike Haskell, Gaia functions are **not pure**. Natural language reasoning has inherent uncertainty — an AI agent executing a Reasoning action can make mistakes.

```
Haskell:  f(a, b) -> c     -- deterministic, always correct
Gaia:     f(a, b) -> c     -- probabilistic, may be wrong
```

Each function application carries its own prior/posterior:

```
action contrastive_analysis(env: Setting, hyp: Claim) -> Claim :=
  "Contrast behavior under two different conditions"

-- Application with probabilistic annotation
premise => contrastive_analysis(vacuum_setting, premise) (prior = 0.9) => conclusion
-- After BP: posterior may change based on evidence
```

### Action subtypes

**Reasoning** — natural language method description:

```
action contrastive_analysis(env: Setting, hyp: Claim) -> Claim :=
  "Contrast behavior under two different conditions"
-- Inherently probabilistic (prior typically < 1.0)
```

**ToolCall** — executable code requiring an execution environment:

```
action compute_drag(env: Setting) -> Claim
  [tool = "python", requires = PythonEnv] :=
  """
  import physics
  result = physics.drag_coefficient(env.parameters)
  return f"Drag coefficient is {result}"
  """
-- Deterministic given correct env (prior ≈ 1.0)
-- Uncertainty comes from Setting's prior, not from the code
```

### Anonymous functions (lambdas)

Inline reasoning text in an expression — a one-off reasoning step without a reusable Action definition:

```
premise => "Obviously follows from the definition" => conclusion
```

## Expression

### Definition

An expression is a linear pipeline of knowledge and function applications, connected by `=>`:

```
premise
  => contrastive_analysis(vacuum_setting, premise) (prior = 0.9)
  => conclusion
```

### Syntax

```
=>   for chain flow (knowledge flows through reasoning steps)
->   for type signatures (input types to output types)
```

### Forms

**Named function application:**

```
premise => contrastive_analysis(vacuum_setting, premise) => conclusion
```

**Anonymous lambda:**

```
premise => "Simple deductive step" => conclusion
```

**Multi-step pipeline:**

```
premise
  => contrastive_analysis(vacuum_setting, premise)
  => intermediate
  => further_analysis(intermediate, new_evidence)
  => final_conclusion
```

### Design rules

| Rule | Decision |
|------|----------|
| Structure | Linear pipeline |
| Branching | Use multiple expressions, not explicit branch syntax |
| Loops | Not allowed (circular reasoning = logical error) |
| Per module | Multiple expressions supported |
| Well-formedness | Flexible — no strict alternation rules |

### Branching via multiple expressions

Instead of explicit branch syntax, branching is expressed as multiple expressions sharing input:

```
-- Two conclusions from the same premise (no branch syntax needed)
premise => analysis_a(premise) => conclusion_a
premise => analysis_b(premise) => conclusion_b

-- Synthesis of multiple results
conclusion_a => synthesis(conclusion_a, conclusion_b) => final
```

## Module

### Definition

A module is an organizational unit that groups expressions, manages imports/exports, and provides scoping.

```
module reasoning_module:
  import vacuum_setting from env_module (strong)
  import question from motivation_module (weak)

  -- Expression 1
  question => contrastive_analysis(vacuum_setting, question) => conclusion

  -- Expression 2
  conclusion => "Identify open problems" => follow_up

  export conclusion, follow_up
```

### Imports with dependency strength

Imports declare cross-module dependencies with strength:

- **strong** — logical dependency. If the imported knowledge is wrong, this module's conclusions are likely wrong too. Participates in BP.
- **weak** — contextual dependency. Relevant context, but this module's conclusions can stand on their own. Folded into prior, not BP edges.

```
import premise from other_module (strong)    -- affects truth value
import context from background (weak)        -- relevant but not load-bearing
```

### Exports and BP participation

Export determines whether knowledge enters the probabilistic inference layer:

- Exported knowledge → participates in BP (enters the factor graph)
- Non-exported knowledge → in LKM, visible, but does not participate in BP

### Module roles

Modules carry an optional role describing their purpose:

- `reasoning` — establishes conclusions through premises and reasoning
- `setting` — establishes shared context (definitions, environments, assumptions)
- `motivation` — establishes why the work was undertaken
- `follow_up` — establishes open questions for future work

Roles replace separate editorial fields — the structure itself carries editorial intent.

### Probabilistic semantics

In the new design, the module is a **pure organizational unit**. Probabilistic semantics are at the function application level:

- Each function application in an expression has its own prior/posterior (factor node)
- Each knowledge object has its own prior/posterior (variable node)
- The module provides scoping and narrative structure, not probabilistic weight

## Package

Package is primarily a V2 (package management) concern. In V1, a package is a container of modules with exports:

```
package falling_bodies:
  modules = [motivation, env, reasoning, follow_up]
  export conclusion, follow_up_question
```

V2 defines:

- `Gaia.toml` manifest
- Dependency resolution across packages
- Registry and publish protocol
- Global identity assignment at publish time

## Probabilistic Layer (V3)

### Unified probabilistic interface

**One pair of primitives — (prior, posterior) — applies to all language elements:**

| Language element | Prior | Posterior | Factor graph role |
|-----------------|-------|-----------|------------------|
| Knowledge (Claim, Setting) | Initial belief | Belief after BP | Variable node |
| Function application | Initial reliability | Reliability after BP | Factor node |
| ToolCall application | ≈ 1.0 (deterministic) | ≈ 1.0 | Near-transparent factor |

### Conditioning via import strength

Import strength is Gaia's analog of `observe` in probabilistic PLs:

- `strong` import → creates a BP edge (conditions the conclusion on the premise)
- `weak` import → folded into prior (contextual, does not create BP edge)

### BP as posterior inference

Belief propagation computes posteriors from priors + graph structure:

```
priors (input) → BP on factor graph → posteriors (output)
```

The factor graph is derived from the expression structure:

```
[premise]  --f(prior=0.9)--  [intermediate]  --g(prior=0.85)--  [conclusion]
   ↑                              ↑                                  ↑
 variable                      variable                           variable
(prior/posterior)            (prior/posterior)                  (prior/posterior)
```

## Version Layers Summary

| Layer | What it adds | PL analogy |
|-------|-------------|------------|
| **V1 — FP Core** | Knowledge, Action, Expression, Module | Haskell values, functions, composition, modules |
| **V2 — Package Management** | Package, Gaia.toml, dependency resolution, registry, publish, global identity | Cargo, Cabal, npm |
| **V3 — Probabilistic Layer** | Prior, posterior, dependency strength, BP | Church's flip/observe, Pyro's sample/observe |
| **Future** | Action type signatures, parameterized modules, dependent types, formal verification | Lean, OCaml functors, Coq |

## Open Design Questions

The following topics are identified for further discussion:

1. **Abstract syntax specification** — formal BNF grammar for the language
2. **Concrete syntax** — YAML serialization format mapping
3. **Well-formedness rules** — precise conditions for valid expressions, modules, packages
4. **Identity resolution algorithm** — how the registry merges equivalent knowledge from different packages (V2)
5. **BP on fine-grained factor graph** — implications of per-function-application factors vs per-module factors (V3)
6. **Action type signatures** — formal input/output type constraints for future type checking
7. **Scoping rules** — precise definition of visibility and reference resolution
8. **Interaction between Reasoning and ToolCall** — how tool results feed back into NL reasoning chains
