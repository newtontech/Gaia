# Gaia Lang & CLI Documentation Rewrite — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace all superseded Typst v4 foundation docs with 7 new documents reflecting the current Python-native Gaia Lang DSL and CLI.

**Architecture:** Archive old docs to `docs/archive/foundations-v4/`, then write 3 gaia-lang docs (dsl.md, package.md, knowledge-and-reasoning.md) and 4 cli docs (workflow.md, compilation.md, inference.md, registration.md). All docs reference `docs/foundations/gaia-ir/` for IR definitions — never redefine.

**Tech Stack:** Markdown, cross-references to gaia-ir/ specs (01–08).

**Spec:** `docs/specs/2026-04-03-gaia-lang-cli-docs-rewrite-design.md`

---

## Conventions

### Status Header

Every new doc MUST start with:

```markdown
---
status: current-canonical
layer: gaia-lang | cli
since: v5-phase-1
---
```

### Cross-Reference Style

Reference gaia-ir concepts by relative link + section anchor:

```markdown
See [Gaia IR §1 — Knowledge](../gaia-ir/02-gaia-ir.md#1-knowledge)
```

Key gaia-ir cross-reference targets:

| Concept | Link target |
|---------|-------------|
| Knowledge types (claim/setting/question) | `../gaia-ir/02-gaia-ir.md` §1 |
| Operator types & truth tables | `../gaia-ir/02-gaia-ir.md` §2 |
| Strategy forms (leaf/composite/formal) | `../gaia-ir/02-gaia-ir.md` §3 |
| QID format | `../gaia-ir/03-identity-and-hashing.md` §2 |
| content_hash | `../gaia-ir/03-identity-and-hashing.md` §3 |
| ir_hash | `../gaia-ir/03-identity-and-hashing.md` §5 |
| Helper claims & private nodes | `../gaia-ir/04-helper-claims.md` |
| Parameterization (PriorRecord, StrategyParamRecord) | `../gaia-ir/06-parameterization.md` |
| Lowering contract | `../gaia-ir/07-lowering.md` |
| Validation layers | `../gaia-ir/08-validation.md` |

### Writing Style

- Foundation docs, not tutorials — precise and authoritative
- Show real Python code examples from actual DSL API
- Each doc should be readable standalone but link to related docs
- Keep under 400 lines per doc
- No emojis

---

## Chunk 1: Archive & Setup

### Task 1: Archive old docs

**Files:**
- Move: `docs/foundations/gaia-lang/spec.md` → `docs/archive/foundations-v4/gaia-lang/spec.md`
- Move: `docs/foundations/gaia-lang/knowledge-types.md` → `docs/archive/foundations-v4/gaia-lang/knowledge-types.md`
- Move: `docs/foundations/gaia-lang/package-model.md` → `docs/archive/foundations-v4/gaia-lang/package-model.md`
- Move: `docs/foundations/cli/compiler.md` → `docs/archive/foundations-v4/cli/compiler.md`
- Move: `docs/foundations/cli/lifecycle.md` → `docs/archive/foundations-v4/cli/lifecycle.md`
- Move: `docs/foundations/cli/local-inference.md` → `docs/archive/foundations-v4/cli/local-inference.md`
- Move: `docs/foundations/cli/local-storage.md` → `docs/archive/foundations-v4/cli/local-storage.md`

- [ ] **Step 1: Create archive directories**

```bash
mkdir -p docs/archive/foundations-v4/gaia-lang
mkdir -p docs/archive/foundations-v4/cli
```

- [ ] **Step 2: Move gaia-lang docs**

```bash
git mv docs/foundations/gaia-lang/spec.md docs/archive/foundations-v4/gaia-lang/spec.md
git mv docs/foundations/gaia-lang/knowledge-types.md docs/archive/foundations-v4/gaia-lang/knowledge-types.md
git mv docs/foundations/gaia-lang/package-model.md docs/archive/foundations-v4/gaia-lang/package-model.md
```

- [ ] **Step 3: Move cli docs**

```bash
git mv docs/foundations/cli/compiler.md docs/archive/foundations-v4/cli/compiler.md
git mv docs/foundations/cli/lifecycle.md docs/archive/foundations-v4/cli/lifecycle.md
git mv docs/foundations/cli/local-inference.md docs/archive/foundations-v4/cli/local-inference.md
git mv docs/foundations/cli/local-storage.md docs/archive/foundations-v4/cli/local-storage.md
```

