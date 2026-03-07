# tests/libs/dsl/test_executor.py
from pathlib import Path

from libs.dsl.executor import ActionExecutor, execute_package
from libs.dsl.loader import load_package
from libs.dsl.resolver import resolve_refs

FIXTURE_DIR = Path(__file__).parents[2] / "fixtures" / "dsl_packages" / "galileo_falling_bodies"


class MockExecutor(ActionExecutor):
    """Mock LLM executor that returns fixed responses."""

    def __init__(self):
        self.calls: list[dict] = []

    def execute_infer(self, content: str, args: dict[str, str]) -> str:
        self.calls.append({"type": "infer", "content": content, "args": args})
        # Substitute params into content as a simple mock
        result = content
        for k, v in args.items():
            result = result.replace(f"{{{k}}}", v)
        return f"[推理结果] {result}"

    def execute_lambda(self, content: str, input_text: str) -> str:
        self.calls.append({"type": "lambda", "content": content, "input": input_text})
        return f"[Lambda结果] {content}"


def test_execute_fills_empty_claims():
    pkg = load_package(FIXTURE_DIR)
    pkg = resolve_refs(pkg)
    executor = MockExecutor()
    execute_package(pkg, executor)

    # aristotle_contradicted was empty, should now have content
    reasoning = next(m for m in pkg.loaded_modules if m.name == "reasoning")
    ac = next(d for d in reasoning.declarations if d.name == "aristotle_contradicted")
    assert ac.content != ""


def test_execute_calls_infer_action():
    pkg = load_package(FIXTURE_DIR)
    pkg = resolve_refs(pkg)
    executor = MockExecutor()
    execute_package(pkg, executor)

    # Should have called execute_infer for reductio_ad_absurdum and synthesize
    infer_calls = [c for c in executor.calls if c["type"] == "infer"]
    assert len(infer_calls) >= 2


def test_execute_calls_lambda():
    pkg = load_package(FIXTURE_DIR)
    pkg = resolve_refs(pkg)
    executor = MockExecutor()
    execute_package(pkg, executor)

    # Should have called execute_lambda for confound_chain lambda
    lambda_calls = [c for c in executor.calls if c["type"] == "lambda"]
    assert len(lambda_calls) >= 1


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
    assert vp.content != ""
