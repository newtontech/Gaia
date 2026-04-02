"""gaia compile -- compile Python DSL package to Gaia IR v2 JSON."""

from __future__ import annotations

import typer

from gaia.cli._packages import GaiaCliError, compile_loaded_package, load_gaia_package
from gaia.cli._packages import write_compiled_artifacts


def compile_command(
    path: str = typer.Argument(".", help="Path to knowledge package directory"),
) -> None:
    """Compile a knowledge package to .gaia/ir.json."""
    try:
        loaded = load_gaia_package(path)
        ir = compile_loaded_package(loaded)
        gaia_dir = write_compiled_artifacts(loaded.pkg_path, ir)
    except GaiaCliError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1)

    typer.echo(
        f"Compiled {len(ir['knowledges'])} knowledge, "
        f"{len(ir['strategies'])} strategies, "
        f"{len(ir['operators'])} operators"
    )
    typer.echo(f"IR hash: {ir['ir_hash'][:16]}...")
    typer.echo(f"Output: {gaia_dir / 'ir.json'}")