- [ ] **Step 4: Commit archive**

```bash
git add docs/archive/foundations-v4/
git commit -m "docs: archive v4 gaia-lang and cli foundation docs"
```

---

## Chunk 2: Gaia Lang Foundation Docs (3 files)

Tasks 2–4 are independent and can be executed in parallel.

### Task 2: Write `docs/foundations/gaia-lang/dsl.md`

**Files:**
- Create: `docs/foundations/gaia-lang/dsl.md`

**Source code to read for accuracy:**
- `gaia/lang/__init__.py` — public API exports
- `gaia/lang/dsl/knowledge.py` — claim/setting/question signatures
- `gaia/lang/dsl/operators.py` — operator signatures
- `gaia/lang/dsl/strategies.py` — strategy signatures
- `gaia/lang/runtime/nodes.py` — Knowledge/Strategy/Operator dataclasses
- `gaia/lang/runtime/package.py` — auto-registration via contextvars

**Content structure:**

```markdown
---
status: current-canonical
layer: gaia-lang
since: v5-phase-1
---

# Gaia Lang DSL Reference

## Overview

(Python 3.12+ internal DSL. Declarative knowledge authoring.
All declarations auto-register to a CollectedPackage via contextvars.
Import path: `from gaia.lang import claim, setting, question, ...`)

## Knowledge Declarations

### claim()

(Signature from gaia/lang/dsl/knowledge.py.
When `given` is provided, auto-creates a `noisy_and` strategy.
`background` attaches context without making it a premise.
`parameters` for universal quantification.
`label` for cross-referencing.)

### setting()

(Background context. No probability, no BP participation.
Reference: gaia-ir/02-gaia-ir.md §1)

### question()

(Open research inquiry. No probability.
Reference: gaia-ir/02-gaia-ir.md §1)

## Operators

(Deterministic logical constraints. Each returns a helper claim that
can be used as a premise in further reasoning.
Reference: gaia-ir/02-gaia-ir.md §2, gaia-ir/04-helper-claims.md)

### contradiction(a, b)
### equivalence(a, b)
### complement(a, b)
### disjunction(*claims)

(Each with: signature, one-line semantics, example, link to IR operator type.)

## Strategies

(Reasoning declarations connecting Knowledge nodes.
Reference: gaia-ir/02-gaia-ir.md §3)

### Direct Strategies
#### noisy_and(premises, conclusion)
#### infer(premises, conclusion)

### Named Strategies (compile-time formalization)
#### deduction(premises, conclusion)
#### abduction(observation, hypothesis, alternative)
#### analogy(source, target, bridge)
#### extrapolation(source, target, continuity)
#### elimination(exhaustiveness, excluded, survivor)
#### case_analysis(exhaustiveness, cases, conclusion)
#### mathematical_induction(base, step, conclusion)

(Each with: signature, semantic meaning, example, what it formalizes into.
Reference: gaia-ir/02-gaia-ir.md §3 for IR strategy forms.)

### Composite Strategy
#### composite(premises, conclusion, sub_strategies)

## Labels and Cross-Referencing

(Variable-name auto-inference, manual .label assignment,
QID generation at compile time.
Reference: gaia-ir/03-identity-and-hashing.md §2)

## Complete Example

(Galileo falling bodies — based on tests/cli/fixtures/galileo_lang/
Show: settings, claims, contradiction operator, noisy_and via given,
labels, and what the compiled IR looks like.)
```

- [ ] **Step 1: Read source files** — read the 6 source files listed above for exact signatures
- [ ] **Step 2: Write `docs/foundations/gaia-lang/dsl.md`** following the structure above
- [ ] **Step 3: Verify** — ensure all function signatures match code, cross-references use correct section numbers
- [ ] **Step 4: Commit**

```bash
git add docs/foundations/gaia-lang/dsl.md
git commit -m "docs(gaia-lang): add DSL reference for v5 Python DSL"
```

---

### Task 3: Write `docs/foundations/gaia-lang/package.md`

**Files:**
- Create: `docs/foundations/gaia-lang/package.md`

