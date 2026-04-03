# Gaia Lang & CLI Documentation Rewrite Design

**Status:** Target design
**Date:** 2026-04-03
**Scope:** `docs/foundations/gaia-lang/` and `docs/foundations/cli/`

## Summary

Rewrite the Gaia Lang and CLI foundation docs to reflect the current Python-native
DSL (`gaia.lang`), restructured codebase (`gaia.ir`, `gaia.cli`, `gaia.bp`), and
the compile → check → infer → register workflow. Archive all superseded Typst v4 docs.

## Context

The codebase has completed:
- Gaia Lang v5 Python DSL (`gaia/lang/`)
- Package restructure: `gaia.ir`, `gaia.lang`, `gaia.cli`, `gaia.bp`, `gaia.review`
- CLI commands: `compile`, `check`, `infer`, `register`
- Review sidecar model for inference parameterization
- Julia-style registry protocol

Current foundation docs still reference Typst v4 syntax, old `libs/` code paths,
and a workflow that no longer exists. Some docs are marked "superseded" but have
no replacement.

## Approach

1. Archive all existing files in `gaia-lang/` and `cli/` to `docs/archive/`
2. Write 7 new documents based on current code
3. Align terminology and cross-references with `docs/foundations/gaia-ir/`

## Document Structure

### `docs/foundations/gaia-lang/` (3 files)

#### `dsl.md` — DSL Complete Reference

Author-facing API manual for the Python DSL.

- Overview: Python 3.12+ internal DSL, declarative knowledge authoring,
  auto-registration via contextvars
- Knowledge declarations
  - `claim(content, *, given, background, parameters, provenance, label, **metadata)`
  - `setting(content, **metadata)`
  - `question(content, **metadata)`
  - `given` auto-creates `noisy_and` strategy
- Operators (deterministic constraints, return helper claims)
  - `contradiction(a, b)` — not both true
  - `equivalence(a, b)` — same truth value
  - `complement(a, b)` — opposite truth values
  - `disjunction(*claims)` — at least one true
- Strategies (reasoning declarations)
  - Direct: `noisy_and()`, `infer()`
  - Named: `deduction()`, `abduction()`, `analogy()`, `extrapolation()`,
    `elimination()`, `case_analysis()`, `mathematical_induction()`
  - Composite: `composite()`
  - Each with signature, semantics, example
- Labels and cross-referencing
- Complete example (Galileo falling bodies)

#### `package.md` — Package Model

Author-facing project configuration guide.

- Package creation: `gaia init <name>` (scaffold) or manual `uv init` + config
- `pyproject.toml` structure: `[project]` + `[tool.gaia]` fields
- Naming convention: GitHub `*.gaia` → PyPI `*-gaia` → Python `snake_case`
- Directory layout: `src/<import_name>/`, flat layout
- Visibility: `__all__` (exported), public (no `_`), private (`_` prefix)
- Cross-package dependencies: standard Python imports + `[project].dependencies`
- Review sidecar: `review.py` or `reviews/<name>.py` with `REVIEW = ReviewBundle(...)`
- Build artifacts: `.gaia/ir.json`, `.gaia/ir_hash`, `.gaia/reviews/<name>/`

#### `knowledge-and-reasoning.md` — Knowledge Types & Reasoning Semantics

Bridge between DSL syntax and Gaia IR.

- Three knowledge types
  - claim: only type carrying probability, participates in BP
  - setting: background context, no BP participation
  - question: open inquiry, no BP participation
- Operator semantics: how each constrains the factor graph (potential matrices)
- Strategy semantics and expansion
  - Direct (noisy_and, infer) → direct factor mapping
  - Named → formalization → FormalStrategy + generated helper claims
  - Expansion patterns per named strategy
- DSL → IR mapping: `lang.Knowledge` → `ir.Knowledge`, etc.
- Cromwell's rule: all probabilities in [eps, 1-eps]

### `docs/foundations/cli/` (4 files)

#### `workflow.md` — Complete Workflow

