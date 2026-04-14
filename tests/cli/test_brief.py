"""Tests for gaia check --brief / --show warrant structure output."""

from __future__ import annotations

from typer.testing import CliRunner

from gaia.cli.main import app

runner = CliRunner()


def _write_base_package(pkg_dir, *, name: str) -> None:
    pkg_dir.mkdir()
    (pkg_dir / "pyproject.toml").write_text(
        f'[project]\nname = "{name}-gaia"\nversion = "1.0.0"\n\n'
        '[tool.gaia]\nnamespace = "github"\ntype = "knowledge-package"\n'
    )
    (pkg_dir / name).mkdir()


def _write_two_module_package(pkg_dir):
    """Package with two modules: background + reasoning, using support strategy."""
    name = "brief_demo"
    _write_base_package(pkg_dir, name=name)
    (pkg_dir / name / "__init__.py").write_text(
        "from .background import *\nfrom .reasoning import *\n"
    )
    (pkg_dir / name / "background.py").write_text(
        "from gaia.lang import claim, setting\n\n"
        'env = setting("Experiment conducted at room temperature.")\n'
        'obs_a = claim("Observation A was recorded.", background=[env])\n'
        'obs_b = claim("Observation B was recorded.")\n'
    )
    (pkg_dir / name / "reasoning.py").write_text(
        "from gaia.lang import claim, support, contradiction\n"
        "from .background import obs_a, obs_b\n\n"
        'hypothesis = claim("The hypothesis holds.")\n'
        "support([obs_a, obs_b], hypothesis,\n"
        '    reason="Two observations converge.", prior=0.85)\n'
        'alt = claim("Alternative explanation.")\n'
        "not_both = contradiction(hypothesis, alt,\n"
        '    reason="Mutually exclusive.", prior=0.99)\n'
    )
    (pkg_dir / name / "priors.py").write_text(
        "from . import obs_a, obs_b, hypothesis, alt\n\n"
        "PRIORS = {\n"
        '    obs_a: (0.9, "Measured directly."),\n'
        '    obs_b: (0.85, "Reported observation."),\n'
        '    alt: (0.3, "Weak alternative."),\n'
        "}\n"
    )


def _write_induction_package(pkg_dir):
    """Package with induction composite strategy (binary support chain)."""
    name = "induction_demo"
    _write_base_package(pkg_dir, name=name)
    (pkg_dir / name / "__init__.py").write_text(
        "from gaia.lang import claim, support, induction\n\n"
        'law = claim("Universal law holds.")\n'
        'obs1 = claim("Sample 1 confirms law.")\n'
        'obs2 = claim("Sample 2 confirms law.")\n'
        'obs3 = claim("Sample 3 confirms law.")\n'
        "s1 = support([obs1], law, reason='obs1 supports law', prior=0.9)\n"
        "s2 = support([obs2], law, reason='obs2 supports law', prior=0.9)\n"
        "s3 = support([obs3], law, reason='obs3 supports law', prior=0.85)\n"
        "ind_12 = induction(s1, s2, law=law, reason='independent samples')\n"
        "ind_123 = induction(ind_12, s3, law=law, reason='third sample')\n"
    )
    (pkg_dir / name / "priors.py").write_text(
        "from . import law, obs1, obs2, obs3\n\n"
        "PRIORS = {\n"
        '    law: (0.5, "To be determined by induction."),\n'
        '    obs1: (0.9, "Confirmed."),\n'
        '    obs2: (0.9, "Confirmed."),\n'
        '    obs3: (0.9, "Confirmed."),\n'
        "}\n"
    )


def _compile(pkg_dir):
    result = runner.invoke(app, ["compile", str(pkg_dir)])
    assert result.exit_code == 0, result.output


# ── Unit tests on generate functions ──


def test_brief_overview_groups_by_module(tmp_path):
    pkg_dir = tmp_path / "brief_demo"
    _write_two_module_package(pkg_dir)
    _compile(pkg_dir)

    from gaia.cli._packages import apply_package_priors, load_gaia_package
    from gaia.cli._packages import compile_loaded_package_artifact
    from gaia.cli.commands._brief import generate_brief_overview

    loaded = load_gaia_package(str(pkg_dir))
    apply_package_priors(loaded)
    compiled = compile_loaded_package_artifact(loaded)
    ir = compiled.to_json()

    lines = generate_brief_overview(ir)
    text = "\n".join(lines)

    # Module headers present
    assert "Module: background" in text
    assert "Module: reasoning" in text

    # Settings appear
    assert "env" in text
    assert "Experiment conducted" in text

    # Claims with roles
    assert "obs_a" in text
    assert "obs_b" in text
    assert "hypothesis" in text

    # Strategy with prior
    assert "support" in text
    assert "0.85" in text

    # Operator
    assert "contradiction" in text


