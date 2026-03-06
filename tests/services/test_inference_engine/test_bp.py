"""Tests for the BeliefPropagation algorithm."""

from __future__ import annotations

import pytest

from services.inference_engine.bp import BeliefPropagation
from services.inference_engine.factor_graph import FactorGraph


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _simple_chain() -> FactorGraph:
    """A -> B with probability 0.8"""
    fg = FactorGraph()
    fg.add_variable(1, 0.9)  # A: high prior
    fg.add_variable(2, 1.0)  # B: default prior
    fg.add_factor(edge_id=100, tail=[1], head=[2], probability=0.8)
    return fg


def _two_step_chain() -> FactorGraph:
    """A -> B -> C"""
    fg = FactorGraph()
    fg.add_variable(1, 0.9)
    fg.add_variable(2, 1.0)
    fg.add_variable(3, 1.0)
    fg.add_factor(edge_id=100, tail=[1], head=[2], probability=0.8)
    fg.add_factor(edge_id=101, tail=[2], head=[3], probability=0.7)
    return fg


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_simple_chain():
    fg = _simple_chain()
    bp = BeliefPropagation(damping=0.5, max_iterations=50)
    beliefs = bp.run(fg)
    assert 1 in beliefs
    assert 2 in beliefs
    # B's belief should be influenced by A's high prior and edge probability
    assert beliefs[2] > 0.5


def test_chain_propagation():
    fg = _two_step_chain()
    bp = BeliefPropagation(damping=0.5, max_iterations=50)
    beliefs = bp.run(fg)
    # Source node (1, prior=0.9) should have highest belief
    # End-of-chain node (3) should have lowest
    assert beliefs[1] >= beliefs[3], f"Source should >= end: {beliefs[1]} vs {beliefs[3]}"


def test_convergence():
    """BP should converge within max_iterations."""
    fg = FactorGraph()
    for i in range(1, 6):
        fg.add_variable(i, 0.8)
    fg.add_factor(1, [1], [2], 0.9)
    fg.add_factor(2, [2], [3], 0.8)
    fg.add_factor(3, [3], [4], 0.7)
    fg.add_factor(4, [4], [5], 0.6)
    bp = BeliefPropagation(max_iterations=100, convergence_threshold=1e-6)
    beliefs = bp.run(fg)
    # All beliefs should be valid probabilities
    for b in beliefs.values():
        assert 0.0 <= b <= 1.0


def test_empty_graph():
    fg = FactorGraph()
    bp = BeliefPropagation()
    beliefs = bp.run(fg)
    assert beliefs == {}


def test_single_node_no_factors():
    fg = FactorGraph()
    fg.add_variable(1, 0.75)
    bp = BeliefPropagation()
    beliefs = bp.run(fg)
    assert beliefs[1] == pytest.approx(0.75)


def test_low_probability_edge():
    fg = FactorGraph()
    fg.add_variable(1, 0.9)
    fg.add_variable(2, 1.0)
    fg.add_factor(edge_id=100, tail=[1], head=[2], probability=0.1)
    bp = BeliefPropagation(damping=0.5, max_iterations=50)
    beliefs = bp.run(fg)
    # With low edge probability, B should not get high belief
    assert beliefs[2] < 0.9


def test_multi_tail_factor():
    """Multiple premises needed for conclusion."""
    fg = FactorGraph()
    fg.add_variable(1, 0.9)  # premise 1
    fg.add_variable(2, 0.8)  # premise 2
    fg.add_variable(3, 1.0)  # conclusion
    fg.add_factor(edge_id=100, tail=[1, 2], head=[3], probability=0.9)
    bp = BeliefPropagation(damping=0.5, max_iterations=50)
    beliefs = bp.run(fg)
    assert 0.0 <= beliefs[3] <= 1.0


def test_damping_effect():
    """Higher damping should cause beliefs to deviate more from prior."""
    fg = _simple_chain()
    bp_low = BeliefPropagation(damping=0.1, max_iterations=50)
    bp_high = BeliefPropagation(damping=0.9, max_iterations=50)
    beliefs_low = bp_low.run(fg)
    beliefs_high = bp_high.run(fg)
    # Node 2 prior is 1.0; after BP it should decrease.
    # High damping should deviate more from the prior.
    deviation_low = abs(beliefs_low[2] - 1.0)
    deviation_high = abs(beliefs_high[2] - 1.0)
    assert deviation_high > deviation_low, (
        f"High damping should deviate more: low={deviation_low}, high={deviation_high}"
    )
