"""End-to-end integration test: load galileo package, execute, run BP, inspect."""

from pathlib import Path

from libs.dsl.runtime import DSLRuntime

from .conftest import PassthroughExecutor

FIXTURE_DIR = Path(__file__).parents[2] / "fixtures" / "dsl_packages" / "galileo_falling_bodies"


async def test_galileo_full_pipeline():
    """Full pipeline: load -> execute -> infer -> inspect."""
    runtime = DSLRuntime(executor=PassthroughExecutor())
    result = await runtime.run(FIXTURE_DIR)

    # Package loaded correctly
    assert result.package.name == "galileo_falling_bodies"
    assert len(result.package.loaded_modules) == 5

    # Factor graph built
    assert len(result.factor_graph.variables) == 7
    assert len(result.factor_graph.factors) == 5

    # Beliefs computed for all 7 variables
    assert len(result.beliefs) == 7

    # BP should actually change beliefs from priors
    assert result.beliefs["heavier_falls_faster"] != 0.7, "BP should update belief from prior"
    assert result.beliefs["vacuum_prediction"] != 0.5, "BP should update belief from prior"

    # Summary
    summary = result.inspect()
    assert summary["package"] == "galileo_falling_bodies"
    assert summary["modules"] == 5
    assert summary["variables"] == 7
    assert summary["factors"] == 5


async def test_galileo_empty_claims_filled():
    """Execute phase should fill in empty claims."""
    runtime = DSLRuntime(executor=PassthroughExecutor())
    result = await runtime.run(FIXTURE_DIR)

    reasoning = next(m for m in result.package.loaded_modules if m.name == "reasoning")
    for decl in reasoning.declarations:
        if hasattr(decl, "content") and decl.name in [
            "aristotle_contradicted",
            "air_resistance_is_confound",
            "vacuum_prediction",
        ]:
            assert decl.content != "", f"{decl.name} should have content after execution"


async def test_galileo_branching_structure():
    """Two chains branch from heavier_falls_faster, merge at synthesis."""
    runtime = DSLRuntime(executor=PassthroughExecutor())
    result = await runtime.run(FIXTURE_DIR)

    fg = result.factor_graph
    # heavier_falls_faster should appear as tail in at least 2 factors
    # (refutation_chain and confound_chain)
    hff_factors = [f for f in fg.factors if "heavier_falls_faster" in f["tail"]]
    assert len(hff_factors) == 2, "heavier_falls_faster should feed into exactly 2 chains"

    # vacuum_prediction should appear as head in synthesis_chain
    vp_factors = [f for f in fg.factors if "vacuum_prediction" in f["head"]]
    assert len(vp_factors) == 1, "vacuum_prediction should be output of exactly 1 synthesis"