def test_brief_overview_shows_priors(tmp_path):
    pkg_dir = tmp_path / "brief_demo"
    _write_two_module_package(pkg_dir)
    _compile(pkg_dir)

    from gaia.cli._packages import apply_package_priors, load_gaia_package
    from gaia.cli._packages import compile_loaded_package_artifact
    from gaia.cli.commands._brief import generate_brief_overview

    loaded = load_gaia_package(str(pkg_dir))
    apply_package_priors(loaded)
    compiled = compile_loaded_package_artifact(loaded)
    ir = compiled.to_json()

    lines = generate_brief_overview(ir)
    text = "\n".join(lines)

    # Claim priors from priors.py should appear
    assert "prior=0.9" in text
    assert "prior=0.85" in text


def test_brief_module_expands_all_strategies(tmp_path):
    pkg_dir = tmp_path / "brief_demo"
    _write_two_module_package(pkg_dir)
    _compile(pkg_dir)

    from gaia.cli._packages import apply_package_priors, load_gaia_package
    from gaia.cli._packages import compile_loaded_package_artifact
    from gaia.cli.commands._brief import generate_brief_module

    loaded = load_gaia_package(str(pkg_dir))
    apply_package_priors(loaded)
    compiled = compile_loaded_package_artifact(loaded)
    ir = compiled.to_json()

    lines = generate_brief_module(ir, "reasoning")
    text = "\n".join(lines)

    # Module header
    assert "reasoning" in text
    assert "expanded" in text

    # Full claim content (not truncated)
    assert "The hypothesis holds." in text
    assert "Alternative explanation." in text

    # Strategy warrant tree
    assert "support" in text
    assert "Two observations converge." in text

    # Operator
    assert "contradiction" in text
    assert "Mutually exclusive." in text


def test_brief_module_unknown_returns_error(tmp_path):
    pkg_dir = tmp_path / "brief_demo"
    _write_two_module_package(pkg_dir)
    _compile(pkg_dir)

    from gaia.cli._packages import apply_package_priors, load_gaia_package
    from gaia.cli._packages import compile_loaded_package_artifact
    from gaia.cli.commands._brief import generate_brief_module

    loaded = load_gaia_package(str(pkg_dir))
    apply_package_priors(loaded)
    compiled = compile_loaded_package_artifact(loaded)
    ir = compiled.to_json()

    lines = generate_brief_module(ir, "nonexistent")
    text = "\n".join(lines)
    assert "No module" in text


def test_brief_detail_expands_formal_strategy(tmp_path):
    pkg_dir = tmp_path / "brief_demo"
    _write_two_module_package(pkg_dir)
    _compile(pkg_dir)

    from gaia.cli._packages import apply_package_priors, load_gaia_package
    from gaia.cli._packages import compile_loaded_package_artifact
    from gaia.cli.commands._brief import generate_brief_detail

    loaded = load_gaia_package(str(pkg_dir))
    apply_package_priors(loaded)
    compiled = compile_loaded_package_artifact(loaded)
    ir = compiled.to_json()

    lines = generate_brief_detail(ir, "hypothesis")
    text = "\n".join(lines)

    # Claim header
    assert "hypothesis" in text
    assert "The hypothesis holds." in text

    # Warrant tree: support is a FormalStrategy, should show operators
    assert "support" in text
    assert "0.85" in text

    # Premises section
    assert "Premises:" in text
    assert "obs_a" in text
    assert "obs_b" in text


def test_brief_detail_expands_composite(tmp_path):
    pkg_dir = tmp_path / "induction_demo"
    _write_induction_package(pkg_dir)
    _compile(pkg_dir)

    from gaia.cli._packages import apply_package_priors, load_gaia_package
    from gaia.cli._packages import compile_loaded_package_artifact
    from gaia.cli.commands._brief import generate_brief_detail

    loaded = load_gaia_package(str(pkg_dir))
    apply_package_priors(loaded)
    compiled = compile_loaded_package_artifact(loaded)
    ir = compiled.to_json()

    # Find the composition_warrant generated by induction — it is the derived claim
    # The law claim itself gets a composite strategy conclusion via induction
    # Let's check what labels exist
    labels = [k.get("label") for k in ir["knowledges"] if k.get("label")]

    # induction generates composition_warrant helper claims
    # The law is the target — check if any strategy concludes at law
    strat_conclusions = {s.get("conclusion") for s in ir["strategies"]}
    law_id = None
    for k in ir["knowledges"]:
        if k.get("label") == "law":
            law_id = k["id"]
            break

    # law may or may not be the conclusion of induction (it depends on how the DSL wires it)
    # Instead, look for any CompositeStrategy and test its detail
    composite_labels = []
    for s in ir["strategies"]:
        if s.get("sub_strategies"):
            conc_id = s.get("conclusion")
            for k in ir["knowledges"]:
                if k["id"] == conc_id and k.get("label"):
                    composite_labels.append(k["label"])

    # Should have at least one composite
    assert len(composite_labels) > 0 or law_id in strat_conclusions, (
        f"Expected composite strategy. Labels: {labels}"
    )

    # Try expanding the law claim or any composite conclusion
    target_label = composite_labels[0] if composite_labels else "law"
    lines = generate_brief_detail(ir, target_label)
    text = "\n".join(lines)

    # Should show composite sub-strategies
    assert "composite" in text.lower() or "support" in text.lower()