Big-picture overview of the full CLI pipeline.

- Five-step pipeline: `init → compile → check → infer → register`
- Per-command summary (1-2 paragraphs each): input, output, purpose
  - `gaia init <name>` — scaffold pyproject.toml + src/ + .gitignore
  - `gaia compile [path]` — Python DSL → .gaia/ir.json + ir_hash
  - `gaia check [path]` — validate metadata, hash consistency, schema
  - `gaia infer [path] [--review <name>]` — review sidecar + BP → beliefs
  - `gaia register [path] [--tag] [--registry-dir] [--create-pr]` — registry submission
- Artifacts-by-stage table
- Quick start: complete shell session from init to register

#### `compilation.md` — Compilation & Validation

Internals of `gaia compile` and `gaia check`.

- Compilation pipeline:
  pyproject.toml → dynamic import → CollectedPackage → LocalCanonicalGraph → .gaia/ir.json
  - Metadata loading (name, namespace, version)
  - Python module execution → DSL auto-registration
  - Variable name → label inference
  - QID assignment: `{namespace}:{package}::{label}`, anonymous via content hash
  - Named strategy formalization (→ FormalStrategy + helper claims)
  - IR hash computation (canonical JSON SHA-256, order-independent)
  - Schema validation (`gaia.ir.validator`)
- gaia check validation items:
  - name ends with `-gaia`
  - [tool.gaia] required fields
  - .gaia/ir.json exists and hash matches
  - IR validator passes (no errors)
- Determinism guarantee: same source → same ir_hash, no LLM/network/randomness

#### `inference.md` — Inference Pipeline

Internals of `gaia infer`.

- Review sidecar model
  - ReviewBundle(claim_reviews, strategy_reviews, generated_claim_reviews)
  - Discovery: single `review.py` vs multi `reviews/<name>.py`
  - `--review <name>` selection
- Parameterization resolution
  - ClaimReview → PriorRecord (claim priors)
  - StrategyReview → StrategyParamRecord (conditional probabilities / CPT)
  - GeneratedClaimReview → helper claim priors
  - Cromwell clamping: [eps, 1-eps]
  - Completeness validation
- Lowering to FactorGraph
  - IR Knowledge → Variable (with prior)
  - IR Strategy/Operator → Factor (8 factor types)
  - Named strategy → deterministic operator expansion
- BP algorithm
  - Sum-product loopy BP
  - Parameters: damping=0.5, max_iterations=100, convergence_threshold=1e-4
  - Convergence diagnostics
- Output format: parameterization.json + beliefs.json structure

#### `registration.md` — Registry Registration

`gaia register` and registry protocol.

- Prerequisites: [tool.gaia].uuid, git clean, tag exists and pushed
- Two modes
  - Dry-run (no --registry-dir): JSON plan to stdout
  - Write mode: generates Package.toml / Versions.toml / Deps.toml
- Registry metadata format (TOML examples)
- --create-pr flow: push branch + gh pr create
- Registry CI overview: untrusted sandbox → trusted gate → GitHub Releases + PEP 503 index
- Consumer perspective: `uv add <package>-gaia`

## Archive Plan

Move existing files to `docs/archive/foundations-v4/`:
- `gaia-lang/spec.md`
- `gaia-lang/knowledge-types.md`
- `gaia-lang/package-model.md`
- `cli/compiler.md`
- `cli/lifecycle.md`
- `cli/local-inference.md`
- `cli/local-storage.md`

## Cross-References

New docs must reference (not redefine):
- `docs/foundations/gaia-ir/` — Knowledge node schemas, FactorNode types, QID format
- `docs/foundations/bp/` — Factor potentials, BP algorithm details
- `docs/foundations/ecosystem/` — Decentralized architecture, registry model
- `docs/foundations/review/` — Review pipeline (when applicable)

## Non-Goals

- Rewriting gaia-ir/ docs (protected layer, unchanged)
- Documenting LKM server-side internals (separate from CLI/Lang docs)
- Writing user tutorials (these are foundation/architecture docs)