**Source code to read for accuracy:**
- `gaia/lang/runtime/package.py` — CollectedPackage, package inference from pyproject.toml
- `gaia/cli/_packages.py` — load_gaia_package, label inference, layout detection
- `gaia/cli/_reviews.py` — review sidecar discovery
- `gaia/cli/commands/register.py` — naming convention, uuid, registry metadata

**Content structure:**

```markdown
---
status: current-canonical
layer: gaia-lang
since: v5-phase-1
---

# Gaia Lang Package Model

## Package Creation

### gaia init (scaffold)

(gaia init <name> generates pyproject.toml + src/ + .gitignore.
Note: not yet implemented as of current code — document the intended behavior.
Fallback: uv init + manual [tool.gaia] config.)

### Manual Setup

(uv init, then add [tool.gaia] section manually.)

## pyproject.toml Structure

### [project] section
(name: must end with -gaia. version, description, dependencies.)

### [tool.gaia] section
(type: "knowledge-package" — required.
namespace — optional, default "reg".
uuid — required for registration.)

## Naming Convention

(Julia-style:
GitHub repo: CamelCase.gaia
PyPI name: kebab-case-gaia
Python import: snake_case without suffix
Reference: docs/specs/2026-04-02-gaia-lang-v5-python-dsl-design.md)

## Directory Layout

(src/<import_name>/__init__.py — standard Python.
Flat layout also supported.
.gaia/ — compilation artifacts, gitignored.)

## Visibility

(__all__ — exported, cross-package visible.
Public — no _ prefix, package-internal.
Private — _ prefix, not compiled into IR.)

## Cross-Package Dependencies

(Standard Python imports. [project].dependencies lists *-gaia packages.
At compile time, imported claims get foreign QIDs.)

## Review Sidecar

(Single: <package>/review.py exports REVIEW = ReviewBundle(...)
Multi: <package>/reviews/<name>.py
ReviewBundle contains: claim_reviews, strategy_reviews, generated_claim_reviews)

## Build Artifacts

(.gaia/ir.json — LocalCanonicalGraph.
.gaia/ir_hash — SHA-256 integrity.
.gaia/reviews/<name>/ — parameterization.json + beliefs.json.)

## Package Lifecycle

(authored → compiled → checked → tagged → registered.
Reference: cli/workflow.md for command details.)
```

- [ ] **Step 1: Read source files** — read the 4 source files listed above
- [ ] **Step 2: Write `docs/foundations/gaia-lang/package.md`** following the structure above
- [ ] **Step 3: Verify** — ensure pyproject.toml fields match actual code validation
- [ ] **Step 4: Commit**

```bash
git add docs/foundations/gaia-lang/package.md
git commit -m "docs(gaia-lang): add package model for v5 Python packages"
```

---

### Task 4: Write `docs/foundations/gaia-lang/knowledge-and-reasoning.md`

**Files:**
- Create: `docs/foundations/gaia-lang/knowledge-and-reasoning.md`

**Source code to read for accuracy:**
- `gaia/ir/knowledge.py` — Knowledge, KnowledgeType
- `gaia/ir/operator.py` — Operator, OperatorType, arity rules
- `gaia/ir/strategy.py` — Strategy, CompositeStrategy, FormalStrategy, StrategyType
- `gaia/ir/formalize.py` — formalize_named_strategy, expansion patterns
- `gaia/bp/potentials.py` — potential matrices per factor type
- `gaia/lang/compiler/compile.py` — how DSL objects map to IR

**Content structure:**

