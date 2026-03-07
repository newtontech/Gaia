from libs.dsl.models import (
    Claim, Question, Setting,  # noqa: F401 — import-smoke-test
    InferAction, ToolCallAction,  # noqa: F401 — import-smoke-test
    ChainExpr, Ref,
    Module, Package,
    StepRef, StepApply, StepLambda,
    Param, Arg,
)


def test_claim_creation():
    c = Claim(name="test", content="some claim", prior=0.8)
    assert c.type == "claim"
    assert c.prior == 0.8


def test_infer_action_with_params():
    a = InferAction(
        name="reductio",
        params=[Param(name="hyp", type="claim")],
        return_type="claim",
        content="对 {hyp} 运用归谬法",
        prior=0.9,
    )
    assert a.type == "infer_action"
    assert len(a.params) == 1


def test_chain_expr_steps():
    chain = ChainExpr(
        name="my_chain",
        steps=[
            StepRef(step=1, ref="premise"),
            StepApply(
                step=2,
                apply="reductio",
                args=[Arg(ref="premise", dependency="direct")],
                prior=0.9,
            ),
            StepRef(step=3, ref="conclusion"),
        ],
    )
    assert chain.type == "chain_expr"
    assert len(chain.steps) == 3


def test_ref_declaration():
    r = Ref(name="premise", target="other_module.premise")
    assert r.type == "ref"
    assert r.target == "other_module.premise"


def test_module_with_declarations():
    m = Module(
        type="reasoning_module",
        name="reasoning",
        declarations=[
            Claim(name="c1", content="test"),
        ],
        export=["c1"],
    )
    assert m.type == "reasoning_module"
    assert len(m.declarations) == 1


def test_package():
    p = Package(
        name="test_pkg",
        version="1.0.0",
        modules_list=["mod_a", "mod_b"],
        export=["conclusion"],
    )
    assert p.name == "test_pkg"
    assert p.version == "1.0.0"


def test_prior_defaults_to_none():
    c = Claim(name="test", content="no prior")
    assert c.prior is None


def test_step_discriminator():
    """Steps are distinguished by which key is present: ref, apply, or lambda_."""
    s1 = StepRef(step=1, ref="x")
    s2 = StepApply(step=2, apply="f", args=[])
    s3 = StepLambda(step=3, lambda_="some reasoning")
    assert s1.ref == "x"
    assert s2.apply == "f"
    assert s3.lambda_ == "some reasoning"
