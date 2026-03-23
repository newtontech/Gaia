# CLI Lifecycle

> **Status:** Current canonical

The Gaia CLI (`cli/main.py`) is a Typer application providing single-package interactive workflows. This document covers the full local lifecycle from init to publish.

## Workflow Overview

```
gaia init  ->  author  ->  gaia build  ->  [agent skills]  ->  gaia infer  ->  gaia publish
```

Additional utility commands: `gaia search`, `gaia clean`.

## Commands

### `gaia init <name>`

Scaffold a new Typst knowledge package with v4 DSL runtime.

- **Input**: package name.
- **Output**: a new directory with `typst.toml`, `lib.typ`, vendored `_gaia/` runtime, and template module files.
- **What it does**: copies the v4 runtime from `libs/typst/gaia-lang-v4/` and creates a minimal package structure.
- **What it does NOT do**: no compilation, no LLM calls, no network access.

### `gaia build [path]`

Deterministic lowering from Typst source to Graph IR.

- **Input**: package source (`.typ` files + `typst.toml`).
- **Output**: `.gaia/graph/raw_graph.json`, `.gaia/graph/local_canonical_graph.json`, `.gaia/graph/canonicalization_log.json`.
- **What it does**: validates package structure, extracts knowledge via `typst query`, compiles raw graph, builds singleton local canonical graph.
- **What it does NOT do**: no LLM calls, no search, no probability assignment.
- **Output formats**: `--format md` (default), `json`, `typst`, `all`.
- **Optional**: `--proof-state` flag runs `libs/lang/proof_state.analyze_proof_state()` and writes a proof state report.

Build runs the unified `pipeline_build()` from `libs/pipeline.py`:

```
typst_loader.load_typst_package_v4(pkg_path)
    -> compile_v4_to_raw_graph(graph_data)
    -> build_singleton_local_graph(raw_graph)
    -> save artifacts to .gaia/graph/ and .gaia/build/
```

### Agent Skills (optional, recommended)

Optional LLM-assisted steps between build and infer:

- **Self-review**: two-round LLM evaluation of reasoning quality. Produces candidate weak points and conditional priors as local sidecar artifacts.
- **Graph-construction**: inspects raw graph, clusters semantically similar nodes, produces refined local canonical graph and optional local parameterization.

If review discovers missing premises or references, the agent updates source and re-runs `gaia build`.

### `gaia infer [path]`

Local belief propagation preview.

- **Input**: local canonical graph + local parameterization overlay.
- **Output**: local belief preview under `.gaia/infer/infer_result.json`.
- **What it does**: adapts local canonical graph to a `FactorGraph`, derives parameterization from local review sidecars, runs sum-product BP with damping.
- **Scope**: package-local only. Does not query or modify the global graph.

`gaia infer` chains three pipeline functions:

1. `pipeline_build()` -- rebuild the package
2. `pipeline_review(build, mock=True)` -- derive priors and factor params via `MockReviewClient`
3. `pipeline_infer(build, review)` -- adapt graph to factor graph, run `BeliefPropagation`, output beliefs

For details on the BP algorithm: see [../bp/inference.md](../bp/inference.md). For factor potentials: see [../bp/potentials.md](../bp/potentials.md).

### `gaia publish [path]`

Submission handoff from local to shared system.

- **Input**: source + raw graph + local canonical graph + canonicalization log.
- **Output**: package submission to registry (local LanceDB or remote server).
- **What it does**: converts local canonical graph + review output to storage models, ingests via `StorageManager`.
- **What it does NOT submit**: author-local parameterization, self-review priors, local belief previews.
- **Modes**: `--git` (git-based), `--local` (LanceDB + Kuzu), `--server` (remote API, stubbed).

#### `gaia publish --local` Flow

The full four-step local publish pipeline:

1. `pipeline_build()` -- load and compile
2. `pipeline_review(build, mock=True)` -- mock review (LLM review not yet wired to CLI)
3. `pipeline_infer(build, review)` -- local BP
4. `pipeline_publish(build, review, infer, db_path=...)` -- convert Graph IR to storage models, three-write via `StorageManager` into LanceDB + Kuzu

The `--db-path` option (or `GAIA_LANCEDB_PATH` env var) controls the LanceDB location.

### `gaia search <query>`

BM25 full-text search over published knowledge in LanceDB.

- Primary: BM25 full-text search via LanceDB FTS index
- Fallback: SQL `LIKE` filter for CJK/unsegmented text
- `--id <knowledge_id>`: direct lookup with latest belief from `belief_history`

### `gaia clean [path]`

Remove `.gaia/` build artifacts from a package directory.

## Artifacts at Each Stage

| Stage | Key artifacts |
|---|---|
| Init | `typst.toml`, `lib.typ`, `_gaia/`, template `.typ` files |
| Source | `.typ` files, `typst.toml`, `gaia-deps.yml` |
| Build | `raw_graph.json`, `local_canonical_graph.json`, `canonicalization_log.json` |
| Self-review | review sidecars (candidate weak points, conditional priors) |
| Infer | `local_parameterization.json`, `infer_result.json` (belief preview) |
| Publish | submission to registry (source + raw + local canonical + log) |

## Code Paths

| Function | File |
|----------|------|
| CLI app + commands | `cli/main.py` |
| Pipeline functions | `libs/pipeline.py` (`pipeline_build`, `pipeline_review`, `pipeline_infer`, `pipeline_publish`) |
| Typst loader | `libs/lang/typst_loader.py` |
| Graph IR compiler | `libs/graph_ir/typst_compiler.py` |
| Mock/LLM review | `cli/llm_client.py` |
| BP engine | `libs/inference/bp.py` |
| Storage manager | `libs/storage/manager.py` |

## Current State

All commands are working. `publish --server` is stubbed (exits with "not yet implemented"). Review always uses `MockReviewClient` in the CLI; real LLM review is only available via the pipeline scripts.

## Target State

- Add `gaia review` command that invokes real LLM review via `ReviewClient` and saves a review sidecar file.
- Wire `publish --server` to the gateway API's `POST /packages/ingest` endpoint.
