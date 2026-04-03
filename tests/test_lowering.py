"""Tests for gaia.bp.lowering."""

from __future__ import annotations

import pytest

from gaia.bp import FactorType, lower_local_graph, lower_operator
from gaia.bp.factor_graph import FactorGraph
from gaia.bp.exact import exact_inference
from gaia.ir import Knowledge, Operator, Strategy, LocalCanonicalGraph

NS, PKG = "github", "lowertest"


def _lg(**kwargs) -> LocalCanonicalGraph:
    kwargs.setdefault("namespace", NS)
    kwargs.setdefault("package_name", PKG)
    return LocalCanonicalGraph(**kwargs)


def test_lower_operator_helper():
    fg = FactorGraph()
    fg.add_variable("a", 0.5)
    fg.add_variable("b", 0.5)
    op = Operator(operator="implication", variables=["a"], conclusion="b")
    lower_operator(fg, op, "f1")
    assert len(fg.factors) == 1
    assert fg.factors[0].factor_type == FactorType.IMPLICATION


def test_equivalence_operator_round_trip():
    g = _lg(
        knowledges=[
            Knowledge(id="github:lowertest::a", type="claim", content="A"),
            Knowledge(id="github:lowertest::b", type="claim", content="B"),
            Knowledge(id="github:lowertest::h", type="claim", content="H"),
        ],
        operators=[
            Operator(
                operator="equivalence",
                variables=["github:lowertest::a", "github:lowertest::b"],
                conclusion="github:lowertest::h",
            ),
        ],
    )
    fg = lower_local_graph(
        g,
        node_priors={
            "github:lowertest::a": 0.7,
            "github:lowertest::b": 0.4,
            "github:lowertest::h": 0.95,
        },
    )
    assert not fg.validate()
    beliefs, _ = exact_inference(fg)
    assert all(0 < beliefs[v] < 1 for v in beliefs)


def test_contradiction_default_prior_near_one():
    """Relation-type operator conclusion defaults to ~1.0 (constraint active)."""
    from gaia.bp.factor_graph import CROMWELL_EPS

    g = _lg(
        knowledges=[
            Knowledge(id="github:lowertest::x", type="claim", content="X"),
            Knowledge(id="github:lowertest::y", type="claim", content="Y"),
            Knowledge(id="github:lowertest::r", type="claim", content="R"),
        ],
        operators=[
            Operator(
                operator="contradiction",
                variables=["github:lowertest::x", "github:lowertest::y"],
                conclusion="github:lowertest::r",
            ),
        ],
    )
    fg = lower_local_graph(g)
    assert fg.variables["github:lowertest::r"] == pytest.approx(1.0 - CROMWELL_EPS)


def test_contradiction_actually_constrains():
    """With prior ~1.0 on helper, CONTRADICTION suppresses joint X=Y=1."""
    g = _lg(
        knowledges=[
            Knowledge(id="github:lowertest::x", type="claim", content="X"),
            Knowledge(id="github:lowertest::y", type="claim", content="Y"),
            Knowledge(id="github:lowertest::r", type="claim", content="R"),
        ],
        operators=[
            Operator(
                operator="contradiction",
                variables=["github:lowertest::x", "github:lowertest::y"],
                conclusion="github:lowertest::r",
            ),
        ],
    )
    fg = lower_local_graph(
        g,
        node_priors={"github:lowertest::x": 0.8, "github:lowertest::y": 0.8},
    )
    beliefs, _ = exact_inference(fg)
    assert beliefs["github:lowertest::x"] < 0.8 or beliefs["github:lowertest::y"] < 0.8


def test_noisy_and_strategy_lowering():
    s = Strategy(
        scope="local",
        type="noisy_and",
        premises=["github:lowertest::p1", "github:lowertest::p2"],
        conclusion="github:lowertest::c",
    )
    g = _lg(
        knowledges=[
            Knowledge(id="github:lowertest::p1", type="claim", content="P1"),
            Knowledge(id="github:lowertest::p2", type="claim", content="P2"),
            Knowledge(id="github:lowertest::c", type="claim", content="C"),
        ],
        strategies=[s],
    )
    fg = lower_local_graph(
        g,
        strategy_conditional_params={s.strategy_id: [0.85]},
    )
    fts = [f.factor_type for f in fg.factors]
    assert FactorType.CONJUNCTION in fts
    assert FactorType.SOFT_ENTAILMENT in fts


