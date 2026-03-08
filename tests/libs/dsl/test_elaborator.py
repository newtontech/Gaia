"""Tests for the DSL elaborator — deterministic template expansion."""

from pathlib import Path

from libs.dsl.elaborator import ElaboratedPackage, elaborate_package
from libs.dsl.loader import load_package
from libs.dsl.resolver import resolve_refs


FIXTURE_PATH = Path("tests/fixtures/dsl_packages/galileo_falling_bodies")


def test_elaborate_returns_elaborated_package():
    pkg = load_package(FIXTURE_PATH)
    pkg = resolve_refs(pkg)
    result = elaborate_package(pkg)
    assert isinstance(result, ElaboratedPackage)
    assert result.package.name == "galileo_falling_bodies"


def test_elaborate_renders_step_apply_prompts():
    """StepApply templates like {law} should be substituted with resolved arg content."""
    pkg = load_package(FIXTURE_PATH)
    pkg = resolve_refs(pkg)
    result = elaborate_package(pkg)
    prompts = {(p["chain"], p["step"]): p for p in result.prompts}
    key = ("drag_prediction_chain", 2)
    assert key in prompts
    rendered = prompts[key]["rendered"]
    assert "{law}" not in rendered
    assert "{env}" not in rendered
    assert "重的物体" in rendered  # from heavier_falls_faster content
    assert "重球" in rendered  # from thought_experiment_env content


def test_elaborate_records_lambda_content():
    """StepLambda content should be recorded as-is (no template substitution needed)."""
    pkg = load_package(FIXTURE_PATH)
    pkg = resolve_refs(pkg)
    result = elaborate_package(pkg)
    prompts = {(p["chain"], p["step"]): p for p in result.prompts}
    key = ("combined_weight_chain", 2)
    assert key in prompts
    assert "复合体" in prompts[key]["rendered"]


def test_elaborate_records_arg_metadata():
    """Each rendered prompt should include arg refs and dependency types."""
    pkg = load_package(FIXTURE_PATH)
    pkg = resolve_refs(pkg)
    result = elaborate_package(pkg)
    prompts = {(p["chain"], p["step"]): p for p in result.prompts}
    key = ("drag_prediction_chain", 2)
    prompt = prompts[key]
    assert len(prompt["args"]) == 2
    assert prompt["args"][0]["ref"] == "heavier_falls_faster"
    assert prompt["args"][0]["dependency"] == "direct"
    assert prompt["args"][1]["ref"] == "thought_experiment_env"
    assert prompt["args"][1]["dependency"] == "indirect"


def test_elaborate_does_not_modify_original():
    """Elaboration should not mutate the original package."""
    pkg = load_package(FIXTURE_PATH)
    pkg = resolve_refs(pkg)
    original_content = None
    for mod in pkg.loaded_modules:
        for decl in mod.declarations:
            if decl.name == "deduce_drag_effect":
                original_content = decl.content
                break
    elaborate_package(pkg)
    for mod in pkg.loaded_modules:
        for decl in mod.declarations:
            if decl.name == "deduce_drag_effect":
                assert decl.content == original_content


def test_elaborate_covers_all_apply_and_lambda_steps():
    """Every StepApply and StepLambda in the package should produce a prompt."""
    pkg = load_package(FIXTURE_PATH)
    pkg = resolve_refs(pkg)
    result = elaborate_package(pkg)
    assert len(result.prompts) >= 11
