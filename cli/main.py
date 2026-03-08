"""Gaia CLI — proof assistant for probabilistic defeasible reasoning."""

from __future__ import annotations

import typer

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
    typer.echo(f"gaia build {path} — not yet implemented")
    raise typer.Exit(1)


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
    typer.echo(f"gaia init {name} — not yet implemented")
    raise typer.Exit(1)


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
    typer.echo(f"gaia clean {path} — not yet implemented")
    raise typer.Exit(1)


if __name__ == "__main__":
    app()
