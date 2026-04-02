from gaia.lang import Package, claim, question, setting
from gaia.lang.compiler import compile_package
from gaia.lang.operators import contradiction


def test_compile_produces_valid_ir():
    with Package("test_pkg", namespace="test") as pkg:
        setting("Background.")
        claim("Assertion.")
        question("Question?")
    ir = compile_package(pkg)
    assert ir["package"]["name"] == "test_pkg"
    assert ir["package"]["namespace"] == "test"
    assert len(ir["knowledge"]) == 3


def test_compile_knowledge_has_qid():
    with Package("test_pkg", namespace="test") as pkg:
        claim("A claim.")
    pkg.knowledge[0].label = "my_claim"
    ir = compile_package(pkg)
    k = ir["knowledge"][0]
    assert k["id"] == "test:test_pkg::my_claim"
    assert k["type"] == "claim"
    assert k["content"] == "A claim."
    assert k["content_hash"] is not None


def test_compile_strategy():
    with Package("test_pkg", namespace="test") as pkg:
        a = claim("A.")
        claim("B.", given=[a])
    pkg.knowledge[0].label = "a"
    pkg.knowledge[1].label = "b"
    ir = compile_package(pkg)
    assert len(ir["strategies"]) == 1
    s = ir["strategies"][0]
    assert s["type"] == "noisy_and"
    assert s["strategy_id"].startswith("lcs_")


def test_compile_operator():
    with Package("test_pkg", namespace="test") as pkg:
        a = claim("A.")
        b = claim("B.")
        contradiction(a, b, reason="Conflict")
    pkg.knowledge[0].label = "a"
    pkg.knowledge[1].label = "b"
    pkg.knowledge[2].label = "contra"
    ir = compile_package(pkg)
    assert len(ir["operators"]) == 1
    op = ir["operators"][0]
    assert op["operator"] == "contradiction"
    assert op["operator_id"].startswith("lco_")


def test_compile_ir_hash_deterministic():
    def build():
        with Package("test_pkg", namespace="test") as pkg:
            a = claim("A.")
            claim("B.", given=[a])
        pkg.knowledge[0].label = "a"
        pkg.knowledge[1].label = "b"
        return compile_package(pkg)

    ir1 = build()
    ir2 = build()
    assert ir1["ir_hash"] == ir2["ir_hash"]


def test_compile_input_claims():
    with Package("test_pkg", namespace="test") as pkg:
        a = claim("Input claim.")
        claim("Derived.", given=[a])
    pkg.knowledge[0].label = "a"
    pkg.knowledge[1].label = "b"
    ir = compile_package(pkg)
    inputs = [k for k in ir["knowledge"] if k.get("is_input")]
    assert len(inputs) == 1
    assert inputs[0]["label"] == "a"
