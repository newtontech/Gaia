# gaia init, gaia add, Registry CI Update — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `gaia init` (scaffold package) and `gaia add` (install from registry) CLI commands, and update the official registry CI to use PyPI-installed gaia-lang with namespace validation.

**Architecture:** Two new Typer commands following existing patterns in `gaia/cli/commands/`. `gaia init` shells out to `uv init --lib` then patches files. `gaia add` fetches registry TOML via GitHub API (httpx), parses with tomllib, then shells out to `uv add`. Registry CI update is a YAML edit in a separate repo.

**Tech Stack:** Python 3.12, Typer, httpx (for GitHub API), tomllib, subprocess (for uv), pytest + CliRunner

**Spec:** `docs/specs/2026-04-03-gaia-init-add-registry-ci-design.md`

---

## File Map

| File | Responsibility |
|------|----------------|
| `gaia/cli/commands/init.py` | **New.** `gaia init <name>` — scaffold a Gaia package |
| `gaia/cli/commands/add.py` | **New.** `gaia add <package>` — install from registry |
| `gaia/cli/_registry.py` | **New.** Shared registry API client (fetch Package.toml, Versions.toml) |
| `gaia/cli/main.py` | **Modify.** Register `init` and `add` commands |
| `tests/cli/test_init.py` | **New.** Tests for init command |
| `tests/cli/test_add.py` | **New.** Tests for add command |

Registry CI is in a separate repo (`SiliconEinstein/gaia-registry`) — Task 5 provides the exact YAML.

---

## Chunk 1: gaia init + gaia add

### Task 1: `gaia init` command

**Files:**
- Create: `gaia/cli/commands/init.py`
- Modify: `gaia/cli/main.py`
- Test: `tests/cli/test_init.py`

- [ ] **Step 1: Write failing tests**

Create `tests/cli/test_init.py`:

```python
"""Tests for gaia init command."""

import subprocess
from unittest.mock import patch

from typer.testing import CliRunner

from gaia.cli.main import app

runner = CliRunner()


def test_init_rejects_name_without_gaia_suffix():
    """Name must end with -gaia."""
    result = runner.invoke(app, ["init", "my-package"])
    assert result.exit_code != 0
    assert "-gaia" in result.output


def test_init_creates_package(tmp_path, monkeypatch):
    """gaia init creates pyproject.toml with [tool.gaia] and correct src layout."""
    pkg_name = "test-pkg-gaia"
    pkg_dir = tmp_path / pkg_name
    monkeypatch.chdir(tmp_path)

    # Mock uv init to just create the directory with minimal structure
    def mock_uv_init(args, **kwargs):
        pkg_dir.mkdir(exist_ok=True)
        (pkg_dir / "pyproject.toml").write_text(
            f'[project]\nname = "{pkg_name}"\nversion = "0.1.0"\n'
            f'requires-python = ">=3.12"\n\n'
            f'[build-system]\nrequires = ["hatchling"]\n'
            f'build-backend = "hatchling.build"\n'
        )
        src = pkg_dir / "src" / "test_pkg_gaia"
        src.mkdir(parents=True)
        (src / "__init__.py").write_text("")
        return subprocess.CompletedProcess(args, 0)

    # Mock uv add to be a no-op
    def mock_run(args, **kwargs):
        if args[0] == "uv" and args[1] == "init":
            return mock_uv_init(args, **kwargs)
        return subprocess.CompletedProcess(args, 0)

    with patch("gaia.cli.commands.init._run_uv", side_effect=mock_run):
        result = runner.invoke(app, ["init", pkg_name])

    assert result.exit_code == 0, f"Failed: {result.output}"

    # pyproject.toml has [tool.gaia]
    import tomllib
    toml = tomllib.loads((pkg_dir / "pyproject.toml").read_text())
    assert toml["tool"]["gaia"]["type"] == "knowledge-package"
    assert "uuid" in toml["tool"]["gaia"]

    # src dir renamed: test_pkg (not test_pkg_gaia)
    assert (pkg_dir / "src" / "test_pkg").exists()
    assert not (pkg_dir / "src" / "test_pkg_gaia").exists()

    # __init__.py has DSL example
    init_py = (pkg_dir / "src" / "test_pkg" / "__init__.py").read_text()
    assert "from gaia.lang import" in init_py
    assert "__all__" in init_py

    # .gitignore has .gaia/
    gitignore = (pkg_dir / ".gitignore").read_text()
    assert ".gaia/" in gitignore
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/cli/test_init.py -v`
Expected: FAIL (init command not registered)

