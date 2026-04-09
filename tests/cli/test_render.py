"""Tests for gaia render command."""

from __future__ import annotations

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


def _prepare_inferred_package(tmp_path, name: str = "render_demo"):
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
    content = docs_path.read_text()
    assert "# render_demo-gaia" in content or "# render_demo" in content

    github_dir = pkg_dir / ".github-output"
    assert (github_dir / "wiki" / "Home.md").exists()
    assert (github_dir / "manifest.json").exists()
    assert (github_dir / "docs" / "public" / "data" / "graph.json").exists()
    assert (github_dir / "README.md").exists()
