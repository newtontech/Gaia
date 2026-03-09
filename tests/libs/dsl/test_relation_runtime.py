"""Runtime integration tests for Relation types."""

from libs.dsl.models import (
    ChainExpr,
    Claim,
    Contradiction,
    Equivalence,
    Module,
    Package,
    StepLambda,
    StepRef,
)
from libs.dsl.runtime import DSLRuntime, RuntimeResult


async def test_contradiction_gets_belief_after_inference():
    """Relation declarations should have .belief set after BP."""
    claim_a = Claim(name="a", content="A", prior=0.8)
    claim_b = Claim(name="b", content="B", prior=0.7)
    contra = Contradiction(
        name="a_contradicts_b",
        between=["a", "b"],
        prior=0.95,
    )
    mod = Module(
        type="reasoning_module",
        name="m",
        declarations=[claim_a, claim_b, contra],
        export=["a", "b", "a_contradicts_b"],
    )
    pkg = Package(name="test_relation_bp", modules=["m"])
    pkg.loaded_modules = [mod]

    runtime = DSLRuntime()
    result = RuntimeResult(package=pkg)
    result = await runtime.infer(result)

    # Relation should have belief computed
    assert "a_contradicts_b" in result.beliefs
    assert contra.belief is not None
    assert contra.belief == result.beliefs["a_contradicts_b"]


async def test_equivalence_gets_belief_after_inference():
    """Equivalence relation should also get belief."""
    claim_x = Claim(name="x", content="X", prior=0.6)
    claim_y = Claim(name="y", content="Y", prior=0.9)
    equiv = Equivalence(
        name="x_equiv_y",
        between=["x", "y"],
        prior=0.85,
    )
    mod = Module(
        type="reasoning_module",
        name="m",
        declarations=[claim_x, claim_y, equiv],
        export=["x", "y", "x_equiv_y"],
    )
    pkg = Package(name="test_equiv_bp", modules=["m"])
    pkg.loaded_modules = [mod]

    runtime = DSLRuntime()
    result = RuntimeResult(package=pkg)
    result = await runtime.infer(result)

    assert equiv.belief is not None
    # Equivalence should pull beliefs together
    prior_gap = abs(0.9 - 0.6)
    posterior_gap = abs(result.beliefs["y"] - result.beliefs["x"])
    assert posterior_gap < prior_gap


async def test_contradiction_weakens_shared_premises():
    """Full pipeline: Contradiction relation should weaken beliefs of claims
    that are premises of both contradicting claims."""
    # Setup: shared premise -> two contradicting conclusions
    premise = Claim(name="premise", content="Shared premise", prior=0.8)
    claim_a = Claim(name="a", content="Prediction A", prior=0.5)
    claim_b = Claim(name="b", content="Prediction B", prior=0.5)

    chain_a = ChainExpr(
        name="chain_a",
        steps=[
            StepRef(step=1, ref="premise"),
            StepLambda(step=2, **{"lambda": "derive A"}, prior=0.9),
            StepRef(step=3, ref="a"),
        ],
    )
    chain_b = ChainExpr(
        name="chain_b",
        steps=[
            StepRef(step=1, ref="premise"),
            StepLambda(step=2, **{"lambda": "derive B"}, prior=0.9),
            StepRef(step=3, ref="b"),
        ],
    )
    contra = Contradiction(
        name="a_vs_b",
        between=["a", "b"],
        prior=0.95,
    )

    mod = Module(
        type="reasoning_module",
        name="m",
        declarations=[premise, claim_a, claim_b, chain_a, chain_b, contra],
        export=["premise", "a", "b", "a_vs_b"],
    )
    pkg = Package(name="test_integration", modules=["m"])
    pkg.loaded_modules = [mod]

    runtime = DSLRuntime()
    result = RuntimeResult(package=pkg)
    result = await runtime.infer(result)

    # Both claims should be lower than without contradiction
    # Without contradiction, chains would push a and b above 0.5
    # With contradiction, they can't both be true -> both drop
    assert result.beliefs["a"] < 0.8  # limited by contradiction
    assert result.beliefs["b"] < 0.8

    # Shared premise should also be weakened (indirect BP propagation)
    assert result.beliefs["premise"] < 0.8

    # Contradiction belief should stay high
    assert result.beliefs["a_vs_b"] > 0.8