def test_infer_conditional_lowering():
    s = Strategy(
        scope="local",
        type="infer",
        premises=["github:lowertest::x"],
        conclusion="github:lowertest::y",
    )
    g = _lg(
        knowledges=[
            Knowledge(id="github:lowertest::x", type="claim", content="X"),
            Knowledge(id="github:lowertest::y", type="claim", content="Y"),
        ],
        strategies=[s],
    )
    cpt = [0.3, 0.9]
    fg = lower_local_graph(g, strategy_conditional_params={s.strategy_id: cpt})
    cond = [f for f in fg.factors if f.factor_type == FactorType.CONDITIONAL]
    assert len(cond) == 1
    assert cond[0].cpt == tuple(cpt)


def test_formal_strategy_expand_implication():
    from gaia.ir.strategy import FormalExpr, FormalStrategy

    fs = FormalStrategy(
        scope="local",
        type="deduction",
        premises=["github:lowertest::p"],
        conclusion="github:lowertest::c",
        formal_expr=FormalExpr(
            operators=[
                Operator(
                    operator="implication",
                    variables=["github:lowertest::p"],
                    conclusion="github:lowertest::c",
                ),
            ],
        ),
    )
    g = _lg(
        knowledges=[
            Knowledge(id="github:lowertest::p", type="claim", content="P"),
            Knowledge(id="github:lowertest::c", type="claim", content="C"),
        ],
        strategies=[fs],
    )
    fg = lower_local_graph(g, expand_formal=True)
    assert any(f.factor_type == FactorType.IMPLICATION for f in fg.factors)


def test_formal_fold_not_implemented():
    from gaia.ir.strategy import FormalExpr, FormalStrategy

    fs = FormalStrategy(
        scope="local",
        type="deduction",
        premises=["github:lowertest::p"],
        conclusion="github:lowertest::c",
        formal_expr=FormalExpr(
            operators=[
                Operator(
                    operator="implication",
                    variables=["github:lowertest::p"],
                    conclusion="github:lowertest::c",
                ),
            ],
        ),
    )
    g = _lg(
        knowledges=[
            Knowledge(id="github:lowertest::p", type="claim", content="P"),
            Knowledge(id="github:lowertest::c", type="claim", content="C"),
        ],
        strategies=[fs],
    )
    with pytest.raises(NotImplementedError):
        lower_local_graph(g, expand_formal=False)


# ---------------------------------------------------------------------------
# Named leaf strategy auto-formalization (07-lowering.md §4.1 / §4.3)
# ---------------------------------------------------------------------------


def test_deduction_leaf_strategy_auto_formalizes():
    """Plain Strategy(type=deduction) is auto-formalized to CONJUNCTION + IMPLICATION."""
    s = Strategy(
        scope="local",
        type="deduction",
        premises=["github:lowertest::a", "github:lowertest::b"],
        conclusion="github:lowertest::c",
    )
    g = _lg(
        knowledges=[
            Knowledge(id="github:lowertest::a", type="claim", content="A"),
            Knowledge(id="github:lowertest::b", type="claim", content="B"),
            Knowledge(id="github:lowertest::c", type="claim", content="C"),
        ],
        strategies=[s],
    )
    fg = lower_local_graph(g)
    assert not fg.validate()
    ftypes = {f.factor_type for f in fg.factors}
    assert FactorType.CONJUNCTION in ftypes
    assert FactorType.IMPLICATION in ftypes


def test_analogy_leaf_strategy_auto_formalizes():
    """Plain Strategy(type=analogy) produces CONJUNCTION + IMPLICATION factors."""
    s = Strategy(
        scope="local",
        type="analogy",
        premises=["github:lowertest::src", "github:lowertest::bridge"],
        conclusion="github:lowertest::tgt",
    )
    g = _lg(
        knowledges=[
            Knowledge(id="github:lowertest::src", type="claim", content="SourceLaw"),
            Knowledge(id="github:lowertest::bridge", type="claim", content="BridgeClaim"),
            Knowledge(id="github:lowertest::tgt", type="claim", content="Target"),
        ],
        strategies=[s],
    )
    fg = lower_local_graph(g)
    assert not fg.validate()
    ftypes = {f.factor_type for f in fg.factors}
    assert FactorType.CONJUNCTION in ftypes
    assert FactorType.IMPLICATION in ftypes