- [ ] **Step 3: Implement `gaia/cli/commands/init.py`**

```python
"""gaia init -- scaffold a new Gaia knowledge package."""

from __future__ import annotations

import subprocess
import uuid
from pathlib import Path

import typer

from gaia.cli._packages import GaiaCliError

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef]

_INIT_TEMPLATE = '''\
from gaia.lang import claim, setting

context = setting("Background context for this package.")
hypothesis = claim("A scientific hypothesis.")
evidence = claim("Supporting evidence.", given=[hypothesis])

__all__ = ["context", "hypothesis", "evidence"]
'''


def _run_uv(args: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
    """Run a uv command. Separated for testability."""
    return subprocess.run(args, text=True, capture_output=True, **kwargs)


def _patch_pyproject(pyproject_path: Path) -> None:
    """Add [tool.gaia] section to pyproject.toml."""
    text = pyproject_path.read_text()
    gaia_section = (
        "\n[tool.gaia]\n"
        'type = "knowledge-package"\n'
        f'uuid = "{uuid.uuid4()}"\n'
    )
    text += gaia_section
    pyproject_path.write_text(text)


def init_command(
    name: str = typer.Argument(help="Package name (must end with -gaia)"),
) -> None:
    """Scaffold a new Gaia knowledge package."""
    if not name.endswith("-gaia"):
        typer.echo("Error: package name must end with '-gaia'.", err=True)
        typer.echo(f"  Suggestion: {name}-gaia", err=True)
        raise typer.Exit(1)

    # Derive import name: strip -gaia suffix, replace hyphens with underscores
    import_name = name.removesuffix("-gaia").replace("-", "_")
    uv_import_name = name.replace("-", "_")  # what uv generates

    # 1. Run uv init --lib
    result = _run_uv(["uv", "init", "--lib", name])
    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        typer.echo(f"Error: uv init failed: {stderr}", err=True)
        raise typer.Exit(1)

    pkg_dir = Path(name)

    # 2. Patch pyproject.toml
    _patch_pyproject(pkg_dir / "pyproject.toml")

    # 3. Rename src directory (strip -gaia suffix from import name)
    src_old = pkg_dir / "src" / uv_import_name
    src_new = pkg_dir / "src" / import_name
    if src_old.exists() and src_old != src_new:
        src_old.rename(src_new)

    # 4. Write DSL template
    (src_new / "__init__.py").write_text(_INIT_TEMPLATE)

    # 5. Append .gaia/ to .gitignore
    gitignore = pkg_dir / ".gitignore"
    if gitignore.exists():
        text = gitignore.read_text()
        if ".gaia/" not in text:
            gitignore.write_text(text.rstrip() + "\n\n# Gaia build artifacts\n.gaia/\n")
    else:
        gitignore.write_text("# Gaia build artifacts\n.gaia/\n")

    # 6. Add gaia-lang dependency
    result = _run_uv(["uv", "add", "gaia-lang"], cwd=pkg_dir)
    if result.returncode != 0:
        typer.echo(f"Warning: 'uv add gaia-lang' failed: {result.stderr.strip()}", err=True)
        typer.echo("  Run it manually: cd {name} && uv add gaia-lang", err=True)

    typer.echo(f"Created {name}/")
    typer.echo(f"  src/{import_name}/__init__.py — edit your knowledge declarations here")
    typer.echo(f"  pyproject.toml — package metadata with [tool.gaia]")
    typer.echo(f"\nNext: cd {name} && gaia compile .")
```

- [ ] **Step 4: Register command in `gaia/cli/main.py`**

