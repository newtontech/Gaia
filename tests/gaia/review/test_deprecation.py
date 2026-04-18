"""Tests that review sidecar APIs emit DeprecationWarning (since 0.4.2)."""

from __future__ import annotations

import warnings

import pytest

from gaia.lang.runtime import Knowledge, Strategy


@pytest.fixture()
def _dummy_knowledge():
    return Knowledge(content="test claim", type="claim")


@pytest.fixture()
def _dummy_strategy(_dummy_knowledge):
    return Strategy(type="support", premises=[_dummy_knowledge], conclusion=_dummy_knowledge)


def test_review_bundle_warns(_dummy_knowledge, _dummy_strategy):
    from gaia.review.models import ClaimReview, ReviewBundle

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        ReviewBundle(objects=[ClaimReview(subject=_dummy_knowledge, prior=0.5)])
        assert any(issubclass(x.category, DeprecationWarning) for x in w)
        assert "deprecated" in str(w[0].message).lower()


def test_review_claim_warns(_dummy_knowledge):
    from gaia.review.models import review_claim

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = review_claim(_dummy_knowledge, prior=0.9, justification="test")
        assert any(issubclass(x.category, DeprecationWarning) for x in w)
        assert result.prior == 0.9


def test_review_generated_claim_warns(_dummy_strategy):
    from gaia.review.models import review_generated_claim

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = review_generated_claim(_dummy_strategy, "alternative_explanation", prior=0.3)
        assert any(issubclass(x.category, DeprecationWarning) for x in w)
        assert result.role == "alternative_explanation"


def test_review_strategy_warns(_dummy_strategy):
    from gaia.review.models import review_strategy

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = review_strategy(_dummy_strategy, conditional_probability=0.8)
        assert any(issubclass(x.category, DeprecationWarning) for x in w)
        assert result.conditional_probability == 0.8
