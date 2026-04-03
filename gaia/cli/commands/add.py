"""gaia add -- install a Gaia knowledge package from the official registry."""

from __future__ import annotations

import subprocess

import typer

from gaia.cli._packages import GaiaCliError
from gaia.cli._registry import DEFAULT_REGISTRY, resolve_package


def _run_uv(args: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
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
