"""Tests for gaia compile --readme."""

from gaia.cli.commands._readme import topo_layers


def test_topo_layers_linear_chain():
    """A → B → C should produce 3 layers."""
    ir = {
        "knowledges": [
            {"id": "ns:p::a", "label": "a", "type": "claim", "content": "A."},
            {"id": "ns:p::b", "label": "b", "type": "claim", "content": "B."},
            {"id": "ns:p::c", "label": "c", "type": "claim", "content": "C."},
        ],
        "strategies": [
            {"premises": ["ns:p::a"], "conclusion": "ns:p::b", "type": "noisy_and"},
            {"premises": ["ns:p::b"], "conclusion": "ns:p::c", "type": "noisy_and"},
        ],
        "operators": [],
    }
    layers = topo_layers(ir)
    assert layers["ns:p::a"] == 0
    assert layers["ns:p::b"] == 1
    assert layers["ns:p::c"] == 2


def test_topo_layers_independent_premises():
    """Multiple independent premises should all be layer 0."""
    ir = {
        "knowledges": [
            {"id": "ns:p::a", "label": "a", "type": "claim", "content": "A."},
            {"id": "ns:p::b", "label": "b", "type": "claim", "content": "B."},
            {"id": "ns:p::c", "label": "c", "type": "claim", "content": "C."},
        ],
        "strategies": [
            {"premises": ["ns:p::a", "ns:p::b"], "conclusion": "ns:p::c", "type": "noisy_and"},
        ],
        "operators": [],
    }
    layers = topo_layers(ir)
    assert layers["ns:p::a"] == 0
    assert layers["ns:p::b"] == 0
    assert layers["ns:p::c"] == 1


def test_topo_layers_settings_always_layer_0():
    ir = {
        "knowledges": [
            {"id": "ns:p::s", "label": "s", "type": "setting", "content": "S."},
            {"id": "ns:p::a", "label": "a", "type": "claim", "content": "A."},
        ],
        "strategies": [],
        "operators": [],
    }
    layers = topo_layers(ir)
    assert layers["ns:p::s"] == 0
    assert layers["ns:p::a"] == 0
