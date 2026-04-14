"""Tests for gaia infer command."""

from __future__ import annotations

import json

from typer.testing import CliRunner

from gaia.cli.main import app

runner = CliRunner()


def _write_base_package(pkg_dir, *, name: str, version: str = "1.0.0") -> None:
    pkg_dir.mkdir()
    (pkg_dir / "pyproject.toml").write_text(
        f'[project]\nname = "{name}-gaia"\nversion = "{version}"\n\n'
        '[tool.gaia]\nnamespace = "github"\ntype = "knowledge-package"\n'
    )
    (pkg_dir / name).mkdir()


def test_infer_with_priors_py(tmp_path):
    """Package with priors.py — infer reads metadata priors from compiled IR."""
    pkg_dir = tmp_path / "priors_infer"
    _write_base_package(pkg_dir, name="priors_infer")
    (pkg_dir / "priors_infer" / "__init__.py").write_text(
        "from gaia.lang import claim, deduction\n\n"
        'evidence = claim("Evidence.")\n'
        'hypothesis = claim("Hypothesis.")\n'
        "s = deduction(premises=[evidence], conclusion=hypothesis, reason='deduction', prior=0.9)\n"
        '__all__ = ["evidence", "hypothesis", "s"]\n'
    )
    (pkg_dir / "priors_infer" / "priors.py").write_text(
        "from . import evidence, hypothesis\n\n"
        "PRIORS = {\n"
        '    evidence: (0.9, "Direct observation."),\n'
        '    hypothesis: (0.4, "Base rate."),\n'
        "}\n"
    )

    compile_result = runner.invoke(app, ["compile", str(pkg_dir)])
    assert compile_result.exit_code == 0, compile_result.output

    result = runner.invoke(app, ["infer", str(pkg_dir)])
    assert result.exit_code == 0, result.output
    assert "Method:" in result.output

    beliefs = json.loads((pkg_dir / ".gaia" / "beliefs.json").read_text())
    belief_by_label = {item["label"]: item["belief"] for item in beliefs["beliefs"]}
    assert belief_by_label["hypothesis"] > 0.4


def test_infer_without_priors_py(tmp_path):
    """Package without priors.py — infer uses default 0.5 priors."""
    pkg_dir = tmp_path / "no_priors_infer"
    _write_base_package(pkg_dir, name="no_priors_infer")
    (pkg_dir / "no_priors_infer" / "__init__.py").write_text(
        "from gaia.lang import claim, deduction\n\n"
        'evidence = claim("Evidence.")\n'
        'hypothesis = claim("Hypothesis.")\n'
        "s = deduction(premises=[evidence], conclusion=hypothesis, reason='deduction', prior=0.9)\n"
        '__all__ = ["evidence", "hypothesis", "s"]\n'
    )

    compile_result = runner.invoke(app, ["compile", str(pkg_dir)])
    assert compile_result.exit_code == 0, compile_result.output

    result = runner.invoke(app, ["infer", str(pkg_dir)])
    assert result.exit_code == 0, result.output

    beliefs = json.loads((pkg_dir / ".gaia" / "beliefs.json").read_text())
    assert len(beliefs["beliefs"]) >= 2


def test_infer_fails_when_compiled_artifacts_are_stale(tmp_path):
    pkg_dir = tmp_path / "infer_demo"
    _write_base_package(pkg_dir, name="infer_demo")
    (pkg_dir / "infer_demo" / "__init__.py").write_text(
        "from gaia.lang import claim\n\n"
        'main_claim = claim("Original claim.")\n'
        '__all__ = ["main_claim"]\n'
    )

    compile_result = runner.invoke(app, ["compile", str(pkg_dir)])
    assert compile_result.exit_code == 0, compile_result.output

    (pkg_dir / "infer_demo" / "__init__.py").write_text(
        "from gaia.lang import claim\n\n"
        'main_claim = claim("Updated claim.")\n'
        '__all__ = ["main_claim"]\n'
    )

    result = runner.invoke(app, ["infer", str(pkg_dir)])
    assert result.exit_code != 0
    assert "stale" in result.output.lower()


def test_infer_with_deduction_strategy(tmp_path):
    """Deduction strategy auto-formalizes and runs BP successfully."""
    pkg_dir = tmp_path / "deduction_demo"
    _write_base_package(pkg_dir, name="deduction_demo")
    (pkg_dir / "deduction_demo" / "__init__.py").write_text(
        "from gaia.lang import deduction, claim\n\n"
        'law = claim("forall x. P(x)")\n'
        'instance = claim("P(a)")\n'
        "proof = deduction(premises=[law], conclusion=instance, reason='instantiate', prior=0.9)\n"
        '__all__ = ["law", "instance", "proof"]\n'
    )
    (pkg_dir / "deduction_demo" / "priors.py").write_text(
        "from . import law, instance\n\n"
        "PRIORS = {\n"
        '    law: (0.9, "Well established."),\n'
        '    instance: (0.5, "Follows from law."),\n'
        "}\n"
    )

    compile_result = runner.invoke(app, ["compile", str(pkg_dir)])
    assert compile_result.exit_code == 0, compile_result.output

    result = runner.invoke(app, ["infer", str(pkg_dir)])
    assert result.exit_code == 0, result.output


