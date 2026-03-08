# tests/libs/dsl/test_executor.py
from pathlib import Path

from libs.dsl.executor import execute_package
from libs.dsl.loader import load_package
from libs.dsl.resolver import resolve_refs

from .conftest import MockExecutor

FIXTURE_DIR = Path(__file__).parents[2] / "fixtures" / "dsl_packages" / "galileo_falling_bodies"


def test_execute_fills_empty_claims():
    pkg = load_package(FIXTURE_DIR)
    pkg = resolve_refs(pkg)
    executor = MockExecutor()
    execute_package(pkg, executor)

    # aristotle_contradicted was empty, should now have content
    reasoning = next(m for m in pkg.loaded_modules if m.name == "reasoning")
    ac = next(d for d in reasoning.declarations if d.name == "aristotle_contradicted")
    assert ac.content.startswith("[推理结果]")


def test_execute_calls_infer_action():
    pkg = load_package(FIXTURE_DIR)
    pkg = resolve_refs(pkg)
    executor = MockExecutor()
    execute_package(pkg, executor)

    # Should have called execute_infer for reductio_ad_absurdum and synthesize
    infer_calls = [c for c in executor.calls if c["type"] == "infer"]
    assert len(infer_calls) == 2


def test_execute_calls_lambda():
    pkg = load_package(FIXTURE_DIR)
    pkg = resolve_refs(pkg)
    executor = MockExecutor()
    execute_package(pkg, executor)

    # Should have called execute_lambda for confound_chain lambda
    lambda_calls = [c for c in executor.calls if c["type"] == "lambda"]
    assert len(lambda_calls) == 3  # confound_chain, inductive_support, next_steps


def test_execute_preserves_existing_content():
    pkg = load_package(FIXTURE_DIR)
    pkg = resolve_refs(pkg)
    executor = MockExecutor()
    execute_package(pkg, executor)

    # heavier_falls_faster already had content, should not be overwritten
    aristotle = next(m for m in pkg.loaded_modules if m.name == "aristotle")
    hff = next(d for d in aristotle.declarations if d.name == "heavier_falls_faster")
    assert "重的物体" in hff.content


def test_execute_chain_order():
    """Chains are executed in step order, earlier chains before later ones."""
    pkg = load_package(FIXTURE_DIR)
    pkg = resolve_refs(pkg)
    executor = MockExecutor()
    execute_package(pkg, executor)

    # vacuum_prediction (output of synthesis_chain) should have content
    # because refutation_chain and confound_chain ran first
    reasoning = next(m for m in pkg.loaded_modules if m.name == "reasoning")
    vp = next(d for d in reasoning.declarations if d.name == "vacuum_prediction")
    assert vp.content.startswith("[推理结果]")


# ── Inline tests (no galileo fixture) ─────────────────────────

from libs.dsl.models import (
    Claim,
    ChainExpr,
    Module,
    Package,
    StepRef,
    StepApply,
    StepLambda,
    Arg,
)


def test_execute_missing_action_skips():
    """A chain step that applies a nonexistent action is silently skipped."""
    claim_in = Claim(name="input_claim", content="some input", prior=0.9)
    claim_out = Claim(name="output_claim", content="", prior=0.5)
    chain = ChainExpr(
        name="bad_chain",
        steps=[
            StepRef(step=1, ref="input_claim"),
            StepApply(
                step=2,
                apply="nonexistent_action",
                args=[Arg(ref="input_claim", dependency="direct")],
            ),
            StepRef(step=3, ref="output_claim"),
        ],
    )
    mod = Module(
        type="reasoning_module",
        name="m",
        declarations=[claim_in, claim_out, chain],
        export=[],
    )
    pkg = Package(name="test_missing_action", modules=["m"])
    pkg.loaded_modules = [mod]

    executor = MockExecutor()
    execute_package(pkg, executor)

    # No crash; output claim stays empty since the action wasn't found
    assert claim_out.content == ""
    # Executor was never called
    assert len(executor.calls) == 0


def test_execute_preserves_nonempty_target():
    """If the output claim already has content, execution does NOT overwrite it."""
    claim_in = Claim(name="input_claim", content="existing input", prior=0.9)
    claim_out = Claim(name="output_claim", content="already filled", prior=0.5)
    chain = ChainExpr(
        name="preserve_chain",
        steps=[
            StepRef(step=1, ref="input_claim"),
            StepLambda(step=2, **{"lambda": "do something"}, prior=0.8),
            StepRef(step=3, ref="output_claim"),
        ],
    )
    mod = Module(
        type="reasoning_module",
        name="m",
        declarations=[claim_in, claim_out, chain],
        export=[],
    )
    pkg = Package(name="test_preserve", modules=["m"])
    pkg.loaded_modules = [mod]

    executor = MockExecutor()
    execute_package(pkg, executor)

    # Lambda was called (it always runs)
    assert len(executor.calls) == 1
    assert executor.calls[0]["type"] == "lambda"
    # But the output claim was not overwritten because it already had content
    assert claim_out.content == "already filled"
