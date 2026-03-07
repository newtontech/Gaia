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
    # Factor graph should have variable nodes and factor nodes
    assert len(fg.variables) > 0
    assert len(fg.factors) > 0


def test_variable_nodes_are_claims_and_settings():
    pkg = load_package(FIXTURE_DIR)
    pkg = resolve_refs(pkg)
    fg = compile_factor_graph(pkg)
    # Variable nodes should include knowledge objects with priors
    # heavier_falls_faster (prior=0.7), everyday_observation (prior=0.95),
    # thought_experiment_env (prior=1.0), vacuum_env (prior=1.0),
    # aristotle_contradicted (prior=0.5), air_resistance_is_confound (prior=0.5),
    # vacuum_prediction (prior=0.5)
    assert len(fg.variables) >= 7


def test_factor_nodes_from_chain_steps():
    pkg = load_package(FIXTURE_DIR)
    pkg = resolve_refs(pkg)
    fg = compile_factor_graph(pkg)
    # Factors from: refutation_chain step2, confound_chain step2 (lambda),
    # synthesis_chain step2, inductive_support step2 (lambda), next_steps step2 (lambda)
    assert len(fg.factors) >= 5


def test_direct_dependency_creates_edge():
    pkg = load_package(FIXTURE_DIR)
    pkg = resolve_refs(pkg)
    fg = compile_factor_graph(pkg)
    # refutation_chain: heavier_falls_faster --direct--> aristotle_contradicted
    # Find a factor connecting these two variables
    has_direct = any(f for f in fg.factors if "heavier_falls_faster" in str(f.get("tail", [])))
    assert has_direct


def test_indirect_dependency_excluded_from_edges():
    """Indirect dependencies should NOT create BP edges."""
    pkg = load_package(FIXTURE_DIR)
    pkg = resolve_refs(pkg)
    fg = compile_factor_graph(pkg)
    # thought_experiment_env is used as indirect in refutation_chain
    # It should NOT appear as a tail in that factor
    refutation_factors = [f for f in fg.factors if f.get("name") == "refutation_chain.step_2"]
    if refutation_factors:
        factor = refutation_factors[0]
        assert "thought_experiment_env" not in [t for t in factor.get("tail", [])]


def test_exported_only_in_factor_graph():
    """Only exported declarations participate in BP."""
    pkg = load_package(FIXTURE_DIR)
    pkg = resolve_refs(pkg)
    fg = compile_factor_graph(pkg)
    # main_question (from motivation) is exported
    # but it's a Question type — Questions don't participate in BP
    var_names = set(fg.variables.keys())
    assert "main_question" not in var_names