def test_extrapolation_leaf_strategy_auto_formalizes():
    """Plain Strategy(type=extrapolation) produces CONJUNCTION + IMPLICATION factors."""
    s = Strategy(
        scope="local",
        type="extrapolation",
        premises=["github:lowertest::law", "github:lowertest::cont"],
        conclusion="github:lowertest::ext",
    )
    g = _lg(
        knowledges=[
            Knowledge(id="github:lowertest::law", type="claim", content="KnownLaw"),
            Knowledge(id="github:lowertest::cont", type="claim", content="ContinuityClaim"),
            Knowledge(id="github:lowertest::ext", type="claim", content="Extended"),
        ],
        strategies=[s],
    )
    fg = lower_local_graph(g)
    assert not fg.validate()
    ftypes = {f.factor_type for f in fg.factors}
    assert FactorType.CONJUNCTION in ftypes
    assert FactorType.IMPLICATION in ftypes


def test_abduction_leaf_strategy_generates_interface_claim():
    """Plain Strategy(type=abduction) generates AlternativeExplanationForObs interface claim."""
    s = Strategy(
        scope="local",
        type="abduction",
        premises=["github:lowertest::obs"],
        conclusion="github:lowertest::hyp",
    )
    g = _lg(
        knowledges=[
            Knowledge(id="github:lowertest::obs", type="claim", content="Obs"),
            Knowledge(id="github:lowertest::hyp", type="claim", content="Hypothesis"),
        ],
        strategies=[s],
    )
    fg = lower_local_graph(g)
    assert not fg.validate()
    ftypes = {f.factor_type for f in fg.factors}
    # abduction skeleton: disjunction(H, Alt -> ExplainUnion) + equivalence(ExplainUnion, Obs -> EqH)
    assert FactorType.DISJUNCTION in ftypes
    assert FactorType.EQUIVALENCE in ftypes
    # The auto-generated AlternativeExplanationForObs must appear as a variable
    alt_vars = [v for v in fg.variables if "alternative_explanation" in v]
    assert len(alt_vars) == 1


def test_mathematical_induction_leaf_strategy_auto_formalizes():
    """Plain Strategy(type=mathematical_induction) produces CONJUNCTION + IMPLICATION."""
    s = Strategy(
        scope="local",
        type="mathematical_induction",
        premises=["github:lowertest::base", "github:lowertest::step"],
        conclusion="github:lowertest::law",
    )
    g = _lg(
        knowledges=[
            Knowledge(id="github:lowertest::base", type="claim", content="Base"),
            Knowledge(id="github:lowertest::step", type="claim", content="Step"),
            Knowledge(id="github:lowertest::law", type="claim", content="Law"),
        ],
        strategies=[s],
    )
    fg = lower_local_graph(g)
    assert not fg.validate()
    ftypes = {f.factor_type for f in fg.factors}
    assert FactorType.CONJUNCTION in ftypes
    assert FactorType.IMPLICATION in ftypes


def test_deferred_leaf_strategy_raises():
    """Deferred leaf strategy types (reductio) raise NotImplementedError."""
    s = Strategy(
        scope="local",
        type="reductio",
        premises=["github:lowertest::p"],
        conclusion="github:lowertest::c",
    )
    g = _lg(
        knowledges=[
            Knowledge(id="github:lowertest::p", type="claim", content="P"),
            Knowledge(id="github:lowertest::c", type="claim", content="C"),
        ],
        strategies=[s],
    )
    with pytest.raises(NotImplementedError, match="deferred"):
        lower_local_graph(g)


def test_named_leaf_node_priors_respected():
    """User-supplied node_priors for auto-generated claims are applied via _ensure_claim_var."""
    s = Strategy(
        scope="local",
        type="abduction",
        premises=["github:lowertest::obs2"],
        conclusion="github:lowertest::hyp2",
    )
    g = _lg(
        knowledges=[
            Knowledge(id="github:lowertest::obs2", type="claim", content="Obs2"),
            Knowledge(id="github:lowertest::hyp2", type="claim", content="Hyp2"),
        ],
        strategies=[s],
    )
    # First pass: discover the auto-generated alt-explanation variable ID
    fg0 = lower_local_graph(g)
    alt_id = [v for v in fg0.variables if "alternative_explanation" in v][0]

    # Second pass: supply a custom prior for the auto-generated claim
    fg1 = lower_local_graph(g, node_priors={alt_id: 0.1})
    assert fg1.variables[alt_id] == pytest.approx(0.1)