Add import and registration:

```python
from gaia.cli.commands.init import init_command
app.command(name="init")(init_command)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/cli/test_init.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add gaia/cli/commands/init.py gaia/cli/main.py tests/cli/test_init.py
git commit -m "feat(cli): add gaia init command"
```

---

### Task 2: Registry API client

**Files:**
- Create: `gaia/cli/_registry.py`

- [ ] **Step 1: Implement `_registry.py`**

```python
"""Shared registry metadata client — fetches package info from GitHub API."""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass

import httpx

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef]

from gaia.cli._packages import GaiaCliError

DEFAULT_REGISTRY = "SiliconEinstein/gaia-registry"


@dataclass
class RegistryVersion:
    """Resolved version metadata from the registry."""

    version: str
    repo: str
    git_tag: str
    git_sha: str
    ir_hash: str


def _github_headers() -> dict[str, str]:
    """Build headers, using GITHUB_TOKEN if available for rate limits."""
    headers = {"Accept": "application/vnd.github.v3+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _fetch_file(registry: str, path: str) -> str:
    """Fetch a file from the registry repo via GitHub API."""
    url = f"https://api.github.com/repos/{registry}/contents/{path}"
    resp = httpx.get(url, headers=_github_headers(), timeout=15)
    if resp.status_code == 404:
        raise GaiaCliError(f"Not found in registry: {path}")
    resp.raise_for_status()
    content = resp.json().get("content", "")
    return base64.b64decode(content).decode()


def resolve_package(
    package: str,
    *,
    version: str | None = None,
    registry: str = DEFAULT_REGISTRY,
) -> RegistryVersion:
    """Resolve a package name + optional version to repo URL and git SHA."""
    # Normalize: strip -gaia suffix for registry lookup
    name = package.removesuffix("-gaia") if package.endswith("-gaia") else package

    pkg_toml = tomllib.loads(_fetch_file(registry, f"packages/{name}/Package.toml"))
    ver_toml = tomllib.loads(_fetch_file(registry, f"packages/{name}/Versions.toml"))

    versions = ver_toml.get("versions", {})
    if not versions:
        raise GaiaCliError(f"No versions found for package '{name}'.")

    if version is None:
        # Latest: last key in ordered dict
        version = list(versions)[-1]

    if version not in versions:
        available = ", ".join(versions)
        raise GaiaCliError(
            f"Version '{version}' not found for '{name}'. Available: {available}"
        )

    entry = versions[version]
    return RegistryVersion(
        version=version,
        repo=pkg_toml["repo"],
        git_tag=entry["git_tag"],
        git_sha=entry["git_sha"],
        ir_hash=entry["ir_hash"],
    )
```

- [ ] **Step 2: Commit**

```bash
git add gaia/cli/_registry.py
git commit -m "feat(cli): add registry API client"
```

---

### Task 3: `gaia add` command

**Files:**
- Create: `gaia/cli/commands/add.py`
- Modify: `gaia/cli/main.py`
- Test: `tests/cli/test_add.py`

- [ ] **Step 1: Write failing tests**

Create `tests/cli/test_add.py`:

