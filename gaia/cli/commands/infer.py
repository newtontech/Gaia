"""gaia infer -- run BP from compiled IR plus review sidecar parameterization."""

from __future__ import annotations

import json
from dataclasses import asdict

import typer

from gaia.bp import lower_local_graph
from gaia.bp.engine import InferenceEngine
from gaia.cli._packages import (
    GaiaCliError,
    apply_package_priors,
    compile_loaded_package_artifact,
    gaia_lang_version,
    load_gaia_package,
)
from gaia.cli._reviews import load_gaia_review, resolve_gaia_review
from gaia.ir.validator import validate_local_graph, validate_parameterization


def _write_json(path, payload) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def infer_command(
    path: str = typer.Argument(".", help="Path to knowledge package directory"),
    review: str | None = typer.Option(
        None,
        "--review",
        help="Review sidecar name from <package>/reviews/<name>.py or 'review' for legacy review.py.",
    ),
) -> None:
    """Run BP using the current IR structure plus the package review sidecar."""
    try:
        loaded = load_gaia_package(path)
        apply_package_priors(loaded)
        compiled = compile_loaded_package_artifact(loaded)
    except GaiaCliError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1)

    graph_validation = validate_local_graph(compiled.graph)
    for warning in graph_validation.warnings:
        typer.echo(f"Warning: {warning}")
    if graph_validation.errors:
        for error in graph_validation.errors:
            typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(1)

    ir_hash_path = loaded.pkg_path / ".gaia" / "ir_hash"
    ir_json_path = loaded.pkg_path / ".gaia" / "ir.json"
    compiled_json = compiled.to_json()
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
    if stored_ir.get("ir_hash") != compiled.graph.ir_hash or stored_ir != compiled_json:
        typer.echo("Error: compiled artifacts are stale; run `gaia compile` again.", err=True)
        raise typer.Exit(1)

    try:
        loaded_review = load_gaia_review(loaded, review_name=review)
        if loaded_review is not None:
            resolved_review = resolve_gaia_review(loaded_review, compiled)
        else:
            resolved_review = None
    except GaiaCliError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1)

    if resolved_review is not None:
        priors_list = resolved_review.priors
        strategy_params_list = resolved_review.strategy_params
    else:
        # No review sidecar — lowering reads metadata["prior"] directly
        # (set by priors.py and reason+prior DSL pairing during compilation).
        priors_list = []
        strategy_params_list = []

    # Parameterization validation only applies when using review sidecars
    # (explicit PriorRecord coverage check). When using metadata priors from
    # priors.py, the lowering layer reads metadata["prior"] directly.
    if resolved_review is not None:
        parameterization_validation = validate_parameterization(
            compiled.graph,
            priors_list,
            strategy_params_list,
        )
        for warning in parameterization_validation.warnings:
            typer.echo(f"Warning: {warning}")
        if parameterization_validation.errors:
            for error in parameterization_validation.errors:
                typer.echo(f"Error: {error}", err=True)
            raise typer.Exit(1)

    node_priors = {record.knowledge_id: record.value for record in priors_list}
    strategy_params = {
        record.strategy_id: record.conditional_probabilities
        for record in strategy_params_list
    }
    factor_graph = lower_local_graph(
        compiled.graph,
        node_priors=node_priors,
        strategy_conditional_params=strategy_params,
    )
    fg_errors = factor_graph.validate()
    if fg_errors:
        for error in fg_errors:
            typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(1)

    engine = InferenceEngine()
    inference_result = engine.run(factor_graph)
    result = inference_result.bp_result

    gaia_dir = loaded.pkg_path / ".gaia"
    gaia_dir.mkdir(exist_ok=True)

    gaia_ver = gaia_lang_version()

    if resolved_review is not None:
        review_dir = gaia_dir / "reviews" / loaded_review.name
        review_dir.mkdir(parents=True, exist_ok=True)
        review_content_hash = resolved_review.content_hash()

        _write_json(
            review_dir / "parameterization.json",
            resolved_review.to_json(ir_hash=compiled.graph.ir_hash, gaia_lang_version=gaia_ver),
        )
        output_path = review_dir / "beliefs.json"
    else:
        review_content_hash = ""
        output_path = gaia_dir / "beliefs.json"

    knowledge_by_id = {knowledge.id: knowledge for knowledge in compiled.graph.knowledges}
    beliefs_payload = {
        "ir_hash": compiled.graph.ir_hash,
        "gaia_lang_version": gaia_ver,
        "review_content_hash": review_content_hash,
        "beliefs": [
            {
                "knowledge_id": knowledge_id,
                "label": knowledge_by_id[knowledge_id].label,
                "belief": belief,
            }
            for knowledge_id, belief in sorted(result.beliefs.items())
            if knowledge_id in knowledge_by_id
        ],
        "diagnostics": asdict(result.diagnostics),
    }
    _write_json(output_path, beliefs_payload)

    typer.echo(
        f"Inferred {len(result.beliefs)} beliefs from "
        f"{len(priors_list)} priors and "
        f"{len(strategy_params_list)} strategy parameter records"
    )
    method_label = inference_result.method_used.upper()
    exact_label = " (exact)" if inference_result.is_exact else ""
    typer.echo(f"Method: {method_label}{exact_label}, {inference_result.elapsed_ms:.0f}ms")
    if result.diagnostics.iterations_run:
        typer.echo(
            f"Converged: {result.diagnostics.converged} "
            f"after {result.diagnostics.iterations_run} iterations"
        )
    if loaded_review is not None:
        typer.echo(f"Review: {loaded_review.name}")
    typer.echo(f"Output: {output_path}")
