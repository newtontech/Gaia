"""gaia render -- generate presentation outputs (docs and/or GitHub site) from a reviewed package."""

from __future__ import annotations

import json
from enum import Enum

import typer

from gaia.cli._packages import (
    GaiaCliError,
    compile_loaded_package_artifact,
    load_gaia_package,
)
from gaia.cli._reviews import load_gaia_review
from gaia.cli.commands._detailed_reasoning import generate_detailed_reasoning
from gaia.cli.commands._github import generate_github_output
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
        typer.echo("Error: missing compiled artifacts; run `gaia compile` first.", err=True)
        raise typer.Exit(1)
    if ir_hash_path.read_text().strip() != compiled.graph.ir_hash:
        typer.echo("Error: compiled artifacts are stale; run `gaia compile` again.", err=True)
        raise typer.Exit(1)
    try:
        stored_ir = json.loads(ir_json_path.read_text())
    except json.JSONDecodeError as exc:
        typer.echo(f"Error: .gaia/ir.json is not valid JSON: {exc}", err=True)
        raise typer.Exit(1)
    if stored_ir.get("ir_hash") != compiled.graph.ir_hash or stored_ir != ir:
        typer.echo("Error: compiled artifacts are stale; run `gaia compile` again.", err=True)
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
        exported_ids = {k["id"] for k in ir.get("knowledges", []) if k.get("exported")}
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
