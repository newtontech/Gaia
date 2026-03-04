"""EmbeddingOperator — generate embeddings for new nodes."""

from __future__ import annotations

from libs.embedding import EmbeddingModel, StubEmbeddingModel
from services.review_pipeline.base import Operator
from services.review_pipeline.context import PipelineContext

# Re-export for backward compatibility
__all__ = ["EmbeddingModel", "StubEmbeddingModel", "EmbeddingOperator"]


class EmbeddingOperator(Operator):
    """Generate embeddings for all new nodes in the context."""

    def __init__(self, model: EmbeddingModel) -> None:
        self._model = model

    async def execute(self, context: PipelineContext) -> PipelineContext:
        if not context.new_nodes:
            return context
        texts = [node.content for node in context.new_nodes]
        vectors = await self._model.embed(texts)
        for i, vec in enumerate(vectors):
            context.embeddings[i] = vec
        return context
