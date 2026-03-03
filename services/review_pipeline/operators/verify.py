"""Verify and Refine operators for join trees.

Phase 1: StubVerifyLLM auto-verifies all trees.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from services.review_pipeline.base import Operator
from services.review_pipeline.context import JoinTree, PipelineContext


class VerifyLLM(ABC):
    @abstractmethod
    async def verify(self, trees: list[JoinTree]) -> list[JoinTree]:
        """Verify join trees, setting verified=True/False on each."""
        ...


class StubVerifyLLM(VerifyLLM):
    """Auto-verifies all trees. For testing and Phase 1."""

    async def verify(self, trees: list[JoinTree]) -> list[JoinTree]:
        for tree in trees:
            tree.verified = True
        return trees


class JoinTreeVerifyOperator(Operator):
    """First-pass verification of discovered join trees."""

    def __init__(self, verify_llm: VerifyLLM | None = None) -> None:
        self._llm = verify_llm or StubVerifyLLM()

    async def execute(self, context: PipelineContext) -> PipelineContext:
        all_trees = context.cc_join_trees + context.cp_join_trees
        if all_trees:
            await self._llm.verify(all_trees)
        return context


class RefineOperator(Operator):
    """Refine join trees — Phase 1: pass-through."""

    async def execute(self, context: PipelineContext) -> PipelineContext:
        return context


class VerifyAgainOperator(Operator):
    """Second verification pass. Collects all verified trees into verified_trees."""

    def __init__(self, verify_llm: VerifyLLM | None = None) -> None:
        self._llm = verify_llm or StubVerifyLLM()

    async def execute(self, context: PipelineContext) -> PipelineContext:
        all_trees = context.cc_join_trees + context.cp_join_trees
        if all_trees:
            await self._llm.verify(all_trees)
        context.verified_trees = [t for t in all_trees if t.verified]
        return context
