"""Tests for proof state analysis."""

from pathlib import Path

from libs.lang.proof_state import analyze_proof_state
from libs.lang.typst_loader import load_typst_package

GALILEO_V3 = (
    Path(__file__).parent.parent.parent
    / "fixtures"
    / "gaia_language_packages"
    / "galileo_falling_bodies_v3"
)


def test_established_claims():
    graph = load_typst_package(GALILEO_V3)
    state = analyze_proof_state(graph)
    established = {d["name"] for d in state["established"]}
    assert "composite_is_slower" in established
    assert "composite_is_faster" in established
    assert "air_resistance_is_confound" in established
    assert "vacuum_prediction" in established


def test_claim_relation_is_established():
    """claim_relation nodes (e.g. contradiction) should be established, not holes."""
    graph = load_typst_package(GALILEO_V3)
    state = analyze_proof_state(graph)
    established = {d["name"] for d in state["established"]}
    assert "tied_balls_contradiction" in established


def test_claim_relation_not_hole():
    """claim_relation nodes should never appear as holes."""
    graph = load_typst_package(GALILEO_V3)
    state = analyze_proof_state(graph)
    hole_names = {d["name"] for d in state["holes"]}
    assert "tied_balls_contradiction" not in hole_names


def test_heavier_falls_faster_is_hole():
    """A claim used as premise without a factor concluding it should be a hole."""
    graph = load_typst_package(GALILEO_V3)
    state = analyze_proof_state(graph)
    hole_names = {d["name"] for d in state["holes"]}
    assert "heavier_falls_faster" in hole_names


def test_axioms_include_settings():
    graph = load_typst_package(GALILEO_V3)
    state = analyze_proof_state(graph)
    axiom_names = {d["name"] for d in state["axioms"]}
    assert "thought_experiment_env" in axiom_names
    assert "vacuum_env" in axiom_names


def test_axioms_include_observations():
    graph = load_typst_package(GALILEO_V3)
    state = analyze_proof_state(graph)
    axiom_names = {d["name"] for d in state["axioms"]}
    assert "medium_density_observation" in axiom_names
    assert "inclined_plane_observation" in axiom_names


def test_questions_detected():
    graph = load_typst_package(GALILEO_V3)
    state = analyze_proof_state(graph)
    question_names = {d["name"] for d in state["questions"]}
    assert "main_question" in question_names
    assert "follow_up_question" in question_names


def test_no_false_holes():
    """Settings and observations should never be holes."""
    graph = load_typst_package(GALILEO_V3)
    state = analyze_proof_state(graph)
    hole_names = {d["name"] for d in state["holes"]}
    assert "thought_experiment_env" not in hole_names
    assert "medium_density_observation" not in hole_names


def test_constraint_between_members_are_used_as_premise():
    """Claims used only as between members of a constraint should be detected as holes."""
    graph = {
        "nodes": [
            {"name": "A", "type": "claim"},
            {"name": "B", "type": "claim"},
            {"name": "rel", "type": "contradiction"},
        ],
        "factors": [],
        "constraints": [
            {"name": "rel", "type": "contradiction", "between": ["A", "B"]},
        ],
    }
    state = analyze_proof_state(graph)
    hole_names = {d["name"] for d in state["holes"]}
    assert "A" in hole_names
    assert "B" in hole_names
    # The relation itself should be established, not a hole
    established_names = {d["name"] for d in state["established"]}
    assert "rel" in established_names


def test_standalone_claims_reported():
    """Claims not proven and not referenced should appear in standalone."""
    graph = {
        "nodes": [
            {"name": "orphan", "type": "claim"},
        ],
        "factors": [],
        "constraints": [],
    }
    state = analyze_proof_state(graph)
    standalone_names = {d["name"] for d in state["standalone"]}
    assert "orphan" in standalone_names
    assert len(state["holes"]) == 0


def test_proof_state_format_string():
    graph = load_typst_package(GALILEO_V3)
    state = analyze_proof_state(graph)
    report = state["report"]
    assert "established" in report.lower() or "\u2713" in report
    assert "axiom" in report.lower() or "\u25cb" in report
