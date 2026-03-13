# Gaia Domain Model

## Purpose

This document defines the shared core vocabulary used by Gaia foundation docs.

Its job is to lock the minimum set of domain terms before later docs define:

- package schema
- package file formats
- global graph integration
- probabilistic semantics

## Boundary

This document defines vocabulary and modeling boundaries only.

It does not define:

- package file layout
- canonicalization or review algorithms
- server API contracts
- graph propagation, prior, belief, or BP

## Core Layers

Gaia V1 uses three conceptual layers:

1. global `closure` — a self-contained, reusable knowledge object
2. local `module` — a coherent unit that groups closures into a chain with imports and exports
3. local `package` — a collection of modules that exports selected closures

The design follows a **state-action model** inspired by functional programming:

- closures are the **states** — self-contained objects that can be passed around independently
- inferences are the **actions** — local reasoning steps that connect closures within a module's chain

## Shared Knowledge Objects

### `closure`

A `closure` is a globally identifiable, self-contained knowledge object.

The name comes from functional programming: like an FP closure that captures its free variables and can be passed around independently, a knowledge closure carries its content and metadata and can be exported, imported, and referenced without knowing the chain it was created in.

V1 keeps the closure kind set intentionally small:

- `claim`
- `question`
- `setting`
- `action`

This is the common substrate used by both local package tooling and later server-side ingestion.

### `claim`

A `claim` is a truth-apt statement or reusable result object.

Examples:

- a scientific statement
- a declarative gap statement
- a reusable code result
- a reusable Lean theorem/proof result

`claim` is the default kind for statement-like content.

### `question`

A `question` is an inquiry object.

It is not a truth-apt statement.

Examples:

- "Why does phenomenon X occur?"
- "Can implementation Y be proven correct?"

### `setting`

A `setting` is a context-setting object that determines how later reasoning should be interpreted or executed.

V1 uses `setting` to unify:

- definitions
- logical setup
- execution environment
- experimental environment

### `action`

An `action` is a self-contained, reusable process description.

It represents a process such as an inference method, a tool, or another canonicalized procedure. The action closure describes **what** the process is; the `inference` entries in a module's chain describe **how** it was applied in a specific context.

Examples:

- an inference method description
- a tool call specification
- another explicit process description

## Local Reasoning Structure

### `inference`

An `inference` is a local reasoning step within a module's chain. It connects closures by filling logical gaps, providing explanations, or describing how an action was applied.

Unlike closures, inferences are **not** self-contained — they depend on their surrounding context in the chain. They are never exported or referenced from outside the module.

In the FP analogy: closures are **values**, inferences are **lambdas**. An inference can be:

- **anonymous** — plain text describing the reasoning (like a lambda)
- **named** — references a reusable `action` closure (like a named function application)

This connects `action` closures (function definitions) to `inference` entries (function calls). An action describes **what** a process is; a named inference describes **how** that process was applied in a specific context.

### Chain model

A module's `chain` defines the narrative reading order: a sequential composition of lambdas applied to values.

```text
closure → inference → closure → inference → closure
  v₀    →    λ₁    →   v₁    →    λ₂    →   v₂
```

When the logical transition between two closures is trivial or locally obvious, the inference may be omitted — two adjacent closures in the chain imply a trivial transition.

### Cross-module dependencies

Modules declare cross-module dependencies via `imports`, with dependency roles authored today as `dependency: direct/indirect`:

- **direct** — semantic role `premise`. If the imported closure is wrong, this module's conclusions are likely wrong too. Across package boundaries, only exported knowledge may be used this way.
- **indirect** — semantic role `context`. The imported closure is relevant background, but this module's conclusions can stand on their own. A non-exported external closure may still be referenced explicitly, but only in this context role.

These are local module relations, not global closure properties. The same closure can be a direct dependency in one module and an indirect dependency in another.

## Module and Package Organization

### `module`

A `module` groups closures into a coherent unit via a chain of closures and inferences. It imports closures from other modules and exports selected closures as its public interface. This is analogous to a module in Rust or Julia: it groups related logic, declares its dependencies (`imports`), and exposes a public interface (`exports`).

Modules have an optional `role` that describes their purpose within the package:

- `reasoning` — establishes conclusions through premises, inferences, and results
- `setting` — establishes shared context (definitions, environment, assumptions)
- `motivation` — establishes why the research was undertaken
- `follow_up_question` — establishes open questions for future work
- `other`

Module roles replace the need for separate editorial fields on packages. The motivation for a research effort is expressed as a `motivation` module; shared definitions become a `setting` module; open questions become a `follow_up_question` module. The structure itself carries the editorial intent.

### `package`

A `package` is a reusable container of modules. It exports selected closures from its modules as the package's public interface.

Typical examples include:

- a paper
- a research bundle
- a structured note
- a project unit

The package's `modules[]` list order defines the recommended reading order for the package (narrative ordering). The package's `exports[]` list is a curated subset of closure_ids from its modules — the key results this package offers to the outside world.

## Important Non-Equivalences

The following should not be treated as equivalent:

- `claim` and `question`
- `claim` and `setting`
- `action` (closure kind) and `inference` (local chain entry)
- global `closure` identity and local chain occurrence
- narrative ordering and logical dependency

Examples:

- a statement-form gap is a `claim`, not a `question`
- a definition is a `setting`, not a generic `claim`
- an `action` closure describes **what** a process is; an `inference` describes **how** it was applied locally
- adjacent closures in a module's chain do not imply logical dependency — all dependencies are declared via `imports`

## Deferred Distinctions

V1 intentionally does not yet split the closure system into more detailed epistemic kinds such as:

- `observation`
- `assumption`
- `conjecture`

Those distinctions may become important later for graph integration, probabilistic semantics, or review policy, but they are not required for the minimal shared package substrate.

For now:

- observation-like content is modeled as `claim` plus provenance and supporting resources
- assumption-like content is modeled as `claim` or `setting`, depending on whether it is statement-like or setup-like

## Relationship To Later Docs

- [shared/knowledge-package-static.md](shared/knowledge-package-static.md) instantiates this vocabulary as the V1 static package schema
- [shared/knowledge-package-file-formats.md](shared/knowledge-package-file-formats.md) defines the corresponding package and review-report file formats
- V2 (graph integration) will define how packages map to the global graph
- V3 (probabilistic semantics) will define prior, belief, and BP on top of the dependency graph
- later docs should build on rather than silently replace the terms defined here

## Current Rule

When a new design needs a new noun, prefer to:

1. reuse `claim`, `question`, `setting`, or `action` if one already fits
2. place local dependency semantics on module `imports`, not on the global closure kind
3. defer finer epistemic distinctions until they are required by graph or probabilistic semantics