def test_infer_loads_upstream_beliefs_for_foreign_nodes(tmp_path, monkeypatch):
    """When dep_beliefs are present, foreign nodes use upstream beliefs as priors."""
    # Create upstream dependency package
    dep_dir = tmp_path / "upstream_dep"
    dep_dir.mkdir()
    (dep_dir / "pyproject.toml").write_text(
        '[project]\nname = "upstream-dep-gaia"\nversion = "1.0.0"\n\n'
        '[tool.gaia]\nnamespace = "github"\ntype = "knowledge-package"\n'
    )
    dep_src = dep_dir / "upstream_dep"
    dep_src.mkdir()
    (dep_src / "__init__.py").write_text(
        "from gaia.lang import claim\n\n"
        'upstream_claim = claim("Upstream conclusion.")\n'
        '__all__ = ["upstream_claim"]\n'
    )
    monkeypatch.syspath_prepend(str(dep_dir))

    # Create local package that imports from upstream
    pkg_dir = tmp_path / "local_pkg"
    _write_base_package(pkg_dir, name="local_pkg")
    (pkg_dir / "local_pkg" / "__init__.py").write_text(
        "from gaia.lang import claim, deduction\n"
        "from upstream_dep import upstream_claim\n\n"
        'local_obs = claim("Local observation.")\n'
        "deduction(premises=[upstream_claim, local_obs], conclusion=claim('Result.'), "
        "reason='apply upstream', prior=0.9)\n"
        '__all__ = ["local_obs"]\n'
    )

    compile_result = runner.invoke(app, ["compile", str(pkg_dir)])
    assert compile_result.exit_code == 0, compile_result.output

    # Write dep_beliefs with high upstream belief
    dep_beliefs_dir = pkg_dir / ".gaia" / "dep_beliefs"
    dep_beliefs_dir.mkdir(parents=True)
    (dep_beliefs_dir / "upstream_dep.json").write_text(
        json.dumps(
            {
                "manifest_schema_version": 1,
                "package": "upstream-dep",
                "version": "1.0.0",
                "ir_hash": "sha256:fake",
                "beliefs": [
                    {
                        "knowledge_id": "github:upstream_dep::upstream_claim",
                        "label": "upstream_claim",
                        "belief": 0.85,
                    }
                ],
            }
        )
    )

    result = runner.invoke(app, ["infer", str(pkg_dir)])
    assert result.exit_code == 0, result.output
    assert "upstream belief" in result.output.lower()

    beliefs = json.loads((pkg_dir / ".gaia" / "beliefs.json").read_text())
    belief_by_id = {b["knowledge_id"]: b["belief"] for b in beliefs["beliefs"]}
    # The upstream claim should NOT be at 0.5 default — it should reflect the upstream prior
    upstream_belief = belief_by_id.get("github:upstream_dep::upstream_claim")
    assert upstream_belief is not None
    assert upstream_belief != 0.5, "Foreign node should not use default 0.5 when dep_beliefs exist"


def test_collect_foreign_node_priors_unit(tmp_path):
    """Unit test for collect_foreign_node_priors — no inference, just file parsing."""
    from types import SimpleNamespace

    from gaia.cli._packages import collect_foreign_node_priors

    pkg_path = tmp_path / "test_pkg"
    pkg_path.mkdir()

    # No dep_beliefs dir → empty dict
    result = collect_foreign_node_priors(
        SimpleNamespace(
            namespace="github",
            package_name="test_pkg",
            knowledges=[],
        ),
        pkg_path,
    )
    assert result == {}

    # Create dep_beliefs with upstream data
    dep_beliefs_dir = pkg_path / ".gaia" / "dep_beliefs"
    dep_beliefs_dir.mkdir(parents=True)
    (dep_beliefs_dir / "upstream_a.json").write_text(
        json.dumps(
            {
                "beliefs": [
                    {"knowledge_id": "github:upstream_a::claim_x", "belief": 0.9},
                    {"knowledge_id": "github:upstream_a::claim_y", "belief": 0.3},
                ]
            }
        )
    )
    (dep_beliefs_dir / "upstream_b.json").write_text(
        json.dumps(
            {
                "beliefs": [
                    {"knowledge_id": "github:upstream_b::claim_z", "belief": 0.7},
                ]
            }
        )
    )
    # Also add a malformed file to verify graceful handling
    (dep_beliefs_dir / "bad.json").write_text("not valid json")

    # Mock graph with local + foreign nodes
    local_node = SimpleNamespace(id="github:test_pkg::local_claim")
    foreign_a = SimpleNamespace(id="github:upstream_a::claim_x")
    foreign_b = SimpleNamespace(id="github:upstream_b::claim_z")
    foreign_missing = SimpleNamespace(id="github:upstream_c::no_data")

    graph = SimpleNamespace(
        namespace="github",
        package_name="test_pkg",
        knowledges=[local_node, foreign_a, foreign_b, foreign_missing],
    )

    result = collect_foreign_node_priors(graph, pkg_path)
    # Only foreign nodes with matching upstream beliefs
    assert result == {
        "github:upstream_a::claim_x": 0.9,
        "github:upstream_b::claim_z": 0.7,
    }
    # Local node and unmatched foreign node are excluded
    assert "github:test_pkg::local_claim" not in result
    assert "github:upstream_c::no_data" not in result
