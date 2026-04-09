# Gaia Render Command Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract presentation outputs (`docs/detailed-reasoning.md` and `.github-output/`) from `gaia compile` into a dedicated `gaia render` command that strictly requires inference results.

**Architecture:** New Typer command `gaia render` re-compiles the package (matching `gaia infer`'s pattern), verifies `.gaia/ir.json` and `.gaia/ir_hash` are fresh, loads a review sidecar via existing `load_gaia_review`, requires a matching `.gaia/reviews/<name>/beliefs.json` on disk (hard error if missing or stale), then delegates to the already-existing `generate_detailed_reasoning` and `generate_github_output` helpers based on `--target docs|github|all`. `gaia compile` loses its `--github` / `--module-graphs` / `--readme` flags (hard delete). `gaia register` is untouched. No deprecation window — callers must migrate.

Prep: the legacy `gaia/cli/commands/_readme.py` module (and its `generate_readme` function + its test file `tests/cli/test_readme.py`) are renamed to `_detailed_reasoning.py` / `generate_detailed_reasoning` / `test_detailed_reasoning.py` in a dedicated Chunk 0 commit before the render command is added. The name matches the actual output filename `docs/detailed-reasoning.md`; `readme` was a leftover from the deprecated `--readme` flag.

**Target naming:** `--target github` (not `site`) because the output is GitHub-specific (`.github-output/` with GitHub Wiki structure, GitHub-native Mermaid in README, React SPA scaffolded for GitHub Pages). Using `github` reserves `--target gitlab` / `--target docusaurus` etc. as future possibilities.

**Tech Stack:** Python 3.12, Typer, pytest, existing `gaia.cli` helpers (`load_gaia_package`, `load_gaia_review`, `compile_loaded_package_artifact`, `generate_detailed_reasoning`, `generate_github_output`).

**Motivation recap (for context):**
- `compile --github` currently reaches forward into `.gaia/reviews/` to grab the latest beliefs — dependency inversion across pipeline stages.
- When beliefs are missing, current code silently passes `beliefs_data=None` and produces a half-complete site — silent partial failure.
- `compile` should be a pure `DSL → IR` function; presentation belongs in a stage that runs *after* `infer`.

**Pipeline change:**
```
before: init → add → [write pkg] → compile (+ --github/--module-graphs) → [write review] → infer → git tag → register
after:  init → add → [write pkg] → compile → [write review] → infer → render → git tag → register
```

**Out of scope (explicitly):**
- Renaming `gaia register` to `gaia publish` / `gaia release` — user chose to leave it alone.
- Any `--push` / GitHub Pages deployment for `gaia render`.
- Refactoring `_github.py` or `_detailed_reasoning.py` (the renamed `_readme.py`) internals — they stay as-is; render just calls them.
- Touching `docs/foundations/gaia-ir/` or `docs/foundations/theory/` (protected layers).

---

## File Structure

**New files:**
- `gaia/cli/commands/render.py` — new command handler, ~130 lines, orchestrates existing helpers
- `tests/cli/test_render.py` — new test file, mirrors `tests/cli/test_infer.py` patterns

**Renamed files (Chunk 0):**
- `gaia/cli/commands/_readme.py` → `gaia/cli/commands/_detailed_reasoning.py`
- `tests/cli/test_readme.py` → `tests/cli/test_detailed_reasoning.py`
- Function `generate_readme` → `generate_detailed_reasoning` (inside the renamed file)

**Modified files:**
- `gaia/cli/main.py` — register `render` command in the Typer app
- `gaia/cli/commands/compile.py` — (1) update import from `_readme` → `_detailed_reasoning` in Chunk 0, (2) remove `--github` / `--module-graphs` / `--readme` options and their bodies (~55 lines deleted) in Chunk 4
- `gaia/cli/_reviews.py` — make the "multiple review sidecars" error message command-agnostic (drop `gaia infer` hardcode)
- `tests/cli/test_github_integration.py` — 2 CLI invocation tests (~lines 250, 281) migrated from `compile --github` to `render --target github`
- `tests/cli/test_detailed_reasoning.py` (post-rename) — 1 CLI invocation test (~line 246) migrated from `compile --readme` to `render --target docs`
- `docs/foundations/cli/workflow.md` — add `gaia render` section, update pipeline arrow diagram, add to Artifacts table
- `README.md` — update commands table, Quick Start workflow, top-of-file pipeline diagram
- `skills/gaia-cli/SKILL.md` — replace `compile --github` / `--module-graphs` / `--readme` references with `render --target ...`
- `skills/gaia/SKILL.md` — same
- `skills/publish/SKILL.md` — same (the `/gaia:publish` skill's Step 1 becomes `gaia render --target github`)
- `skills/formalization/SKILL.md` — same

**Unchanged (verified):**
- `gaia/cli/commands/_github.py` — `generate_github_output()` keeps its signature with `beliefs_data: dict | None` (pure function, still allows `None` for unit tests)
- `gaia/cli/commands/_detailed_reasoning.py` (post-rename) — `generate_detailed_reasoning()` keeps its signature with `beliefs_data: dict | None` (contents are not edited in Chunk 0; only the file name, module docstring, and top-level function name change)
- `tests/cli/test_github_react.py` — all 4 tests call `generate_github_output()` as a pure function, no CLI invocation
- `tests/cli/test_github_integration.py` unit tests (lines ~30–245) — same, pure function calls
- `tests/cli/test_detailed_reasoning.py` (post-rename) unit tests for `generate_detailed_reasoning()` — same
- `tests/cli/test_compile.py` — does not reference any of the removed flags

---

## Chunk 0: Rename `_readme.py` → `_detailed_reasoning.py`

Mechanical rename prep so the rest of the plan can reference the new names. No behavioral changes — contents of the renamed file are byte-identical except for the module docstring, the top-level function name, and any internal self-references.

### Task 0: Rename module, function, and test file

**Files:**
- Rename: `gaia/cli/commands/_readme.py` → `gaia/cli/commands/_detailed_reasoning.py`
- Rename: `tests/cli/test_readme.py` → `tests/cli/test_detailed_reasoning.py`
- Modify: the renamed `_detailed_reasoning.py` (function rename + docstring)
- Modify: the renamed `test_detailed_reasoning.py` (import updates)
- Modify: `gaia/cli/commands/compile.py` (import update only — flag removal comes in Chunk 4)

- [ ] **Step 1: Rename the source file with `git mv`**

```bash
git mv gaia/cli/commands/_readme.py gaia/cli/commands/_detailed_reasoning.py
```

- [ ] **Step 2: Update the module docstring and the top-level function name inside the renamed file**

In `gaia/cli/commands/_detailed_reasoning.py`:

Replace the module docstring at line 1:

```python
"""gaia compile --readme: generate README.md from compiled IR."""
```

with:

```python
"""Generate docs/detailed-reasoning.md — per-module reasoning doc — from compiled IR."""
```

Rename the top-level orchestrator function. Find (around line 635):

```python
def generate_readme(
    ir: dict,
    pkg_metadata: dict,
    beliefs_data: dict | None = None,
    param_data: dict | None = None,
) -> str:
    """Generate full README.md content from compiled IR and optional inference results."""
```

Replace with:

```python
def generate_detailed_reasoning(
    ir: dict,
    pkg_metadata: dict,
    beliefs_data: dict | None = None,
    param_data: dict | None = None,
) -> str:
    """Generate detailed-reasoning.md content from compiled IR and optional inference results."""
```

Do **not** rename the internal helpers (`render_mermaid`, `render_knowledge_nodes`, `render_inference_results`, `topo_layers`, `_render_node`, `_render_overview_graph`, `_render_introduction`, etc.). They keep their current names — they are implementation details and nothing outside this file imports them by name (except tests, which import them explicitly by name and will be updated in Step 4).

- [ ] **Step 3: Rename the test file with `git mv`**

```bash
git mv tests/cli/test_readme.py tests/cli/test_detailed_reasoning.py
```

- [ ] **Step 4: Update imports in the renamed test file**

In `tests/cli/test_detailed_reasoning.py`, find every import of the form:

```python
from gaia.cli.commands._readme import generate_readme
```

(there is at least one at the top of the file around line 7, plus several inline imports in test bodies around lines 475, 517, 580, 600) and replace with:

```python
from gaia.cli.commands._detailed_reasoning import generate_detailed_reasoning
```

Then find every call site of `generate_readme(` inside the test bodies and replace with `generate_detailed_reasoning(`. Use a plain text search to be sure:

```bash
grep -n 'generate_readme\|_readme' tests/cli/test_detailed_reasoning.py
```

Expected after edits: zero hits.

- [ ] **Step 5: Update the import and call in `gaia/cli/commands/compile.py`**

In the CURRENT `compile.py` (not yet trimmed — that's Chunk 4), find the import inside the `module_graphs or readme` branch:

```python
    if module_graphs or readme:
        from gaia.cli.commands._readme import generate_readme

        content = generate_readme(
            ir, loaded.project_config, beliefs_data=beliefs_data, param_data=param_data
        )
```

Replace with:

```python
    if module_graphs or readme:
        from gaia.cli.commands._detailed_reasoning import generate_detailed_reasoning

        content = generate_detailed_reasoning(
            ir, loaded.project_config, beliefs_data=beliefs_data, param_data=param_data
        )
```

(This import and branch will be deleted entirely in Chunk 4; we only rename it here so Chunk 0 leaves the tree in a working state.)

- [ ] **Step 6: Verify no stale references remain**

Run:
```bash
grep -rn 'generate_readme\|_readme\.py\|from gaia\.cli\.commands\._readme' gaia tests
```

Expected: zero hits. If any remain (e.g., in a test file we missed), update them.

- [ ] **Step 7: Run the full CLI test suite**

Run: `uv run pytest tests/cli -x`
Expected: all pass. The renamed `test_detailed_reasoning.py` runs its unit tests against the renamed function; `test_compile.py` is unaffected; `test_github_integration.py` and `test_infer.py` still work.

- [ ] **Step 8: Ruff check**

Run: `ruff check gaia tests && ruff format --check gaia tests`
Expected: no errors.

- [ ] **Step 9: Commit Chunk 0**

```bash
git add -A gaia/cli/commands/ tests/cli/
git commit -m "refactor(cli): rename _readme.py → _detailed_reasoning.py

The module was named after the deprecated --readme flag but its actual
output is docs/detailed-reasoning.md. Rename the file, function, and
test file to match. No behavioral changes — this is prep for the
upcoming gaia render command that will import the new name."
```

---

## Chunk 1: `gaia render` scaffolding + happy path

### Task 1: Create `gaia/cli/commands/render.py` with skeleton

**Files:**
- Create: `gaia/cli/commands/render.py`

- [ ] **Step 1: Create the file with the skeleton shown below**

```python
"""gaia render -- generate presentation outputs (docs and/or GitHub site) from a reviewed package."""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path

import typer

from gaia.cli._packages import (
    GaiaCliError,
    compile_loaded_package_artifact,
    load_gaia_package,
)
from gaia.cli._reviews import load_gaia_review
from gaia.ir.validator import validate_local_graph


class RenderTarget(str, Enum):
    docs = "docs"
    github = "github"
    all = "all"


def render_command(
    path: str = typer.Argument(".", help="Path to knowledge package directory"),
    review: str | None = typer.Option(
        None,
        "--review",
        help=(
            "Review sidecar name from <package>/reviews/<name>.py. "
            "Auto-selected when only one sidecar exists."
        ),
    ),
    target: RenderTarget = typer.Option(
        RenderTarget.all,
        "--target",
        help="What to render: 'docs', 'github', or 'all' (default).",
    ),
) -> None:
    """Render presentation outputs (docs and/or GitHub site) from a reviewed package.

    Requires `gaia compile` and `gaia infer` to have been run successfully first.
    """
    raise NotImplementedError
```

- [ ] **Step 2: Verify it imports cleanly**

Run: `uv run python -c "from gaia.cli.commands.render import render_command, RenderTarget"`
Expected: no output, exit code 0.

---

### Task 2: Register `render` in `gaia/cli/main.py`

**Files:**
- Modify: `gaia/cli/main.py`

- [ ] **Step 1: Add the import and the `app.command` registration**

In `gaia/cli/main.py`, after the existing `from gaia.cli.commands.register import register_command` line, add:

```python
from gaia.cli.commands.render import render_command
```

And after the existing `app.command(name="register")(register_command)` line, add:

```python
app.command(name="render")(render_command)
```

- [ ] **Step 2: Verify Typer sees the command**

Run: `uv run gaia render --help`
Expected: help text showing `--review` and `--target` options; exit code 0 (even though body raises NotImplementedError, --help short-circuits).

- [ ] **Step 3: Commit the scaffolding**

```bash
git add gaia/cli/commands/render.py gaia/cli/main.py
git commit -m "feat(cli): scaffold gaia render command"
```

---

### Task 3: Happy-path test for `gaia render --target all` (failing)

**Files:**
- Create: `tests/cli/test_render.py`

- [ ] **Step 1: Create the test file with fixture helpers and the happy-path test**

```python
"""Tests for gaia render command."""

from __future__ import annotations

import json

from typer.testing import CliRunner

from gaia.cli.main import app

runner = CliRunner()


def _write_base_package(pkg_dir, *, name: str, version: str = "1.0.0") -> None:
    pkg_dir.mkdir()
    (pkg_dir / "pyproject.toml").write_text(
        f'[project]\nname = "{name}-gaia"\nversion = "{version}"\n'
        'description = "Test package."\n\n'
        '[tool.gaia]\nnamespace = "github"\ntype = "knowledge-package"\n'
    )
    (pkg_dir / name).mkdir()


def _write_minimal_source(pkg_dir, name: str) -> None:
    (pkg_dir / name / "__init__.py").write_text(
        "from gaia.lang import claim, noisy_and\n\n"
        'evidence_a = claim("Observed evidence A.")\n'
        'evidence_b = claim("Observed evidence B.")\n'
        'hypothesis = claim("Main hypothesis.")\n'
        "support = noisy_and(premises=[evidence_a, evidence_b], conclusion=hypothesis)\n"
        '__all__ = ["evidence_a", "evidence_b", "hypothesis", "support"]\n'
    )


def _write_review(pkg_dir, package_name: str, review_name: str) -> None:
    reviews_dir = pkg_dir / package_name / "reviews"
    reviews_dir.mkdir(exist_ok=True)
    (reviews_dir / f"{review_name}.py").write_text(
        "from gaia.review import ReviewBundle, review_claim, review_strategy\n"
        "from .. import evidence_a, evidence_b, hypothesis, support\n\n"
        "REVIEW = ReviewBundle(\n"
        f'    source_id="{review_name}",\n'
        "    objects=[\n"
        '        review_claim(evidence_a, prior=0.9, judgment="strong", justification="Direct observation."),\n'
        '        review_claim(evidence_b, prior=0.8, judgment="supporting", justification="A second reinforcing observation."),\n'
        '        review_claim(hypothesis, prior=0.4, judgment="tentative", justification="Base rate before support."),\n'
        '        review_strategy(support, conditional_probability=0.85, judgment="good", justification="The evidence usually supports the hypothesis."),\n'
        "    ],\n"
        ")\n"
    )


def _prepare_inferred_package(tmp_path, name: str = "render_demo") -> "Path":
    """Create a package, write a review, compile and infer it. Returns pkg_dir."""
    pkg_dir = tmp_path / name
    _write_base_package(pkg_dir, name=name)
    _write_minimal_source(pkg_dir, name)
    _write_review(pkg_dir, name, "self_review")

    compile_result = runner.invoke(app, ["compile", str(pkg_dir)])
    assert compile_result.exit_code == 0, compile_result.output
    infer_result = runner.invoke(app, ["infer", str(pkg_dir)])
    assert infer_result.exit_code == 0, infer_result.output
    return pkg_dir


def test_render_target_all_writes_docs_and_github(tmp_path):
    """Happy path: render --target all (default) writes both docs and github outputs."""
    pkg_dir = _prepare_inferred_package(tmp_path)

    result = runner.invoke(app, ["render", str(pkg_dir)])
    assert result.exit_code == 0, result.output

    docs_path = pkg_dir / "docs" / "detailed-reasoning.md"
    assert docs_path.exists(), "render should write docs/detailed-reasoning.md"
    assert "# render_demo-gaia" in docs_path.read_text() or "# render_demo" in docs_path.read_text()

    github_dir = pkg_dir / ".github-output"
    assert (github_dir / "wiki" / "Home.md").exists()
    assert (github_dir / "manifest.json").exists()
    assert (github_dir / "docs" / "public" / "data" / "graph.json").exists()
    assert (github_dir / "README.md").exists()
```

- [ ] **Step 2: Run the test — it must fail with NotImplementedError**

Run: `uv run pytest tests/cli/test_render.py::test_render_target_all_writes_docs_and_github -xvs`
Expected: FAIL with `NotImplementedError` (or similar) — this proves the test hits the stub body.

---

### Task 4: Implement `render_command` body

**Files:**
- Modify: `gaia/cli/commands/render.py`

- [ ] **Step 1: Replace the stub body with the full implementation**

Replace the `raise NotImplementedError` with the following implementation. Also add imports for `generate_github_output` and `generate_detailed_reasoning` at the top.

Updated imports block:

```python
from gaia.cli._packages import (
    GaiaCliError,
    compile_loaded_package_artifact,
    load_gaia_package,
)
from gaia.cli._reviews import load_gaia_review
from gaia.cli.commands._detailed_reasoning import generate_detailed_reasoning
from gaia.cli.commands._github import generate_github_output
from gaia.ir.validator import validate_local_graph
```

Full body:

```python
def render_command(
    path: str = typer.Argument(".", help="Path to knowledge package directory"),
    review: str | None = typer.Option(
        None,
        "--review",
        help=(
            "Review sidecar name from <package>/reviews/<name>.py. "
            "Auto-selected when only one sidecar exists."
        ),
    ),
    target: RenderTarget = typer.Option(
        RenderTarget.all,
        "--target",
        help="What to render: 'docs', 'github', or 'all' (default).",
    ),
) -> None:
    """Render presentation outputs (docs and/or GitHub site) from a reviewed package.

    Requires `gaia compile` and `gaia infer` to have been run successfully first.
    """
    try:
        loaded = load_gaia_package(path)
        compiled = compile_loaded_package_artifact(loaded)
    except GaiaCliError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1)

    # Validate IR structure (same gate as compile/infer)
    graph_validation = validate_local_graph(compiled.graph)
    for warning in graph_validation.warnings:
        typer.echo(f"Warning: {warning}")
    if graph_validation.errors:
        for error in graph_validation.errors:
            typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(1)

    ir = compiled.to_json()

    # ── Verify compile artifacts are fresh (same pattern as infer.py) ──
    gaia_dir = loaded.pkg_path / ".gaia"
    ir_hash_path = gaia_dir / "ir_hash"
    ir_json_path = gaia_dir / "ir.json"
    if not ir_hash_path.exists() or not ir_json_path.exists():
        typer.echo(
            "Error: missing compiled artifacts; run `gaia compile` first.", err=True
        )
        raise typer.Exit(1)
    if ir_hash_path.read_text().strip() != compiled.graph.ir_hash:
        typer.echo(
            "Error: compiled artifacts are stale; run `gaia compile` again.", err=True
        )
        raise typer.Exit(1)
    try:
        stored_ir = json.loads(ir_json_path.read_text())
    except json.JSONDecodeError as exc:
        typer.echo(f"Error: .gaia/ir.json is not valid JSON: {exc}", err=True)
        raise typer.Exit(1)
    if stored_ir.get("ir_hash") != compiled.graph.ir_hash or stored_ir != ir:
        typer.echo(
            "Error: compiled artifacts are stale; run `gaia compile` again.", err=True
        )
        raise typer.Exit(1)

    # ── Load review sidecar (auto-select if only one exists) ──
    try:
        loaded_review = load_gaia_review(loaded, review_name=review)
        if loaded_review is None:
            raise GaiaCliError(
                "Error: missing review sidecar. Create <package>/review.py or "
                "<package>/reviews/<name>.py with REVIEW = ReviewBundle(...), "
                "then run `gaia infer` before `gaia render`."
            )
    except GaiaCliError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1)

    # ── Require inference results on disk (strict — no silent None) ──
    review_dir = gaia_dir / "reviews" / loaded_review.name
    beliefs_path = review_dir / "beliefs.json"
    param_path = review_dir / "parameterization.json"
    if not beliefs_path.exists():
        typer.echo(
            f"Error: missing beliefs for review {loaded_review.name!r}; "
            f"run `gaia infer --review {loaded_review.name}` first.",
            err=True,
        )
        raise typer.Exit(1)

    try:
        beliefs_data = json.loads(beliefs_path.read_text())
    except json.JSONDecodeError as exc:
        typer.echo(f"Error: {beliefs_path} is not valid JSON: {exc}", err=True)
        raise typer.Exit(1)

    if beliefs_data.get("ir_hash") != compiled.graph.ir_hash:
        typer.echo(
            f"Error: beliefs for review {loaded_review.name!r} are stale; "
            f"run `gaia infer --review {loaded_review.name}` again.",
            err=True,
        )
        raise typer.Exit(1)

    param_data: dict | None = None
    if param_path.exists():
        try:
            param_data = json.loads(param_path.read_text())
        except json.JSONDecodeError as exc:
            typer.echo(f"Error: {param_path} is not valid JSON: {exc}", err=True)
            raise typer.Exit(1)

    # ── Dispatch to generators ──
    want_docs = target in (RenderTarget.docs, RenderTarget.all)
    want_github = target in (RenderTarget.github, RenderTarget.all)

    if want_docs:
        content = generate_detailed_reasoning(
            ir,
            loaded.project_config,
            beliefs_data=beliefs_data,
            param_data=param_data,
        )
        docs_out = loaded.pkg_path / "docs" / "detailed-reasoning.md"
        docs_out.parent.mkdir(parents=True, exist_ok=True)
        docs_out.write_text(content)
        typer.echo(f"Docs: {docs_out}")

    if want_github:
        exported_ids = {
            k["id"] for k in ir.get("knowledges", []) if k.get("exported")
        }
        github_out = generate_github_output(
            ir,
            loaded.pkg_path,
            beliefs_data=beliefs_data,
            param_data=param_data,
            exported_ids=exported_ids,
            pkg_metadata=loaded.project_config,
        )
        typer.echo(f"GitHub: {github_out}")

    typer.echo(f"Review: {loaded_review.name}")
```

Note: `validate_local_graph` takes `compiled.graph` directly (matching `infer.py:37`), so no `LocalCanonicalGraph` import is needed in `render.py`. If ruff flags any unused import, remove it.

- [ ] **Step 2: Run the happy-path test again**

Run: `uv run pytest tests/cli/test_render.py::test_render_target_all_writes_docs_and_github -xvs`
Expected: PASS.

- [ ] **Step 3: Commit the working happy path**

```bash
git add gaia/cli/commands/render.py tests/cli/test_render.py
git commit -m "feat(cli): implement gaia render happy path (--target all)"
```

---

## Chunk 2: Error-handling paths

### Task 5: Tests for missing / stale IR artifacts and missing review

**Files:**
- Modify: `tests/cli/test_render.py`

- [ ] **Step 1: Append tests for each error condition**

Append to the end of `tests/cli/test_render.py`:

```python
def test_render_fails_when_ir_artifacts_missing(tmp_path):
    """render before compile → error about missing compiled artifacts."""
    pkg_dir = tmp_path / "no_compile"
    _write_base_package(pkg_dir, name="no_compile")
    _write_minimal_source(pkg_dir, "no_compile")
    _write_review(pkg_dir, "no_compile", "self_review")

    result = runner.invoke(app, ["render", str(pkg_dir)])
    assert result.exit_code != 0
    assert "missing compiled artifacts" in result.output


def test_render_fails_when_ir_stale(tmp_path):
    """render when source changed after compile → stale-artifact error."""
    pkg_dir = _prepare_inferred_package(tmp_path, name="stale_ir")

    # Mutate source so re-compile yields a different ir_hash
    (pkg_dir / "stale_ir" / "__init__.py").write_text(
        "from gaia.lang import claim, noisy_and\n\n"
        'evidence_a = claim("Observed evidence A (edited).")\n'
        'evidence_b = claim("Observed evidence B.")\n'
        'hypothesis = claim("Main hypothesis.")\n'
        "support = noisy_and(premises=[evidence_a, evidence_b], conclusion=hypothesis)\n"
        '__all__ = ["evidence_a", "evidence_b", "hypothesis", "support"]\n'
    )

    result = runner.invoke(app, ["render", str(pkg_dir)])
    assert result.exit_code != 0
    assert "stale" in result.output.lower()


def test_render_fails_when_no_review_sidecar(tmp_path):
    """render when no review.py / reviews/*.py exists → missing review error."""
    pkg_dir = tmp_path / "no_review"
    _write_base_package(pkg_dir, name="no_review")
    _write_minimal_source(pkg_dir, "no_review")

    compile_result = runner.invoke(app, ["compile", str(pkg_dir)])
    assert compile_result.exit_code == 0

    result = runner.invoke(app, ["render", str(pkg_dir)])
    assert result.exit_code != 0
    assert "review" in result.output.lower()


def test_render_fails_when_beliefs_missing(tmp_path):
    """render after compile but before infer → missing beliefs error."""
    pkg_dir = tmp_path / "no_infer"
    _write_base_package(pkg_dir, name="no_infer")
    _write_minimal_source(pkg_dir, "no_infer")
    _write_review(pkg_dir, "no_infer", "self_review")

    compile_result = runner.invoke(app, ["compile", str(pkg_dir)])
    assert compile_result.exit_code == 0

    result = runner.invoke(app, ["render", str(pkg_dir)])
    assert result.exit_code != 0
    assert "beliefs" in result.output.lower()
    assert "gaia infer" in result.output


def test_render_fails_when_beliefs_stale(tmp_path):
    """render when beliefs.json has a wrong ir_hash → stale beliefs error."""
    pkg_dir = _prepare_inferred_package(tmp_path, name="stale_beliefs")
    beliefs_path = pkg_dir / ".gaia" / "reviews" / "self_review" / "beliefs.json"
    beliefs = json.loads(beliefs_path.read_text())
    beliefs["ir_hash"] = "not-the-real-hash"
    beliefs_path.write_text(json.dumps(beliefs))

    result = runner.invoke(app, ["render", str(pkg_dir)])
    assert result.exit_code != 0
    assert "stale" in result.output.lower()
    assert "beliefs" in result.output.lower()
```

- [ ] **Step 2: Run the new tests**

Run: `uv run pytest tests/cli/test_render.py -xvs`
Expected: all 6 tests PASS (the impl from Task 4 already covers these branches; if any fail, fix `render.py`).

- [ ] **Step 3: Commit**

```bash
git add tests/cli/test_render.py
git commit -m "test(cli): add error-path tests for gaia render"
```

---

## Chunk 3: Target filtering and multi-review selection

### Task 6: Make `_reviews.py` error message command-agnostic

**Files:**
- Modify: `gaia/cli/_reviews.py:119-123`

- [ ] **Step 1: Change the error message**

In `gaia/cli/_reviews.py`, find the block that raises when multiple sidecars are found (currently around line 119–123):

```python
        else:
            available = ", ".join(sorted(candidates))
            raise GaiaCliError(
                "Error: multiple review sidecars found; choose one with "
                f"`gaia infer --review <name>`. Available: {available}"
            )
```

Replace with:

```python
        else:
            available = ", ".join(sorted(candidates))
            raise GaiaCliError(
                "Error: multiple review sidecars found; choose one with "
                f"`--review <name>`. Available: {available}"
            )
```

- [ ] **Step 2: Verify infer tests still pass**

Run: `uv run pytest tests/cli/test_infer.py -xvs`
Expected: all pass. (If any test asserts on the exact `gaia infer --review` substring, update that assertion to match the new command-agnostic form.)

---

### Task 7: Test + impl: multi-review selection

**Files:**
- Modify: `tests/cli/test_render.py`

- [ ] **Step 1: Append multi-review tests**

```python
def _write_second_review(pkg_dir, package_name: str, review_name: str) -> None:
    reviews_dir = pkg_dir / package_name / "reviews"
    (reviews_dir / f"{review_name}.py").write_text(
        "from gaia.review import ReviewBundle, review_claim, review_strategy\n"
        "from .. import evidence_a, evidence_b, hypothesis, support\n\n"
        "REVIEW = ReviewBundle(\n"
        f'    source_id="{review_name}",\n'
        "    objects=[\n"
        '        review_claim(evidence_a, prior=0.5, judgment="tentative", justification="Alt."),\n'
        '        review_claim(evidence_b, prior=0.5, judgment="tentative", justification="Alt."),\n'
        '        review_claim(hypothesis, prior=0.5, judgment="tentative", justification="Alt."),\n'
        '        review_strategy(support, conditional_probability=0.5, judgment="weak", justification="Alt."),\n'
        "    ],\n"
        ")\n"
    )


def test_render_fails_when_multiple_reviews_without_flag(tmp_path):
    """Two review sidecars and no --review → error listing candidates."""
    pkg_dir = _prepare_inferred_package(tmp_path, name="multi_review")
    _write_second_review(pkg_dir, "multi_review", "alt_review")
    # Run infer for the second review so both have beliefs on disk
    alt_infer = runner.invoke(app, ["infer", str(pkg_dir), "--review", "alt_review"])
    assert alt_infer.exit_code == 0, alt_infer.output

    result = runner.invoke(app, ["render", str(pkg_dir)])
    assert result.exit_code != 0
    assert "multiple review sidecars" in result.output
    assert "self_review" in result.output
    assert "alt_review" in result.output


def test_render_selects_named_review(tmp_path):
    """--review <name> selects that review's beliefs for rendering."""
    pkg_dir = _prepare_inferred_package(tmp_path, name="named_review")
    _write_second_review(pkg_dir, "named_review", "alt_review")
    alt_infer = runner.invoke(app, ["infer", str(pkg_dir), "--review", "alt_review"])
    assert alt_infer.exit_code == 0, alt_infer.output

    result = runner.invoke(app, ["render", str(pkg_dir), "--review", "alt_review"])
    assert result.exit_code == 0, result.output
    assert "Review: alt_review" in result.output
```

- [ ] **Step 2: Run the new tests**

Run: `uv run pytest tests/cli/test_render.py::test_render_fails_when_multiple_reviews_without_flag tests/cli/test_render.py::test_render_selects_named_review -xvs`
Expected: PASS (implementation from Task 4 already delegates to `load_gaia_review` which handles this).

---

### Task 8: Tests for `--target` filtering

**Files:**
- Modify: `tests/cli/test_render.py`

- [ ] **Step 1: Append target-filter tests**

```python
def test_render_target_docs_only(tmp_path):
    """--target docs creates docs/detailed-reasoning.md but not .github-output/."""
    pkg_dir = _prepare_inferred_package(tmp_path, name="docs_only")

    result = runner.invoke(app, ["render", str(pkg_dir), "--target", "docs"])
    assert result.exit_code == 0, result.output

    assert (pkg_dir / "docs" / "detailed-reasoning.md").exists()
    assert not (pkg_dir / ".github-output").exists()
    assert "Docs:" in result.output
    assert "GitHub:" not in result.output


def test_render_target_github_only(tmp_path):
    """--target github creates .github-output/ but not docs/detailed-reasoning.md."""
    pkg_dir = _prepare_inferred_package(tmp_path, name="github_only")

    result = runner.invoke(app, ["render", str(pkg_dir), "--target", "github"])
    assert result.exit_code == 0, result.output

    assert (pkg_dir / ".github-output" / "manifest.json").exists()
    assert not (pkg_dir / "docs" / "detailed-reasoning.md").exists()
    assert "GitHub:" in result.output
    assert "Docs:" not in result.output


def test_render_target_all_is_default(tmp_path):
    """Omitting --target is the same as --target all."""
    pkg_dir = _prepare_inferred_package(tmp_path, name="all_default")

    result = runner.invoke(app, ["render", str(pkg_dir)])
    assert result.exit_code == 0, result.output
    assert (pkg_dir / "docs" / "detailed-reasoning.md").exists()
    assert (pkg_dir / ".github-output" / "manifest.json").exists()
```

- [ ] **Step 2: Run the target tests**

Run: `uv run pytest tests/cli/test_render.py -xvs -k target`
Expected: all 3 PASS.

- [ ] **Step 3: Commit Chunk 3**

```bash
git add gaia/cli/_reviews.py tests/cli/test_render.py
git commit -m "feat(cli): gaia render multi-review selection and --target filtering"
```

---

## Chunk 4: Remove flags from `compile` and migrate existing tests

### Task 9: Delete presentation flags from `gaia compile`

**Files:**
- Modify: `gaia/cli/commands/compile.py`

- [ ] **Step 1: Replace the entire `compile.py` body**

The current file is 109 lines with three presentation branches. Replace with the trimmed version:

```python
"""gaia compile -- compile Python DSL package to Gaia IR v2 JSON."""

from __future__ import annotations

import typer

from gaia.cli._packages import (
    GaiaCliError,
    build_package_manifests,
    compile_loaded_package_artifact,
    load_gaia_package,
    write_compiled_artifacts,
)
from gaia.ir import LocalCanonicalGraph
from gaia.ir.validator import validate_local_graph


def compile_command(
    path: str = typer.Argument(".", help="Path to knowledge package directory"),
) -> None:
    """Compile a knowledge package to .gaia/ir.json."""
    try:
        loaded = load_gaia_package(path)
        compiled = compile_loaded_package_artifact(loaded)
        ir = compiled.to_json()
        manifests = build_package_manifests(loaded, compiled)
    except GaiaCliError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1)

    validation = validate_local_graph(LocalCanonicalGraph(**ir))
    for warning in validation.warnings:
        typer.echo(f"Warning: {warning}")
    if validation.errors:
        for error in validation.errors:
            typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(1)

    gaia_dir = write_compiled_artifacts(loaded.pkg_path, ir, manifests=manifests)

    typer.echo(
        f"Compiled {len(ir['knowledges'])} knowledge, "
        f"{len(ir['strategies'])} strategies, "
        f"{len(ir['operators'])} operators"
    )
    typer.echo(f"IR hash: {ir['ir_hash'][:16]}...")
    typer.echo(f"Output: {gaia_dir / 'ir.json'}")
```

- [ ] **Step 2: Verify compile tests still pass**

Run: `uv run pytest tests/cli/test_compile.py -x`
Expected: all pass — `test_compile.py` does not reference any removed flag (verified by grep during plan drafting).

- [ ] **Step 3: Verify the removed flags are actually gone**

Run: `uv run gaia compile --help`
Expected: help text shows only `PATH`, no `--github` / `--module-graphs` / `--readme`.

---

### Task 10: Migrate `tests/cli/test_github_integration.py` CLI tests

**Files:**
- Modify: `tests/cli/test_github_integration.py:250-379` (the two CLI-invocation tests)

**Context:** The two tests at `test_compile_github_flag` (~line 250) and `test_github_output_with_real_package` (~line 281) currently invoke `runner.invoke(app, ["compile", str(pkg_dir), "--github"])`. They do not run infer, so they rely on the old silent `beliefs_data=None` behavior. Under strict mode, render requires beliefs, so these tests now need to (a) create a review sidecar, (b) run `gaia infer`, (c) then invoke `gaia render --target github`.

- [ ] **Step 1: Update `test_compile_github_flag`**

Replace the test body (starting from the `pkg_src / "__init__.py"` write and continuing through the assertions) with:

```python
def test_render_github_flag(tmp_path):
    """gaia render --target github generates .github-output/ with expected structure."""
    pkg_dir = tmp_path / "github_pkg"
    pkg_dir.mkdir()
    (pkg_dir / "pyproject.toml").write_text(
        '[project]\nname = "github-pkg-gaia"\nversion = "1.0.0"\n'
        'description = "A test package."\n\n'
        '[tool.gaia]\nnamespace = "github"\ntype = "knowledge-package"\n'
    )
    pkg_src = pkg_dir / "github_pkg"
    pkg_src.mkdir()
    (pkg_src / "__init__.py").write_text(
        "from gaia.lang import claim, noisy_and\n\n"
        'a = claim("Premise A.")\n'
        'b = claim("Premise B.")\n'
        'c = claim("Conclusion.")\n'
        "s = noisy_and([a, b], c)\n"
        '__all__ = ["a", "b", "c", "s"]\n'
    )
    reviews_dir = pkg_src / "reviews"
    reviews_dir.mkdir()
    (reviews_dir / "self_review.py").write_text(
        "from gaia.review import ReviewBundle, review_claim, review_strategy\n"
        "from .. import a, b, c, s\n\n"
        "REVIEW = ReviewBundle(\n"
        '    source_id="self_review",\n'
        "    objects=[\n"
        '        review_claim(a, prior=0.8, judgment="ok", justification="."),\n'
        '        review_claim(b, prior=0.8, judgment="ok", justification="."),\n'
        '        review_claim(c, prior=0.4, judgment="ok", justification="."),\n'
        '        review_strategy(s, conditional_probability=0.85, judgment="ok", justification="."),\n'
        "    ],\n"
        ")\n"
    )

    assert runner.invoke(app, ["compile", str(pkg_dir)]).exit_code == 0
    assert runner.invoke(app, ["infer", str(pkg_dir)]).exit_code == 0

    result = runner.invoke(app, ["render", str(pkg_dir), "--target", "github"])
    assert result.exit_code == 0, f"Failed: {result.output}"
    assert "GitHub:" in result.output

    output_dir = pkg_dir / ".github-output"
    assert (output_dir / "wiki" / "Home.md").exists()
    assert (output_dir / "manifest.json").exists()
    assert (output_dir / "docs" / "public" / "data" / "graph.json").exists()
    assert (output_dir / "README.md").exists()
```

Rename the function from `test_compile_github_flag` to `test_render_github_flag` (the old name no longer describes what is tested).

- [ ] **Step 2: Update `test_github_output_with_real_package`**

This test (currently ~line 281) constructs a Galileo-like multi-module package. Rename to `test_render_github_with_real_package` and update the invocation. Find the two places where it calls `runner.invoke(app, ["compile", str(pkg_dir), "--github"])` and the per-invocation assertion `assert "GitHub output:" in result.output`.

Insert a review sidecar file before the render invocation (add to the package construction section, after the `__init__.py` write at ~line 319):

```python
    # Review sidecar — required for render
    (pkg_src / "reviews").mkdir()
    (pkg_src / "reviews" / "self_review.py").write_text(
        "from gaia.review import ReviewBundle, review_claim\n"
        "from ..motivation import context, obs_equal_time\n"
        "from ..analysis import aristotle_hyp, galileo_hyp\n\n"
        "REVIEW = ReviewBundle(\n"
        '    source_id="self_review",\n'
        "    objects=[\n"
        '        review_claim(context, prior=0.95, judgment="ok", justification="."),\n'
        '        review_claim(obs_equal_time, prior=0.9, judgment="ok", justification="."),\n'
        '        review_claim(aristotle_hyp, prior=0.2, judgment="ok", justification="."),\n'
        '        review_claim(galileo_hyp, prior=0.6, judgment="ok", justification="."),\n'
        "    ],\n"
        ")\n"
    )
```

Replace the two places that run `compile --github` with:

```python
    assert runner.invoke(app, ["compile", str(pkg_dir)]).exit_code == 0
    assert runner.invoke(app, ["infer", str(pkg_dir)]).exit_code == 0
    result = runner.invoke(app, ["render", str(pkg_dir), "--target", "github"])
    assert result.exit_code == 0, f"Failed: {result.output}"
    assert "GitHub:" in result.output
```

(Remove the old `"GitHub output:"` assertion — the new output says `GitHub:` instead.)

- [ ] **Step 3: Run the migrated tests**

Run: `uv run pytest tests/cli/test_github_integration.py -xvs`
Expected: all pass (both unit tests for `generate_github_output()` and the two migrated CLI tests).

---

### Task 11: Migrate `tests/cli/test_detailed_reasoning.py` CLI test

**Files:**
- Modify: `tests/cli/test_detailed_reasoning.py` (the CLI integration test around line 246-275; line numbers may have shifted slightly after Chunk 0's rename — search for `test_compile_readme_flag_generates_readme`)

- [ ] **Step 1: Update the CLI integration test**

Replace `test_compile_readme_flag_generates_readme` with:

```python
def test_render_docs_flag_generates_detailed_reasoning(tmp_path):
    """gaia render --target docs writes docs/detailed-reasoning.md."""
    pkg_dir = tmp_path / "readme_pkg"
    pkg_dir.mkdir()
    (pkg_dir / "pyproject.toml").write_text(
        '[project]\nname = "readme-pkg-gaia"\nversion = "1.0.0"\n'
        'description = "A test package."\n\n'
        '[tool.gaia]\nnamespace = "github"\ntype = "knowledge-package"\n'
    )
    pkg_src = pkg_dir / "readme_pkg"
    pkg_src.mkdir()
    (pkg_src / "__init__.py").write_text(
        "from gaia.lang import claim, noisy_and\n\n"
        'a = claim("Premise A.")\n'
        'b = claim("Premise B.")\n'
        'c = claim("Conclusion.")\n'
        "s = noisy_and([a, b], c)\n"
        '__all__ = ["a", "b", "c", "s"]\n'
    )
    (pkg_src / "reviews").mkdir()
    (pkg_src / "reviews" / "self_review.py").write_text(
        "from gaia.review import ReviewBundle, review_claim, review_strategy\n"
        "from .. import a, b, c, s\n\n"
        "REVIEW = ReviewBundle(\n"
        '    source_id="self_review",\n'
        "    objects=[\n"
        '        review_claim(a, prior=0.8, judgment="ok", justification="."),\n'
        '        review_claim(b, prior=0.8, judgment="ok", justification="."),\n'
        '        review_claim(c, prior=0.4, judgment="ok", justification="."),\n'
        '        review_strategy(s, conditional_probability=0.85, judgment="ok", justification="."),\n'
        "    ],\n"
        ")\n"
    )

    assert runner.invoke(app, ["compile", str(pkg_dir)]).exit_code == 0
    assert runner.invoke(app, ["infer", str(pkg_dir)]).exit_code == 0

    result = runner.invoke(app, ["render", str(pkg_dir), "--target", "docs"])
    assert result.exit_code == 0, f"Failed: {result.output}"

    content = (pkg_dir / "docs" / "detailed-reasoning.md").read_text()
    assert "# readme-pkg-gaia" in content
    assert "A test package." in content
    assert "```mermaid" in content
    assert "## Knowledge Nodes" in content or "## " in content
    assert "#### a" in content
    assert "#### b" in content
    assert "#### c" in content
```

Note the filename change: the old test asserted against `README.md` (written by the deprecated `--readme` alias). The new test asserts against `docs/detailed-reasoning.md` (what `--module-graphs` wrote, and what `render --target docs` now writes).

- [ ] **Step 2: Run the migrated test and the whole test_detailed_reasoning.py file**

Run: `uv run pytest tests/cli/test_detailed_reasoning.py -xvs`
Expected: all pass, including the unit tests for `generate_detailed_reasoning()` which are unchanged in body (only renamed in Chunk 0).

- [ ] **Step 3: Commit Chunk 4**

```bash
git add gaia/cli/commands/compile.py tests/cli/test_github_integration.py tests/cli/test_detailed_reasoning.py
git commit -m "feat(cli): remove --github/--module-graphs/--readme flags from gaia compile

Migrate existing CLI integration tests to use gaia render --target github/docs."
```

---

## Chunk 5: Documentation and skill updates

### Task 12: Update `docs/foundations/cli/workflow.md`

**Files:**
- Modify: `docs/foundations/cli/workflow.md`

- [ ] **Step 1: Update the pipeline diagram**

In `docs/foundations/cli/workflow.md`, find the pipeline diagram (around line 14-16):

```
gaia init --> gaia add --> write package --> gaia compile --> write review --> gaia infer --> git tag --> gaia register
(scaffold)   (add deps)    (DSL code)      (DSL -> IR)     (self-review)   (BP preview)              (registry PR)
```

Replace with:

```
gaia init --> gaia add --> write package --> gaia compile --> write review --> gaia infer --> gaia render --> git tag --> gaia register
(scaffold)   (add deps)    (DSL code)      (DSL -> IR)     (self-review)   (BP preview)    (present)              (registry PR)
```

- [ ] **Step 2: Insert a `### gaia render` section**

Insert between the `### gaia infer [PATH] [--review NAME]` section (ends around line 169) and the `### gaia register [PATH] [OPTIONS]` section:

````markdown
### `gaia render [PATH] [--review NAME] [--target TARGET]`

Render presentation outputs (detailed-reasoning docs and/or a GitHub presentation
site) from a compiled and inferred package.

```
gaia render [PATH] [--review NAME] [--target docs|github|all]
```

| Argument / Option | Default | Description |
|-------------------|---------|-------------|
| `PATH`            | `.`     | Path to knowledge package directory |
| `--review NAME`   | `None`  | Review sidecar name (as with `gaia infer`). Auto-selected when only one review exists. |
| `--target TARGET` | `all`   | `docs` writes `docs/detailed-reasoning.md`; `github` writes `.github-output/`; `all` (default) writes both. |

**What it does:**

1. Loads and compiles the package (same gate as `gaia compile`).
2. Verifies `.gaia/ir_hash` and `.gaia/ir.json` are present and not stale.
3. Discovers the review sidecar via the same mechanism as `gaia infer`.
4. Requires `.gaia/reviews/<NAME>/beliefs.json` to exist and match the current
   `ir_hash` — errors otherwise (no silent fallback).
5. Loads `beliefs.json` and (if present) `parameterization.json`.
6. When `--target` includes `docs`, invokes the detailed-reasoning renderer and
   writes `docs/detailed-reasoning.md`.
7. When `--target` includes `github`, invokes the GitHub presentation renderer
   and writes `.github-output/` (React SPA scaffold, wiki pages, `graph.json`,
   `manifest.json`, README skeleton).

**Prerequisites:** `gaia compile` and `gaia infer` must have been run first.
Missing or stale artifacts are hard errors.

**Key output:**
- `docs/detailed-reasoning.md` (when target includes `docs`)
- `.github-output/` (when target includes `github`)
````

- [ ] **Step 3: Update the Artifacts by Stage table**

Find the table around line 225-229 (`## Artifacts by Stage`) and insert a new row between `Infer` and whatever comes next:

```markdown
| Render   | `gaia render`    | `docs/detailed-reasoning.md`, `.github-output/` |
```

---

### Task 13: Update `README.md`

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Fix the workflow diagram**

At `README.md:152`, replace:

```
gaia init → gaia add → write package → gaia compile → write review → gaia infer → gaia compile --github → /gaia:publish → gaia register
```

with:

```
gaia init → gaia add → write package → gaia compile → write review → gaia infer → gaia render → /gaia:publish → gaia register
```

- [ ] **Step 2: Update the command table**

At `README.md:161-162`, replace:

```
| `gaia compile --github [path]` | Generate GitHub presentation skeleton (`.github-output/`): wiki, README, React Pages, graph.json |
| `gaia compile --module-graphs [path]` | Generate per-module detailed reasoning graphs to `docs/detailed-reasoning.md` |
```

with:

```
| `gaia render --target github [path]` | Generate GitHub presentation skeleton (`.github-output/`): wiki, README, React Pages, graph.json |
| `gaia render --target docs [path]` | Generate per-module detailed reasoning to `docs/detailed-reasoning.md` |
| `gaia render [path]` | Default: render both docs and github targets (`--target all`) |
```

- [ ] **Step 3: Update the Quick Start command**

At `README.md:212`, replace:

```
gaia compile . --github       # generate GitHub presentation skeleton
```

with:

```
gaia render . --target github   # generate GitHub presentation skeleton
```

- [ ] **Step 4: Update the `/gaia:publish` description**

At `README.md:111`, replace:

```
2. **`/gaia:publish`** — After `gaia compile . --github` generates the skeleton, this skill fills in the narrative README, writes section summaries, and pushes to GitHub. Your repo gets a human-readable presentation of the formalized knowledge with interactive graphs.
```

with:

```
2. **`/gaia:publish`** — After `gaia render --target github` generates the skeleton, this skill fills in the narrative README, writes section summaries, and pushes to GitHub. Your repo gets a human-readable presentation of the formalized knowledge with interactive graphs.
```

At `README.md:124`, replace:

```
| `/gaia:publish` | Generate GitHub presentation (`--github` skeleton → narrative README → push) |
```

with:

```
| `/gaia:publish` | Generate GitHub presentation (`render --target github` skeleton → narrative README → push) |
```

---

### Task 14: Update skills

**Files:**
- Modify: `skills/gaia-cli/SKILL.md`
- Modify: `skills/gaia/SKILL.md`
- Modify: `skills/publish/SKILL.md`
- Modify: `skills/formalization/SKILL.md`

- [ ] **Step 1: `skills/gaia-cli/SKILL.md`**

Grep for the offending lines first:

Run: `grep -n -- '--github\|--module-graphs\|--readme' skills/gaia-cli/SKILL.md`

For each hit, replace `gaia compile . --github` with `gaia render . --target github`, and `gaia compile . --module-graphs` with `gaia render . --target docs`. At line 96 (the deprecated `--readme` note), delete the whole sentence about `--readme` — the flag is gone and there is no longer an alias to document. Replace with: `"Note: run \`gaia infer\` before \`gaia render\` — render requires beliefs on disk."`.

Specifically:
- Line 91: `gaia compile . --module-graphs` → `gaia render . --target docs`
- Line 96: delete the "Note: `--readme` is a deprecated alias..." line entirely; replace with `"Note: run \`gaia infer\` before \`gaia render\` — render requires beliefs on disk."`
- Line 101: `gaia compile . --github` → `gaia render . --target github`
- Line 213: `gaia compile . --github` → `gaia render . --target github`
- Line 215: `gaia compile . --module-graphs` → `gaia render . --target docs`
- Line 225: `gaia compile . --github` → `gaia render . --target github`
- Line 226: `gaia compile . --module-graphs` → `gaia render . --target docs`

- [ ] **Step 2: `skills/gaia/SKILL.md`**

Run: `grep -n -- '--github\|--module-graphs\|--readme' skills/gaia/SKILL.md`

- Line 32: `gaia compile . --github` → `gaia render . --target github`
- Line 42: `gaia compile . --github` → `gaia render . --target github`
- Line 43: `gaia compile . --module-graphs` → `gaia render . --target docs`

- [ ] **Step 3: `skills/publish/SKILL.md`**

Run: `grep -n -- '--github\|--module-graphs\|--readme' skills/publish/SKILL.md`

- Line 13: `gaia compile . --github` → `gaia render . --target github`
- Line 22: `gaia compile . --github` → `gaia render . --target github`
- Line 174: `gaia compile . --module-graphs` → `gaia render . --target docs`

- [ ] **Step 4: `skills/formalization/SKILL.md`**

Run: `grep -n -- '--github\|--module-graphs\|--readme' skills/formalization/SKILL.md`

- Line 39 (inside a graphviz/DOT block): `gaia compile . --github\n+ /gaia:publish` → `gaia render . --target github\n+ /gaia:publish`
- Line 710: `gaia compile . --github` → `gaia render . --target github`
- Line 711: `gaia compile . --module-graphs` → `gaia render . --target docs`

- [ ] **Step 5: Final grep sanity check**

Run: `grep -rn -- '--github\|--module-graphs\|--readme' skills/ README.md docs/foundations/cli/ gaia/cli/`

Expected: zero hits (or only the harmless `namespace = "github"` hits in test fixtures — which are not in `skills/` / `README.md` / `docs/foundations/cli/` / `gaia/cli/` so should not show up).

- [ ] **Step 6: Commit Chunk 5**

```bash
git add docs/foundations/cli/workflow.md README.md skills/gaia-cli/SKILL.md skills/gaia/SKILL.md skills/publish/SKILL.md skills/formalization/SKILL.md
git commit -m "docs: document gaia render command and retire compile presentation flags"
```

---

## Chunk 6: Verification & PR

### Task 15: Run full verification per `verification-before-completion` skill

- [ ] **Step 1: Ruff lint**

Run: `ruff check .`
Expected: no errors. Fix any that surface — most likely unused imports in `render.py` or `compile.py`.

- [ ] **Step 2: Ruff format check**

Run: `ruff format --check .`
Expected: all files formatted. If any diff, run `ruff format .` and re-check.

- [ ] **Step 3: Full CLI test suite**

Run: `uv run pytest tests/cli -xvs`
Expected: all pass. Pay attention to:
- `test_render.py` (new, all tests)
- `test_compile.py` (unchanged, must still pass)
- `test_infer.py` (the error-message change in Task 6 could theoretically affect an assertion; verify)
- `test_github_integration.py` (migrated CLI tests + unchanged unit tests)
- `test_detailed_reasoning.py` (renamed from `test_readme.py` in Chunk 0; migrated CLI test + unchanged unit tests)
- `test_github_react.py` (unchanged)

- [ ] **Step 4: Broader test suite (as a safety net)**

Run: `uv run pytest tests -x --ignore=tests/integration`
Expected: all pass. If any non-CLI test happens to reference compile's removed flags, fix.

- [ ] **Step 5: Smoke test the new command manually**

Run the happy path against an existing fixture package if one exists:

```bash
uv run gaia render --help
```

Expected: help text showing `--review` and `--target` options.

---

### Task 16: Push branch, create PR, verify CI

- [ ] **Step 1: Check git status**

Run: `git status`
Expected: clean working tree (all Chunk commits already made).

- [ ] **Step 2: Verify branch and commit log**

Run: `git log --oneline main..HEAD`
Expected: 6 commits (one per chunk that produced code changes: Chunk 0 rename prep, Chunk 1 scaffold + happy path, Chunk 2 errors, Chunk 3 target/review, Chunk 4 compile cleanup, Chunk 5 docs). Chunk 6 is verification only.

- [ ] **Step 3: Push the branch**

```bash
git push -u origin HEAD
```

- [ ] **Step 4: Create the PR**

```bash
gh pr create --title "feat(cli): gaia render command (replaces compile --github/--module-graphs)" --body "$(cat <<'EOF'
## Summary
- Extract `compile --github` and `compile --module-graphs`/`--readme` presentation outputs into a dedicated `gaia render` command.
- `gaia render` re-compiles, verifies `.gaia/ir.json` freshness, requires `.gaia/reviews/<name>/beliefs.json` (strict — no silent None), and dispatches to the existing `generate_detailed_reasoning` / `generate_github_output` helpers via `--target docs|github|all`.
- `compile` goes back to being a pure `DSL → IR` function. Its presentation flags are hard-deleted (no deprecation window).
- `gaia register` is untouched.
- Rename legacy `_readme.py` / `generate_readme` / `test_readme.py` → `_detailed_reasoning.py` / `generate_detailed_reasoning` / `test_detailed_reasoning.py` to match the actual output filename.

## Why
- `compile --github` reached forward into `.gaia/reviews/` for beliefs → dependency inversion across pipeline stages.
- Missing beliefs → silent partial output (`beliefs_data=None`) — latent bug.
- Presentation now lives after `infer` in the pipeline, matching its real data dependency.
- `_readme.py` was named after the deprecated `--readme` flag but actually writes `docs/detailed-reasoning.md` — rename closes the name/behavior gap.

## Test plan
- [ ] `uv run pytest tests/cli/test_render.py -xvs` — new tests for happy path, missing/stale artifacts, missing/stale beliefs, multi-review selection, --target filtering
- [ ] `uv run pytest tests/cli` — full CLI suite, including migrated `test_github_integration.py` and `test_detailed_reasoning.py`
- [ ] `ruff check . && ruff format --check .`
- [ ] `uv run gaia render --help` sanity
- [ ] Verify `docs/foundations/cli/workflow.md`, `README.md`, and all `skills/*/SKILL.md` no longer reference the removed flags

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 5: Check CI**

Run: `gh run list --branch $(git rev-parse --abbrev-ref HEAD) --limit 1`

If the run is still in progress, wait for it to finish (do not poll — rely on the user or a follow-up command). If it fails:

```bash
gh run view <run-id> --log-failed
```

Read the log, fix the issue, push a follow-up commit. Do NOT close or force-push over the PR unless explicitly told to.

- [ ] **Step 6: Report PR URL to the user**

Print the PR URL returned by `gh pr create` and stop.

---

## Notes for the executing agent

- **No drive-by cleanups.** `_github.py` and `_detailed_reasoning.py` (post-rename) are large and tempting to refactor. Leave them alone — this plan is a rewire, not a rewrite. The Chunk 0 rename changes filenames and one function name only; do not touch anything else in those files.
- **Do not touch `docs/foundations/gaia-ir/` or `docs/foundations/theory/`.** Protected layers per CLAUDE.md.
- **Review sidecar fixtures** in the new tests mirror `tests/cli/test_infer.py`'s conventions. If you find yourself inventing a new helper pattern, pause and check `test_infer.py` first.
- **Error messages matter.** The plan specifies the substrings tests grep for (e.g. `"missing beliefs"`, `"stale"`, `"multiple review sidecars"`). If you rephrase an error message, update the assertion in the same commit.
- **Import hygiene.** If `ruff` flags an unused import (e.g. `LocalCanonicalGraph` in `render.py` if the code path uses `compiled.graph` directly), just remove the import. Don't introduce `# noqa`.
- **Frequent commits.** One commit per chunk is the minimum; splitting inside a chunk is fine. Do not batch Chunks 4 and 5 into a single commit — they modify different concerns.