```markdown
---
status: current-canonical
layer: gaia-lang
since: v5-phase-1
---

# Knowledge Types and Reasoning Semantics

## Knowledge Types

(Three types and their semantic roles.
Reference: gaia-ir/02-gaia-ir.md §1)

### Claim
(Only type with prior. Participates in BP as a variable node.
Can be universal — with parameters.)

### Setting
(Background context. Listed in factor premises but does not
send/receive BP messages. Reference: gaia-ir/02-gaia-ir.md §1.2)

### Question
(Open inquiry. No probability, no BP participation.)

## Operator Semantics

(Deterministic constraints. Each has a defined potential matrix.
Reference: gaia-ir/02-gaia-ir.md §2)

### Truth Tables

(Table showing each operator type with its potential values.
Source: gaia/bp/potentials.py
- implication: [1, ε, 1, 1]
- equivalence: [1, ε, ε, 1]
- contradiction: [1, 1, 1, ε]
- complement: [ε, 1, 1, ε]
- conjunction: deterministic AND
- disjunction: deterministic OR)

### Helper Claims

(Operators return helper claims. These are ordinary claims of
type="claim" with metadata marking them as structural results.
Reference: gaia-ir/04-helper-claims.md)

## Strategy Semantics

(Reasoning declarations. Three forms in IR.
Reference: gaia-ir/02-gaia-ir.md §3)

### Direct Strategies → Factor Mapping

(noisy_and: lowered to CONJUNCTION + SOFT_ENTAILMENT factors.
infer: lowered to CONDITIONAL factor with full CPT.
Reference: gaia-ir/07-lowering.md)

### Named Strategy Formalization

(At compile time, named strategies expand into FormalStrategy
with generated helper claims + deterministic operators.
Reference: gaia-ir/02-gaia-ir.md §3.2)

#### Deduction
(premises → conjunction → implication → conclusion)

#### Abduction
(observation + alternative → disjunction + equivalence)

#### Analogy
(source + bridge → conjunction → implication → target)

#### Extrapolation
(source + continuity → conjunction → implication → target)

#### Elimination
(exhaustiveness + excluded pairs → contradictions + conjunction gate → survivor)

#### Case Analysis
(exhaustiveness + case/support pairs → per-case implications + conjunction → conclusion)

#### Mathematical Induction
(base + step → conjunction → implication → conclusion)

### Composite Strategies

(References sub-strategies by ID. Recursive expansion at lowering.
Reference: gaia-ir/02-gaia-ir.md §3.1)

## DSL → IR Mapping

(Table:
lang.Knowledge → ir.Knowledge (QID assigned, content_hash computed)
lang.Strategy → ir.Strategy / ir.FormalStrategy / ir.CompositeStrategy
lang.Operator → ir.Operator
CollectedPackage → ir.LocalCanonicalGraph)

## Cromwell's Rule

(All probabilities clamped to [ε, 1-ε] where ε = 1e-3.
Ensures no impossible states collapse BP.
Reference: gaia-ir/06-parameterization.md)
```

- [ ] **Step 1: Read source files** — read the 6 source files listed above
- [ ] **Step 2: Write `docs/foundations/gaia-lang/knowledge-and-reasoning.md`** following the structure above
- [ ] **Step 3: Verify** — ensure expansion patterns match `gaia/ir/formalize.py`, potential values match `gaia/bp/potentials.py`
- [ ] **Step 4: Commit**

```bash
git add docs/foundations/gaia-lang/knowledge-and-reasoning.md
git commit -m "docs(gaia-lang): add knowledge types and reasoning semantics"
```

---

## Chunk 3: CLI Foundation Docs (4 files)

Tasks 5–8 are independent and can be executed in parallel.

### Task 5: Write `docs/foundations/cli/workflow.md`

**Files:**
- Create: `docs/foundations/cli/workflow.md`

**Source code to read for accuracy:**
- `gaia/cli/main.py` — Typer app, command registration
- `gaia/cli/commands/compile.py` — compile command
- `gaia/cli/commands/check.py` — check command
- `gaia/cli/commands/infer.py` — infer command
- `gaia/cli/commands/register.py` — register command

**Content structure:**

