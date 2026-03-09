from libs.dsl.models import (
    Contradiction,
    Declaration,
    DECLARATION_TYPE_MAP,
    Equivalence,
    Relation,
)


def test_contradiction_model():
    c = Contradiction(
        name="test_contra",
        between=["claim_a", "claim_b"],
        prior=0.95,
    )
    assert c.type == "contradiction"
    assert c.between == ["claim_a", "claim_b"]
    assert c.prior == 0.95
    assert c.belief is None


def test_equivalence_model():
    e = Equivalence(
        name="test_equiv",
        between=["claim_x", "claim_y"],
        prior=0.90,
    )
    assert e.type == "equivalence"
    assert e.between == ["claim_x", "claim_y"]
    assert e.prior == 0.90
    assert e.belief is None


def test_relation_is_declaration():
    c = Contradiction(name="c", between=["a", "b"], prior=0.9)
    assert isinstance(c, Declaration)
    assert isinstance(c, Relation)


def test_relation_types_in_declaration_map():
    assert "contradiction" in DECLARATION_TYPE_MAP
    assert "equivalence" in DECLARATION_TYPE_MAP
    assert DECLARATION_TYPE_MAP["contradiction"] is Contradiction
    assert DECLARATION_TYPE_MAP["equivalence"] is Equivalence