```python
"""Tests for gaia add command."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from gaia.cli._registry import RegistryVersion
from gaia.cli.main import app

runner = CliRunner()

MOCK_VERSION = RegistryVersion(
    version="4.0.5",
    repo="https://github.com/kunyuan/GalileoFallingBodies.gaia",
    git_tag="v4.0.5",
    git_sha="dac84fc722bf81398a7e77c830a60b2b068de18a",
    ir_hash="sha256:abc123",
)


@patch("gaia.cli.commands.add.resolve_package", return_value=MOCK_VERSION)
@patch("gaia.cli.commands.add._run_uv")
def test_add_installs_with_git_url(mock_uv, mock_resolve):
    """gaia add resolves registry metadata and calls uv add with git URL."""
    mock_uv.return_value = MagicMock(returncode=0)

    result = runner.invoke(app, ["add", "galileo-falling-bodies-gaia"])
    assert result.exit_code == 0, f"Failed: {result.output}"

    mock_resolve.assert_called_once_with(
        "galileo-falling-bodies-gaia", version=None, registry="SiliconEinstein/gaia-registry"
    )

    # Check uv add was called with correct git URL
    uv_args = mock_uv.call_args[0][0]
    assert uv_args[0] == "uv"
    assert uv_args[1] == "add"
    assert "git+https://github.com/kunyuan/GalileoFallingBodies.gaia@dac84fc7" in uv_args[2]


@patch("gaia.cli.commands.add.resolve_package", return_value=MOCK_VERSION)
@patch("gaia.cli.commands.add._run_uv")
def test_add_with_version(mock_uv, mock_resolve):
    """gaia add --version passes version to resolver."""
    mock_uv.return_value = MagicMock(returncode=0)

    result = runner.invoke(app, ["add", "galileo-falling-bodies-gaia", "--version", "4.0.5"])
    assert result.exit_code == 0

    mock_resolve.assert_called_once_with(
        "galileo-falling-bodies-gaia", version="4.0.5", registry="SiliconEinstein/gaia-registry"
    )


@patch("gaia.cli.commands.add.resolve_package")
def test_add_not_found(mock_resolve):
    """gaia add shows error for unknown package."""
    from gaia.cli._packages import GaiaCliError
    mock_resolve.side_effect = GaiaCliError("Not found in registry: packages/no-such/Package.toml")

    result = runner.invoke(app, ["add", "no-such-gaia"])
    assert result.exit_code != 0
    assert "Not found" in result.output
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/cli/test_add.py -v`
Expected: FAIL (add command not registered)

- [ ] **Step 3: Implement `gaia/cli/commands/add.py`**

```python
"""gaia add -- install a Gaia knowledge package from the official registry."""

from __future__ import annotations

import subprocess

import typer

from gaia.cli._packages import GaiaCliError
from gaia.cli._registry import DEFAULT_REGISTRY, resolve_package


def _run_uv(args: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
    """Run a uv command. Separated for testability."""
    return subprocess.run(args, text=True, capture_output=True, **kwargs)


def add_command(
    package: str = typer.Argument(help="Package name (e.g., galileo-falling-bodies-gaia)"),
    version: str | None = typer.Option(None, "--version", "-v", help="Specific version"),
    registry: str = typer.Option(DEFAULT_REGISTRY, "--registry", help="Registry GitHub repo"),
) -> None:
    """Install a registered Gaia knowledge package."""
    try:
        resolved = resolve_package(package, version=version, registry=registry)
    except GaiaCliError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1)

    dep_spec = f"{package} @ git+{resolved.repo}@{resolved.git_sha}"
    typer.echo(f"Resolved {package} v{resolved.version} → {resolved.git_sha[:8]}")

    result = _run_uv(["uv", "add", dep_spec])
    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        typer.echo(f"Error: uv add failed: {stderr}", err=True)
        raise typer.Exit(1)

    typer.echo(f"Added {package} v{resolved.version}")
```

- [ ] **Step 4: Register command in `gaia/cli/main.py`**

Add import and registration:

```python
from gaia.cli.commands.add import add_command
app.command(name="add")(add_command)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/cli/test_add.py -v`
Expected: PASS

- [ ] **Step 6: Run all CLI tests**

Run: `pytest tests/cli/ -v`
Expected: ALL PASS

- [ ] **Step 7: Lint and format**

```bash
ruff check gaia/cli/ tests/cli/
ruff format gaia/cli/ tests/cli/
```

- [ ] **Step 8: Commit**

```bash
git add gaia/cli/commands/add.py gaia/cli/main.py tests/cli/test_add.py
git commit -m "feat(cli): add gaia add command — install from registry"
```

---

### Task 4: Add httpx dependency

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add httpx to dependencies**

`gaia add` uses httpx for GitHub API calls. Add it to the `[project].dependencies` list in `pyproject.toml`:

```toml
dependencies = [
    "pydantic>=2.0",
    "typer[all]>=0.12",
    "numpy>=1.26",
    "httpx>=0.27",
]
```

