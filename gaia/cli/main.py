"""Gaia CLI — knowledge package authoring toolkit."""

import typer

from gaia.cli.commands.compile import compile_command

app = typer.Typer(
    name="gaia",
    help="Gaia — knowledge package authoring toolkit.",
    no_args_is_help=True,
)


@app.callback()
def _callback() -> None:
    """Gaia — knowledge package authoring toolkit."""


app.command(name="compile")(compile_command)
