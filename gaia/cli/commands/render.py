"""gaia render -- generate presentation outputs (docs and/or GitHub site) from a reviewed package."""

from __future__ import annotations

from enum import Enum

import typer


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
