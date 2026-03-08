# tests/libs/dsl/test_compiler.py
from pathlib import Path

from libs.dsl.loader import load_package
from libs.dsl.resolver import resolve_refs
from libs.dsl.compiler import compile_factor_graph

FIXTURE_DIR = Path(__file__).parents[2] / "fixtures" / "dsl_packages" / "galileo_falling_bodies"


def test_compile_produces_factor_graph():
    pkg = load_package(FIXTURE_DIR)
    pkg = resolve_refs(pkg)
    fg = compile_factor_graph(pkg)
    assert len(fg.variables) == 7
    assert len(fg.factors) == 5


def test_variable_nodes_are_claims_and_settings():
    pkg = load_package(FIXTURE_DIR)
    pkg = resolve_refs(pkg)
    fg = compile_factor_graph(pkg)
    # Variable nodes should include knowledge objects with priors
    # heavier_falls_faster (prior=0.7), everyday_observation (prior=0.95),
    # thought_experiment_env (prior=1.0), vacuum_env (prior=1.0),
    # aristotle_contradicted (prior=0.5), air_resistance_is_confound (prior=0.5),
    # vacuum_prediction (prior=0.5)
    assert len(fg.variables) == 7
    assert set(fg.variables.keys()) == {
        "heavier_falls_faster", "everyday_observation",
        "thought_experiment_env", "vacuum_env",
        "aristotle_contradicted", "air_resistance_is_confound",
        "vacuum_prediction",
    }


def test_factor_nodes_from_chain_steps():
    pkg = load_package(FIXTURE_DIR)
    pkg = resolve_refs(pkg)
    fg = compile_factor_graph(pkg)
    # Factors from: refutation_chain step2, confound_chain step2 (lambda),
    # synthesis_chain step2, inductive_support step2 (lambda), next_steps step2 (lambda)
    assert len(fg.factors) == 5


def test_direct_dependency_creates_edge():
    pkg = load_package(FIXTURE_DIR)
    pkg = resolve_refs(pkg)
    fg = compile_factor_graph(pkg)
    # refutation_chain: heavier_falls_faster --direct--> aristotle_contradicted
    # Find a factor connecting these two variables
    # Find the refutation factor and check its tail/head
    refutation = next(f for f in fg.factors if f["name"] == "refutation_chain.step_2")
    assert "heavier_falls_faster" in refutation["tail"]
    assert "aristotle_contradicted" in refutation["head"]
    assert refutation["probability"] == 0.9


def test_indirect_dependency_excluded_from_edges():
    """Indirect dependencies should NOT create BP edges."""
    pkg = load_package(FIXTURE_DIR)
    pkg = resolve_refs(pkg)
    fg = compile_factor_graph(pkg)
    # thought_experiment_env is used as indirect in refutation_chain
    # It should NOT appear as a tail in that factor
    refutation_factors = [f for f in fg.factors if f.get("name") == "refutation_chain.step_2"]
    assert len(refutation_factors) == 1, "Expected exactly one refutation_chain.step_2 factor"
    factor = refutation_factors[0]
    assert "thought_experiment_env" not in factor.get("tail", [])


def test_exported_only_in_factor_graph():
    """Only exported declarations participate in BP."""
    pkg = load_package(FIXTURE_DIR)
    pkg = resolve_refs(pkg)
    fg = compile_factor_graph(pkg)
    # main_question (from motivation) is exported
    # but it's a Question type — Questions don't participate in BP
    var_names = set(fg.variables.keys())
    assert "main_question" not in var_names


# ── Inline tests (no galileo fixture) ─────────────────────────

from libs.dsl.models import (
    Claim,
    ChainExpr,
    Module,
    Package,
    StepRef,
    StepLambda,
)


def test_compile_empty_package():
    """A package with no modules produces an empty factor graph."""
    pkg = Package(name="empty", modules=[])
    pkg.loaded_modules = []
    fg = compile_factor_graph(pkg)
    assert fg.variables == {}
    assert fg.factors == []


def test_compile_single_chain_inline():
    """Build one module with 1 chain (3 steps) and verify factor graph structure."""
    claim_a = Claim(name="a", content="Claim A", prior=0.6)
    claim_b = Claim(name="b", content="", prior=0.5)
    chain = ChainExpr(
        name="my_chain",
        steps=[
            StepRef(step=1, ref="a"),
            StepLambda(step=2, **{"lambda": "some reasoning"}, prior=0.8),
            StepRef(step=3, ref="b"),
        ],
    )
    mod = Module(
        type="reasoning_module",
        name="m",
        declarations=[claim_a, claim_b, chain],
        export=["a", "b"],
    )
    pkg = Package(name="inline_test", modules=["m"])
    pkg.loaded_modules = [mod]

    fg = compile_factor_graph(pkg)

    # Variables: a (prior=0.6) and b (prior=0.5)
    assert len(fg.variables) == 2
    assert fg.variables["a"] == 0.6
    assert fg.variables["b"] == 0.5

    # Factors: one factor from the lambda step
    assert len(fg.factors) == 1
    factor = fg.factors[0]
    assert factor["name"] == "my_chain.step_2"
    assert factor["tail"] == ["a"]
    assert factor["head"] == ["b"]
    assert factor["probability"] == 0.8