- [ ] **Step 2: Run `uv sync`**

```bash
uv sync
```

- [ ] **Step 3: Run full test suite**

```bash
pytest tests/ir tests/cli tests/test_lowering.py tests/test_science_examples.py -v
```

Expected: ALL PASS

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "build: add httpx dependency for registry API"
```

---

## Chunk 2: Registry CI Update

### Task 5: Update `register.yml` in gaia-registry repo

This task operates on the **gaia-registry** repo, not the Gaia main repo.

**Files:**
- Modify: `gaia-registry/.github/workflows/register.yml`

- [ ] **Step 1: Clone gaia-registry locally**

```bash
git clone https://github.com/SiliconEinstein/gaia-registry.git /tmp/gaia-registry
cd /tmp/gaia-registry
git checkout -b feat/pypi-gaia-lang-and-namespace
```

- [ ] **Step 2: Update `register.yml`**

Replace the `GAIA_REPO` / `GAIA_REF` env block and the "Clone Gaia CLI source" step with a simpler PyPI install. Add namespace validation step.

The updated sandbox-validate job steps should be:

1. checkout
2. Install uv + Python (unchanged)
3. Parse registration payload (unchanged)
4. **Install Gaia CLI from PyPI** (replaces clone):
   ```yaml
   - name: Install Gaia CLI
     run: uv pip install --system gaia-lang
   ```
5. Clone and validate source release — simplified:
   - Remove the `GAIA_APP` and `/tmp/gaia/.venv/bin/python -c` pattern
   - Call `gaia compile .` and `gaia check .` directly
6. **New step: Validate namespace**:
   ```yaml
   - name: Validate namespace
     run: |
       python3 -c "
       import json, sys
       graph = json.load(open('.gaia/ir.json'))
       ns = graph.get('namespace', '')
       if ns != 'github':
           print(f'Error: namespace must be \"github\", got \"{ns}\"', file=sys.stderr)
           sys.exit(1)
       print(f'Namespace OK: {ns}')
       "
     working-directory: pkg
   ```

Also remove the top-level `env:` block that defines `GAIA_REPO` and `GAIA_REF`.

- [ ] **Step 3: Commit and push**

```bash
cd /tmp/gaia-registry
git add .github/workflows/register.yml
git commit -m "feat(ci): use PyPI gaia-lang + namespace validation

- Replace GAIA_REPO/GAIA_REF clone with 'uv pip install gaia-lang'
- Add namespace == 'github' validation in sandbox job
- Simplify gaia compile/check invocation (direct CLI, no python -c wrapper)"
git push origin feat/pypi-gaia-lang-and-namespace
```

- [ ] **Step 4: Create PR**

```bash
gh pr create \
  --repo SiliconEinstein/gaia-registry \
  --title "feat(ci): use PyPI gaia-lang + namespace validation" \
  --body "$(cat <<'EOF'
## Summary
- Replace clone + GAIA_REF with `uv pip install gaia-lang` from PyPI
- Add namespace validation (must be `github` for this registry)
- Simplify CLI invocation in sandbox job

## Test plan
- [ ] Trigger a test registration PR to verify the updated CI works
EOF
)"
```

---

### Task 6: Update docs and bump version

**Files:**
- Modify: `docs/foundations/cli/workflow.md` (add `gaia init` and `gaia add` descriptions)
- Modify: `README.md` (update install and workflow sections)

- [ ] **Step 1: Update `workflow.md`**

Add `gaia init` and `gaia add` sections to the Commands list, following the existing pattern for compile/check/infer/register.

- [ ] **Step 2: Update `README.md`**

Update the "Create a Knowledge Package" section to use `gaia init` instead of manual `uv init`.
Add a "Install a Package" section showing `gaia add`.

- [ ] **Step 3: Run lint**

```bash
ruff check . && ruff format --check .
```

- [ ] **Step 4: Commit**

```bash
git add docs/foundations/cli/workflow.md README.md
git commit -m "docs: add gaia init and gaia add to workflow docs and README"
```
