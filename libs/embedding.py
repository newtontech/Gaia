"""Shared embedding model interface and stub implementation."""

from __future__ import annotations

import hashlib
import math
import struct
from abc import ABC, abstractmethod


class EmbeddingModel(ABC):
    """Abstract embedding model interface."""

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts."""
        ...


class StubEmbeddingModel(EmbeddingModel):
    """Deterministic stub: hashes text to produce reproducible vectors."""

    def __init__(self, dim: int = 1024) -> None:
        self._dim = dim

    async def embed(self, texts: list[str]) -> list[list[float]]:
        results = []
        for text in texts:
            digest = hashlib.sha256(text.encode()).digest()
            # Repeat digest bytes to fill dim floats
            raw = digest * ((self._dim * 4 // len(digest)) + 1)
            floats = list(struct.unpack(f"<{self._dim}f", raw[: self._dim * 4]))
            # Replace NaN/Inf with 0.0 then normalize
            floats = [0.0 if (math.isnan(f) or math.isinf(f)) else f for f in floats]
            mag = max(abs(f) for f in floats) or 1.0
            results.append([f / mag for f in floats])
        return results