```markdown
---
status: current-canonical
layer: cli
since: v5-phase-1
---

# CLI Workflow

## Overview

(Five-step pipeline: init → compile → check → infer → register.
Entry point: gaia.cli.main:app, installed as `gaia` via pyproject.toml.)

## Commands

### gaia init <name>

(Scaffold a new Gaia knowledge package.
Generates: pyproject.toml with [tool.gaia], src/<import_name>/__init__.py
with example DSL declarations, .gitignore with .gaia/.
Note: not yet implemented — currently use `uv init` + manual config.
Reference: gaia-lang/package.md for package structure.)

### gaia compile [path]

(Compile Python DSL to Gaia IR.
Input: package directory with pyproject.toml.
Output: .gaia/ir.json + .gaia/ir_hash.
Deterministic, no LLM, no network.
Reference: cli/compilation.md for internals.)

### gaia check [path]

(Validate package structure and artifact consistency.
Checks: -gaia name suffix, [tool.gaia] fields, ir_hash consistency,
IR schema validation.
Reference: cli/compilation.md for details.)

### gaia infer [path] [--review <name>]

(Run belief propagation with review sidecar parameterization.
Input: compiled package + review sidecar.
Output: .gaia/reviews/<name>/parameterization.json + beliefs.json.
Reference: cli/inference.md for internals.)

### gaia register [path] [--tag] [--registry-dir] [--create-pr]

(Submit package to Gaia registry.
Prerequisites: uuid set, git clean, tag pushed.
Dry-run by default; writes registry metadata with --registry-dir.
Reference: cli/registration.md for details.)

## Artifacts by Stage

(Table:
| Stage    | Artifacts |
| init     | pyproject.toml, src/, .gitignore |
| compile  | .gaia/ir.json, .gaia/ir_hash |
| check    | (validation only, no new artifacts) |
| infer    | .gaia/reviews/<name>/parameterization.json, beliefs.json |
| register | Package.toml, Versions.toml, Deps.toml in registry repo |)

## Quick Start

(Complete shell session from package creation to registration.
Use galileo-falling-bodies-gaia as running example.)
```

- [ ] **Step 1: Read source files** — read the 5 CLI command files
- [ ] **Step 2: Write `docs/foundations/cli/workflow.md`** following the structure above
- [ ] **Step 3: Verify** — ensure command flags/arguments match actual Typer definitions
- [ ] **Step 4: Commit**

```bash
git add docs/foundations/cli/workflow.md
git commit -m "docs(cli): add workflow overview for v5 CLI"
```

---

### Task 6: Write `docs/foundations/cli/compilation.md`

**Files:**
- Create: `docs/foundations/cli/compilation.md`

**Source code to read for accuracy:**
- `gaia/cli/commands/compile.py` — compile command implementation
- `gaia/cli/commands/check.py` — check command implementation
- `gaia/cli/_packages.py` — load_gaia_package, compile_loaded_package, write_compiled_artifacts
- `gaia/lang/compiler/compile.py` — compile_package_artifact, CompiledPackage
- `gaia/lang/runtime/package.py` — CollectedPackage, package inference
- `gaia/ir/validator.py` — validate_local_graph

**Content structure:**

```markdown
---
status: current-canonical
layer: cli
since: v5-phase-1
---

# Compilation and Validation

## gaia compile

### Pipeline

(Diagram:
pyproject.toml → load metadata → dynamic import →
CollectedPackage → compile → LocalCanonicalGraph →
validate → write .gaia/ir.json + ir_hash)

### Step 1: Load Package Metadata

(Reads pyproject.toml: project.name, version, [tool.gaia].
Detects layout: src/ or flat.
Source: gaia/cli/_packages.py:load_gaia_package)

### Step 2: Execute DSL Module

(Dynamic import with fresh module cache.
DSL declarations auto-register to CollectedPackage.
Variable names → labels via __all__ or module attribute scan.
Source: gaia/cli/_packages.py, gaia/lang/runtime/package.py)

### Step 3: Compile to IR

(CollectedPackage → LocalCanonicalGraph.
- Knowledge closure: collect all referenced nodes recursively
- QID assignment: local={ns}:{pkg}::{label}, foreign={ns}:{foreign_pkg}::{label},
  anonymous={ns}:{pkg}::_anon_{hash8}
- Named strategy formalization: deduction/abduction/etc. →
  FormalStrategy + generated helper claims
- Composite strategy: references sub-strategies by ID
Source: gaia/lang/compiler/compile.py)

### Step 4: Compute IR Hash

(Canonical JSON serialization → SHA-256.
Order-independent: same source always produces same hash.
Reference: gaia-ir/03-identity-and-hashing.md §5)

### Step 5: Validate and Write

(validate_local_graph: schema, reference closure, FormalExpr closure.
Errors → abort. Warnings → report and continue.
Output: .gaia/ir.json + .gaia/ir_hash.
Reference: gaia-ir/08-validation.md)

## gaia check

(Validation items — list each with pass/fail criteria:
1. project.name ends with "-gaia"
2. [tool.gaia].type == "knowledge-package"
3. .gaia/ir.json and .gaia/ir_hash exist
4. Recompile and verify hash matches stored
5. IR validator passes with no errors
Source: gaia/cli/commands/check.py)

## Determinism Guarantee

(Same source → same ir_hash.
No LLM calls, no network access, no randomness.
All IDs computed from content via deterministic hashing.)
```

