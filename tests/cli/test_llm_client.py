"""Tests for LLM client used in gaia review."""

from cli.llm_client import MockReviewClient, ReviewClient


def test_mock_client_returns_valid_review():
    """MockReviewClient should return a valid review dict for any chain."""
    client = MockReviewClient()
    chain_data = {
        "name": "drag_prediction_chain",
        "steps": [
            {"step": 2, "action": "deduce_drag_effect", "prior": 0.93,
             "args": [
                 {"ref": "heavier_falls_faster", "dependency": "direct"},
                 {"ref": "thought_experiment_env", "dependency": "indirect"},
             ]},
        ],
    }
    result = client.review_chain(chain_data)
    assert "chain" in result
    assert result["chain"] == "drag_prediction_chain"
    assert "steps" in result
    assert len(result["steps"]) >= 1
    step = result["steps"][0]
    assert "step" in step
    assert "assessment" in step
    assert "suggested_prior" in step


def test_mock_client_preserves_existing_priors():
    """MockReviewClient should echo back priors and dependency types."""
    client = MockReviewClient()
    chain_data = {
        "name": "test_chain",
        "steps": [
            {"step": 2, "action": "some_action", "prior": 0.85,
             "args": [{"ref": "claim_a", "dependency": "direct"}]},
        ],
    }
    result = client.review_chain(chain_data)
    step = result["steps"][0]
    assert step["suggested_prior"] == 0.85
    assert step["dependencies"][0]["suggested"] == "direct"


def test_review_client_interface():
    """ReviewClient should have a review_chain method."""
    client = ReviewClient(model="test")
    assert hasattr(client, "review_chain")