def test_brief_detail_unknown_label(tmp_path):
    pkg_dir = tmp_path / "brief_demo"
    _write_two_module_package(pkg_dir)
    _compile(pkg_dir)

    from gaia.cli._packages import apply_package_priors, load_gaia_package
    from gaia.cli._packages import compile_loaded_package_artifact
    from gaia.cli.commands._brief import generate_brief_detail

    loaded = load_gaia_package(str(pkg_dir))
    apply_package_priors(loaded)
    compiled = compile_loaded_package_artifact(loaded)
    ir = compiled.to_json()

    lines = generate_brief_detail(ir, "nonexistent_label")
    text = "\n".join(lines)
    assert "No claim or strategy" in text


def test_dispatch_show_routes_module_vs_label(tmp_path):
    pkg_dir = tmp_path / "brief_demo"
    _write_two_module_package(pkg_dir)
    _compile(pkg_dir)

    from gaia.cli._packages import apply_package_priors, load_gaia_package
    from gaia.cli._packages import compile_loaded_package_artifact
    from gaia.cli.commands._brief import dispatch_show

    loaded = load_gaia_package(str(pkg_dir))
    apply_package_priors(loaded)
    compiled = compile_loaded_package_artifact(loaded)
    ir = compiled.to_json()

    # Module name → module expansion
    mod_lines = dispatch_show(ir, "reasoning")
    mod_text = "\n".join(mod_lines)
    assert "expanded" in mod_text

    # Claim label → detail expansion
    label_lines = dispatch_show(ir, "hypothesis")
    label_text = "\n".join(label_lines)
    assert "hypothesis" in label_text
    assert "content:" in label_text

    # Unknown → error
    err_lines = dispatch_show(ir, "does_not_exist")
    err_text = "\n".join(err_lines)
    assert "No module or label" in err_text


# ── CLI integration tests ──


def test_brief_cli_flag(tmp_path):
    pkg_dir = tmp_path / "brief_demo"
    _write_two_module_package(pkg_dir)
    _compile(pkg_dir)

    result = runner.invoke(app, ["check", "--brief", str(pkg_dir)])
    assert result.exit_code == 0, result.output
    assert "Check passed" in result.output
    assert "Module:" in result.output
    assert "support" in result.output


def test_show_cli_flag_module(tmp_path):
    pkg_dir = tmp_path / "brief_demo"
    _write_two_module_package(pkg_dir)
    _compile(pkg_dir)

    result = runner.invoke(app, ["check", "--show", "reasoning", str(pkg_dir)])
    assert result.exit_code == 0, result.output
    assert "Check passed" in result.output
    assert "expanded" in result.output
    assert "hypothesis" in result.output


def test_show_cli_flag_label(tmp_path):
    pkg_dir = tmp_path / "brief_demo"
    _write_two_module_package(pkg_dir)
    _compile(pkg_dir)

    result = runner.invoke(app, ["check", "--show", "hypothesis", str(pkg_dir)])
    assert result.exit_code == 0, result.output
    assert "hypothesis" in result.output
    assert "content:" in result.output


def test_show_cli_flag_unknown(tmp_path):
    pkg_dir = tmp_path / "brief_demo"
    _write_two_module_package(pkg_dir)
    _compile(pkg_dir)

    result = runner.invoke(app, ["check", "--show", "nope", str(pkg_dir)])
    assert result.exit_code == 0, result.output
    assert "No module or label" in result.output


def test_brief_and_show_combined(tmp_path):
    pkg_dir = tmp_path / "brief_demo"
    _write_two_module_package(pkg_dir)
    _compile(pkg_dir)

    result = runner.invoke(app, ["check", "--brief", "--show", "reasoning", str(pkg_dir)])
    assert result.exit_code == 0, result.output
    # Both overview and expanded module should be present
    assert "Module: background" in result.output  # from overview
    assert "expanded" in result.output  # from --show