- [ ] **Step 1: Read source files** — read the 6 source files listed above
- [ ] **Step 2: Write `docs/foundations/cli/compilation.md`** following the structure above
- [ ] **Step 3: Verify** — ensure pipeline steps match actual code flow
- [ ] **Step 4: Commit**

```bash
git add docs/foundations/cli/compilation.md
git commit -m "docs(cli): add compilation and validation internals"
```

---

### Task 7: Write `docs/foundations/cli/inference.md`

**Files:**
- Create: `docs/foundations/cli/inference.md`

**Source code to read for accuracy:**
- `gaia/cli/commands/infer.py` — infer command implementation
- `gaia/cli/_reviews.py` — review sidecar discovery, resolution
- `gaia/review/` — ReviewBundle, ClaimReview, StrategyReview, GeneratedClaimReview
- `gaia/ir/parameterization.py` — PriorRecord, StrategyParamRecord, Cromwell clamping
- `gaia/ir/validator.py` — validate_parameterization
- `gaia/bp/lowering.py` — lower_local_graph
- `gaia/bp/bp.py` — BeliefPropagation algorithm
- `gaia/bp/potentials.py` — potential evaluation

**Content structure:**

```markdown
---
status: current-canonical
layer: cli
since: v5-phase-1
---

# Inference Pipeline

## Overview

(`gaia infer` runs belief propagation on a compiled package using
review sidecar parameterization. Pipeline:
compiled IR + review sidecar → parameterization → factor graph → BP → beliefs)

## Review Sidecar Model

### ReviewBundle Structure

(ReviewBundle contains:
- claim_reviews: dict mapping claim objects → ClaimReview(prior=float)
- strategy_reviews: dict mapping strategy objects → StrategyReview(conditional_probabilities=[...])
- generated_claim_reviews: dict mapping label → GeneratedClaimReview(prior=float)
Source: gaia/review/)

### Discovery

(Single review: <package>/review.py with REVIEW = ReviewBundle(...)
Multi-review: <package>/reviews/<name>.py
If multiple exist, --review <name> is required.
Source: gaia/cli/_reviews.py:load_gaia_review)

### Resolution

(Runtime objects resolved to IR parameterization records:
- ClaimReview → PriorRecord(knowledge_id=QID, value=prior)
- StrategyReview → StrategyParamRecord(strategy_id=lcs_..., conditional_probabilities=[...])
- GeneratedClaimReview → PriorRecord for formalization-generated helper claims
Source: gaia/cli/_reviews.py:resolve_gaia_review)

## Parameterization Validation

(Every non-private claim must have a PriorRecord.
Every parameterized strategy (infer, noisy_and) must have a StrategyParamRecord.
All values clamped to [ε, 1-ε].
Reference: gaia-ir/06-parameterization.md, gaia-ir/08-validation.md)

## Lowering to Factor Graph

(LocalCanonicalGraph → FactorGraph.
- Knowledge → Variable with prior
- Strategy/Operator → Factor
- 8 factor types: implication, equivalence, contradiction, complement,
  disjunction, conjunction, soft_entailment, conditional
- Named strategies auto-formalized before lowering
Reference: gaia-ir/07-lowering.md.
Source: gaia/bp/lowering.py)

## Belief Propagation

(Sum-product loopy BP.
Parameters: damping=0.5, max_iterations=100, convergence_threshold=1e-4.
Convergence: stops when max belief change < threshold.
Output: posterior belief per variable.
Source: gaia/bp/bp.py)

## Output

(.gaia/reviews/<review_name>/parameterization.json — input records.
.gaia/reviews/<review_name>/beliefs.json — posterior beliefs + diagnostics:
  converged, iterations, per-variable beliefs.)
```

- [ ] **Step 1: Read source files** — read the 8 source files listed above
- [ ] **Step 2: Write `docs/foundations/cli/inference.md`** following the structure above
- [ ] **Step 3: Verify** — ensure BP parameters match code defaults, factor types are complete
- [ ] **Step 4: Commit**

```bash
git add docs/foundations/cli/inference.md
git commit -m "docs(cli): add inference pipeline documentation"
```

---

### Task 8: Write `docs/foundations/cli/registration.md`

