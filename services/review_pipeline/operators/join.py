"""CC/CP Join Operators — discover relationships between new and existing nodes.

Phase 1: StubJoinLLM returns empty results. Future phases plug in real LLM.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from services.review_pipeline.base import Operator
from services.review_pipeline.context import JoinTree, PipelineContext


class JoinLLM(ABC):
    """Abstract interface for LLM-based join discovery."""

    @abstractmethod
    async def find_joins(
        self,
        new_content: str,
        candidates: list[tuple[int, str]],
    ) -> list[JoinTree]:
        """Find relationships between new content and candidate nodes.

        Args:
            new_content: Content of the new node.
            candidates: List of (node_id, content) pairs to compare against.

        Returns:
            List of discovered join trees.
        """
        ...


class StubJoinLLM(JoinLLM):
    """Always returns empty results. For testing and Phase 1."""

    async def find_joins(
        self,
        new_content: str,
        candidates: list[tuple[int, str]],
    ) -> list[JoinTree]:
        return []


class CCJoinOperator(Operator):
    """Discover conclusion-conclusion relationships."""

    def __init__(self, join_llm: JoinLLM | None = None) -> None:
        self._llm = join_llm or StubJoinLLM()

    async def execute(self, context: PipelineContext) -> PipelineContext:
        if not context.nn_results:
            return context
        # In future: load candidate node contents, call LLM to find CC joins
        # Phase 1: stub returns empty
        for idx in context.nn_results:
            candidates = [(nid, "") for nid, _ in context.nn_results[idx]]
            trees = await self._llm.find_joins(
                context.new_nodes[idx].content if idx < len(context.new_nodes) else "",
                candidates,
            )
            for tree in trees:
                tree.source_node_index = idx
            context.cc_join_trees.extend(trees)
        return context


class CPJoinOperator(Operator):
    """Discover conclusion-premise relationships."""

    def __init__(self, join_llm: JoinLLM | None = None) -> None:
        self._llm = join_llm or StubJoinLLM()

    async def execute(self, context: PipelineContext) -> PipelineContext:
        if not context.nn_results:
            return context
        for idx in context.nn_results:
            candidates = [(nid, "") for nid, _ in context.nn_results[idx]]
            trees = await self._llm.find_joins(
                context.new_nodes[idx].content if idx < len(context.new_nodes) else "",
                candidates,
            )
            for tree in trees:
                tree.source_node_index = idx
            context.cp_join_trees.extend(trees)
        return context
