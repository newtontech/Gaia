"""Content similarity for global canonicalization."""

from __future__ import annotations

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .models import GlobalCanonicalNode

# Types that are package-local relations — never match across packages
_RELATION_TYPES = {"contradiction", "equivalence"}
# Types that require kind match
_KIND_REQUIRED_TYPES = {"question", "action"}


def compute_similarity(text_a: str, text_b: str) -> float:
    """Compute TF-IDF cosine similarity between two texts."""
    if not text_a.strip() or not text_b.strip():
        return 0.0
    vectorizer = TfidfVectorizer()
    tfidf = vectorizer.fit_transform([text_a, text_b])
    sim = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
    return float(sim)


def find_best_match(
    content: str,
    knowledge_type: str,
    kind: str | None,
    candidates: list[GlobalCanonicalNode],
    threshold: float = 0.90,
) -> tuple[str, float] | None:
    """Find the best matching GlobalCanonicalNode for a local node.

    Returns (global_canonical_id, similarity_score) or None if no match.
    """
    if knowledge_type in _RELATION_TYPES:
        return None

    if not candidates or not content.strip():
        return None

    best_id: str | None = None
    best_score: float = 0.0

    for candidate in candidates:
        if candidate.knowledge_type != knowledge_type:
            continue
        if knowledge_type in _KIND_REQUIRED_TYPES and candidate.kind != kind:
            continue

        score = compute_similarity(content, candidate.representative_content)
        if score > best_score:
            best_score = score
            best_id = candidate.global_canonical_id

    if best_id is not None and best_score >= threshold:
        return (best_id, best_score)
    return None