**Files:**
- Create: `docs/foundations/cli/registration.md`

**Source code to read for accuracy:**
- `gaia/cli/commands/register.py` — register command implementation
- `docs/specs/2026-04-02-gaia-registry-design.md` — registry architecture spec

**Content structure:**

```markdown
---
status: current-canonical
layer: cli
since: v5-phase-1
---

# Registry Registration

## Overview

(`gaia register` prepares or submits a package registration to the
Gaia Official Registry — a Julia General Registry-style metadata-only
GitHub repo.)

## Prerequisites

(Before running gaia register:
1. [tool.gaia].uuid set in pyproject.toml (valid UUID)
2. Package compiled and checked (gaia compile + gaia check pass)
3. Git worktree is clean
4. Git tag exists (default: v<version>) and points to HEAD
5. Tag pushed to origin
6. Repository is on GitHub (Phase 1 limitation))

## Dry-Run Mode (default)

(Without --registry-dir, outputs a JSON registration plan to stdout.
Contains: package metadata, version metadata, dependencies, PR template.
Useful for previewing before committing to registry.)

## Registry Write Mode

(With --registry-dir <path>:
1. Creates branch register/<name>-<version> in registry checkout
2. Writes/updates:
   - packages/<name>/Package.toml (identity: uuid, name, repo URL, description)
   - packages/<name>/Versions.toml (per-version: version, ir_hash, git_tag, git_sha)
   - packages/<name>/Deps.toml (per-version dependency specs)
3. Commits changes)

## Creating a PR

(With --create-pr:
- Pushes branch to registry remote
- Runs gh pr create with title and body
- Registry CI takes over from here)

## Registry CI Overview

(What happens after PR is created — brief summary:
- Untrusted sandbox job: clone package repo by pinned SHA, build wheel, validate IR
- Trusted gate job: publish wheel to GitHub Releases, update PEP 503 index on GitHub Pages
- Auto-merge with waiting period: 72h for new packages, 1h for version updates
Reference: docs/specs/2026-04-02-gaia-registry-design.md for full spec)

## Consumer Workflow

(End users install published packages via standard pip/uv:
uv add galileo-falling-bodies-gaia --index-url <github-pages-url>
Then import and use as Python dependency.)

## Registry Metadata Format

(TOML examples for Package.toml, Versions.toml, Deps.toml.
Source: gaia/cli/commands/register.py for exact format.)
```

- [ ] **Step 1: Read source files** — read register.py and registry design spec
- [ ] **Step 2: Write `docs/foundations/cli/registration.md`** following the structure above
- [ ] **Step 3: Verify** — ensure TOML field names match code, prerequisite checks match code
- [ ] **Step 4: Commit**

```bash
git add docs/foundations/cli/registration.md
git commit -m "docs(cli): add registry registration documentation"
```

---

## Chunk 4: Final Integration

### Task 9: Update foundation index and final commit

**Files:**
- Modify: `docs/foundations/README.md` (if it references old files)

- [ ] **Step 1: Update README.md** — replace old file references with new file names

Old references to remove:
- `gaia-lang/spec.md` → now `gaia-lang/dsl.md`
- `gaia-lang/knowledge-types.md` → now `gaia-lang/knowledge-and-reasoning.md`
- `gaia-lang/package-model.md` → now `gaia-lang/package.md`
- `cli/compiler.md` → now `cli/compilation.md`
- `cli/lifecycle.md` → now `cli/workflow.md`
- `cli/local-inference.md` → now `cli/inference.md`
- `cli/local-storage.md` → now `cli/registration.md`

- [ ] **Step 2: Cross-check all internal links** between the 7 new docs

Verify these cross-references work:
- dsl.md → package.md (for package structure)
- dsl.md → knowledge-and-reasoning.md (for type semantics)
- package.md → cli/workflow.md (for lifecycle commands)
- workflow.md → compilation.md, inference.md, registration.md (for details)
- knowledge-and-reasoning.md → gaia-ir/* docs (for IR definitions)

- [ ] **Step 3: Commit**

```bash
git add docs/foundations/README.md
git commit -m "docs: update foundation index for v5 doc structure"
```

- [ ] **Step 4: Run ruff** (no Python changes, but verify no accidental file issues)

```bash
ruff check .
ruff format --check .
```
