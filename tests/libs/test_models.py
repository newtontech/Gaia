# tests/libs/test_models.py
from libs.models import Node, HyperEdge, AddEdgeOp, ModifyEdgeOp, ModifyNodeOp, NewNode, NodeRef


def test_node_defaults():
    node = Node(id=1, type="paper-extract", content="test")
    assert node.status == "active"
    assert node.belief is None
    assert node.prior == 1.0
    assert node.keywords == []
    assert node.extra == {}
    assert node.title is None
    assert node.metadata == {}


def test_node_all_types():
    for t in ("paper-extract", "join", "deduction", "conjecture"):
        node = Node(id=1, type=t, content="x")
        assert node.type == t


def test_node_title():
    node = Node(id=1, type="paper-extract", content="test", title="My Title")
    assert node.title == "My Title"


def test_node_flexible_content():
    """content can be str, dict, or list."""
    n1 = Node(id=1, type="t", content="text")
    assert n1.content == "text"
    n2 = Node(id=2, type="t", content={"key": "val"})
    assert n2.content == {"key": "val"}
    n3 = Node(id=3, type="t", content=["a", "b"])
    assert n3.content == ["a", "b"]


def test_hyperedge_defaults():
    edge = HyperEdge(id=1, type="paper-extract", tail=[1], head=[2])
    assert edge.verified is False
    assert edge.probability is None
    assert edge.metadata == {}
    assert edge.extra == {}
    assert edge.reasoning == []


def test_hyperedge_types():
    for t in ("paper-extract", "join", "meet", "contradiction", "retraction"):
        edge = HyperEdge(id=1, type=t, tail=[1], head=[2])
        assert edge.type == t


def test_hyperedge_flexible_reasoning():
    """reasoning is list (untyped elements)."""
    e1 = HyperEdge(id=1, type="t", tail=[1], head=[2], reasoning=["step1", "step2"])
    assert e1.reasoning == ["step1", "step2"]
    e2 = HyperEdge(id=2, type="t", tail=[1], head=[2], reasoning=[{"title": "x", "content": "y"}])
    assert e2.reasoning[0]["title"] == "x"


def test_add_edge_op():
    op = AddEdgeOp(
        tail=[NewNode(content="premise")],
        head=[NodeRef(node_id=42)],
        type="meet",
        reasoning=["logical deduction"],
    )
    assert op.op == "add_edge"
    assert len(op.tail) == 1
    assert len(op.head) == 1


def test_modify_edge_op():
    op = ModifyEdgeOp(edge_id=456, changes={"status": "retracted"})
    assert op.op == "modify_edge"


def test_modify_node_op():
    op = ModifyNodeOp(node_id=789, changes={"content": "updated"})
    assert op.op == "modify_node"
