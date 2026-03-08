"""Tests for the DSL Runtime — Load -> Execute -> Infer -> Inspect pipeline."""

from pathlib import Path

from libs.dsl.runtime import DSLRuntime, RuntimeResult

from .conftest import MockExecutor

FIXTURE_DIR = Path(__file__).parents[2] / "fixtures" / "dsl_packages" / "galileo_falling_bodies"


async def test_runtime_full_pipeline():
    runtime = DSLRuntime(executor=MockExecutor())
    result = await runtime.run(FIXTURE_DIR)

    assert isinstance(result, RuntimeResult)
    assert result.package.name == "galileo_falling_bodies"
    assert len(result.beliefs) == 7
    assert result.factor_graph is not None


async def test_runtime_beliefs_computed():
    runtime = DSLRuntime(executor=MockExecutor())
    result = await runtime.run(FIXTURE_DIR)

    # heavier_falls_faster has prior=0.7, after BP it should change
    assert "heavier_falls_faster" in result.beliefs
    assert result.beliefs["heavier_falls_faster"] != 0.7
    # vacuum_prediction has prior=0.5
    assert "vacuum_prediction" in result.beliefs
    assert result.beliefs["vacuum_prediction"] != 0.5


async def test_runtime_load_only():
    runtime = DSLRuntime(executor=MockExecutor())
    result = await runtime.load(FIXTURE_DIR)

    assert result.package.name == "galileo_falling_bodies"
    assert len(result.package.loaded_modules) == 5
    # No beliefs yet (not inferred)
    assert len(result.beliefs) == 0


async def test_runtime_beliefs_written_back_to_declarations():
    """After run(), Claim.belief should reflect BP posteriors."""
    runtime = DSLRuntime(executor=MockExecutor())
    result = await runtime.run(FIXTURE_DIR)

    # Find heavier_falls_faster claim via the package
    aristotle = next(m for m in result.package.loaded_modules if m.name == "aristotle")
    hff = next(d for d in aristotle.declarations if d.name == "heavier_falls_faster")

    # belief field should be set and match result.beliefs
    assert hff.belief is not None
    assert hff.belief == result.beliefs["heavier_falls_faster"]
    # belief should differ from prior (BP updated it)
    assert hff.belief != hff.prior

    # Also check a Setting gets its belief written back
    setting_mod = next(m for m in result.package.loaded_modules if m.name == "setting")
    thought_env = next(
        d for d in setting_mod.declarations if d.name == "thought_experiment_env"
    )
    assert thought_env.belief is not None
    assert thought_env.belief == result.beliefs["thought_experiment_env"]


async def test_runtime_execute_only():
    """Execute fills claims but no BP."""
    runtime = DSLRuntime(executor=MockExecutor())
    result = await runtime.load(FIXTURE_DIR)
    result = await runtime.execute(result)

    # Claims should be filled
    reasoning = next(m for m in result.package.loaded_modules if m.name == "reasoning")
    ac = next(d for d in reasoning.declarations if d.name == "aristotle_contradicted")
    assert ac.content != ""

    # But no factor graph or beliefs
    assert result.factor_graph is None
    assert len(result.beliefs) == 0


async def test_runtime_infer_only():
    """Infer without execute — BP runs on priors alone."""
    runtime = DSLRuntime()  # no executor
    result = await runtime.load(FIXTURE_DIR)
    result = await runtime.infer(result)

    # Factor graph should exist
    assert result.factor_graph is not None
    assert len(result.factor_graph.variables) == 7

    # Beliefs should be computed (from priors only)
    assert len(result.beliefs) == 7


async def test_runtime_inspect():
    runtime = DSLRuntime(executor=MockExecutor())
    result = await runtime.run(FIXTURE_DIR)
    summary = result.inspect()

    assert summary["package"] == "galileo_falling_bodies"
    assert summary["modules"] == 5
    assert summary["variables"] == 7
    assert summary["factors"] == 5
    assert len(summary["beliefs"]) == 7
