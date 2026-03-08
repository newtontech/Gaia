"""Gaia CLI — proof assistant for probabilistic defeasible reasoning."""

from __future__ import annotations

from pathlib import Path

import typer
import yaml

app = typer.Typer(
    name="gaia",
    help="Gaia — proof assistant for probabilistic defeasible reasoning.",
    no_args_is_help=True,
)


@app.command()
def build(
    path: str = typer.Argument(".", help="Path to knowledge package directory"),
) -> None:
    """Elaborate: parse + resolve + instantiate params."""
    from libs.dsl.build_store import save_build
    from libs.dsl.elaborator import elaborate_package
    from libs.dsl.loader import load_package
    from libs.dsl.resolver import resolve_refs

    pkg_path = Path(path)
    try:
        pkg = load_package(pkg_path)
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    pkg = resolve_refs(pkg)
    elaborated = elaborate_package(pkg)

    build_dir = pkg_path / ".gaia" / "build"
    save_build(elaborated, build_dir)

    n_mods = len(pkg.loaded_modules)
    n_prompts = len(elaborated.prompts)
    typer.echo(f"Built {pkg.name}: {n_mods} modules, {n_prompts} elaborated prompts")
    typer.echo(f"Artifacts: {build_dir}/")


@app.command()
def review(
    path: str = typer.Argument(".", help="Path to knowledge package directory"),
) -> None:
    """LLM reviews chains -> sidecar report (.gaia/reviews/)."""
    typer.echo(f"gaia review {path} — not yet implemented")
    raise typer.Exit(1)


@app.command()
def infer(
    path: str = typer.Argument(".", help="Path to knowledge package directory"),
    review_file: str | None = typer.Option(None, "--review", help="Path to review sidecar file"),
) -> None:
    """Compile FG (from review) + BP -> beliefs."""
    typer.echo(f"gaia infer {path} — not yet implemented")
    raise typer.Exit(1)


@app.command()
def publish(
    path: str = typer.Argument(".", help="Path to knowledge package directory"),
    git: bool = typer.Option(False, "--git", help="Publish via git add+commit+push"),
    server: bool = typer.Option(False, "--server", help="Publish to Gaia server API"),
) -> None:
    """Publish to git or server."""
    typer.echo(f"gaia publish {path} — not yet implemented")
    raise typer.Exit(1)


@app.command("init")
def init_cmd(
    name: str = typer.Argument(..., help="Package name"),
) -> None:
    """Initialize a new knowledge package."""
    pkg_dir = Path(name)
    if pkg_dir.exists():
        typer.echo(f"Error: directory '{name}' already exists", err=True)
        raise typer.Exit(1)

    pkg_dir.mkdir(parents=True)

    # package.yaml
    pkg_data = {
        "name": name,
        "version": "0.1.0",
        "manifest": {
            "description": f"Knowledge package: {name}",
            "authors": [],
            "license": "CC-BY-4.0",
        },
        "modules": ["motivation"],
        "export": [],
    }
    (pkg_dir / "package.yaml").write_text(
        yaml.dump(pkg_data, allow_unicode=True, sort_keys=False)
    )

    # motivation.yaml
    mod_data = {
        "type": "motivation_module",
        "name": "motivation",
        "declarations": [
            {
                "type": "question",
                "name": "main_question",
                "content": "What is the main research question?",
            }
        ],
        "export": ["main_question"],
    }
    (pkg_dir / "motivation.yaml").write_text(
        yaml.dump(mod_data, allow_unicode=True, sort_keys=False)
    )

    typer.echo(f"Initialized package '{name}' in ./{name}/")


@app.command()
def show(
    name: str = typer.Argument(..., help="Declaration name to inspect"),
    path: str = typer.Option(".", "--path", "-p", help="Package directory"),
) -> None:
    """Show declaration details + connected chains."""
    typer.echo(f"gaia show {name} — not yet implemented")
    raise typer.Exit(1)


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query text"),
    path: str = typer.Option(".", "--path", "-p", help="Package directory"),
) -> None:
    """Search declarations within the package."""
    typer.echo(f"gaia search '{query}' — not yet implemented")
    raise typer.Exit(1)


@app.command()
def clean(
    path: str = typer.Argument(".", help="Path to knowledge package directory"),
) -> None:
    """Remove build artifacts (.gaia/)."""
    import shutil

    gaia_dir = Path(path) / ".gaia"
    if gaia_dir.exists():
        shutil.rmtree(gaia_dir)
        typer.echo(f"Removed {gaia_dir}")
    else:
        typer.echo(f"No .gaia directory in {path}, nothing to clean.")


if __name__ == "__main__":
    app()
