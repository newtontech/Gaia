"""Tests for Typst package loading via typst-py."""

from pathlib import Path

from libs.lang.typst_loader import load_typst_package

GALILEO_TYPST = Path("tests/fixtures/gaia_language_packages/galileo_falling_bodies_typst")


def test_load_typst_package_returns_graph_with_nodes():
    graph = load_typst_package(GALILEO_TYPST)
    assert "nodes" in graph
    assert len(graph["nodes"]) > 0


def test_load_typst_package_returns_graph_with_factors():
    graph = load_typst_package(GALILEO_TYPST)
    assert "factors" in graph
    assert len(graph["factors"]) > 0


def test_node_has_required_fields():
    graph = load_typst_package(GALILEO_TYPST)
    node = graph["nodes"][0]
    assert "name" in node
    assert "type" in node
    assert "content" in node


def test_node_content_is_plain_text():
    """Content should be flattened from Typst content tree to plain string."""
    graph = load_typst_package(GALILEO_TYPST)
    node = graph["nodes"][0]
    assert isinstance(node["content"], str)
    assert len(node["content"]) > 0


def test_factor_has_required_fields():
    graph = load_typst_package(GALILEO_TYPST)
    factors = [f for f in graph["factors"] if f["type"] == "reasoning"]
    assert len(factors) > 0
    factor = factors[0]
    assert "chain" in factor
    assert "premise" in factor
    assert "conclusion" in factor


def test_contradiction_factor_has_mutex_type():
    graph = load_typst_package(GALILEO_TYPST)
    mutex = [f for f in graph["factors"] if f["type"] == "mutex_constraint"]
    assert len(mutex) > 0


def test_refs_are_collected():
    graph = load_typst_package(GALILEO_TYPST)
    assert "refs" in graph
    ref_targets = [r["target"] for r in graph["refs"]]
    assert "aristotle.heavier_falls_faster" in ref_targets


def test_ctx_normalized_to_context():
    """The Typst library uses 'ctx' (context is a keyword), but Python output should use 'context'."""
    graph = load_typst_package(GALILEO_TYPST)
    for node in graph["nodes"]:
        assert "context" in node
        assert "ctx" not in node
    for factor in graph["factors"]:
        assert "context" in factor
        assert "ctx" not in factor


def test_expected_node_count():
    """Galileo fixture should have ~16 nodes."""
    graph = load_typst_package(GALILEO_TYPST)
    assert len(graph["nodes"]) >= 12  # at minimum


def test_expected_factor_count():
    """Galileo fixture should have ~9 factors."""
    graph = load_typst_package(GALILEO_TYPST)
    assert len(graph["factors"]) >= 6  # at minimum
