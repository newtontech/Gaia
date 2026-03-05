"""CC/CP Abstraction Operators — discover relationships between new and existing nodes."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from libs.storage import StorageManager
from services.review_pipeline.base import Operator
from services.review_pipeline.context import AbstractionTree, PipelineContext
from services.review_pipeline.llm_client import LLMClient
from services.review_pipeline.xml_parser import parse_abstraction_output

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def _load_prompt(name: str) -> str:
    return (_PROMPTS_DIR / f"{name}.md").read_text()


class AbstractionLLM(ABC):
    """Abstract interface for LLM-based abstraction discovery."""

    @abstractmethod
    async def find_abstractions(
        self,
        new_content: str,
        candidates: list[tuple[int, str]],
    ) -> list[AbstractionTree]:
        """Find relationships between new content and candidate nodes.

        Args:
            new_content: Content of the new node.
            candidates: List of (node_id, content) pairs to compare against.

        Returns:
            List of discovered abstraction trees.
        """
        ...


class StubAbstractionLLM(AbstractionLLM):
    """Always returns empty results. For testing and Phase 1."""

    async def find_abstractions(
        self,
        new_content: str,
        candidates: list[tuple[int, str]],
    ) -> list[AbstractionTree]:
        return []


class LiteLLMAbstractionClient(AbstractionLLM):
    """Real abstraction discovery via asymmetric abstraction prompt + litellm."""

    def __init__(self, llm_client: LLMClient) -> None:
        self._llm = llm_client
        self._prompt = _load_prompt("abstraction_asymmetric")

    async def find_abstractions(
        self,
        new_content: str,
        candidates: list[tuple[int, str]],
    ) -> list[AbstractionTree]:
        if not candidates:
            return []

        # Build user prompt: anchor = new node, candidates = existing nodes
        lines = [
            "## Anchor (new proposition):",
            "ID: 0",
            f"Content: {new_content}",
            "",
            "## Candidates:",
        ]
        for node_id, content in candidates:
            lines.append(f"### Proposition {node_id}:")
            lines.append(f"Content: {content}")
            lines.append("")

        user_input = "\n".join(lines)
        output = await self._llm.complete(self._prompt, user_input)
        trees = parse_abstraction_output(output, anchor_index=0)

        # Attach content so downstream verify has the actual text
        candidate_map = {nid: content for nid, content in candidates}
        for tree in trees:
            tree.source_content = new_content
            tree.target_content = candidate_map.get(tree.target_node_id, "")
        return trees


class CCAbstractionOperator(Operator):
    """Discover conclusion-conclusion relationships."""

    def __init__(
        self,
        abstraction_llm: AbstractionLLM | None = None,
        storage: StorageManager | None = None,
    ) -> None:
        self._llm = abstraction_llm or StubAbstractionLLM()
        self._storage = storage

    async def _load_content(self, node_id: int) -> str:
        if self._storage is None:
            return ""
        node = await self._storage.lance.load_node(node_id)
        if node is None:
            return ""
        return node.content if hasattr(node, "content") else ""

    async def execute(self, context: PipelineContext) -> PipelineContext:
        if not context.nn_results:
            return context
        for idx in context.nn_results:
            candidates: list[tuple[int, str]] = []
            for nid, _ in context.nn_results[idx]:
                content = await self._load_content(nid)
                candidates.append((nid, content))
            trees = await self._llm.find_abstractions(
                context.new_nodes[idx].content if idx < len(context.new_nodes) else "",
                candidates,
            )
            for tree in trees:
                tree.source_node_index = idx
            context.cc_abstraction_trees.extend(trees)
        return context


class CPAbstractionOperator(Operator):
    """Discover conclusion-premise relationships."""

    def __init__(
        self,
        abstraction_llm: AbstractionLLM | None = None,
        storage: StorageManager | None = None,
    ) -> None:
        self._llm = abstraction_llm or StubAbstractionLLM()
        self._storage = storage

    async def _load_content(self, node_id: int) -> str:
        if self._storage is None:
            return ""
        node = await self._storage.lance.load_node(node_id)
        if node is None:
            return ""
        return node.content if hasattr(node, "content") else ""

    async def execute(self, context: PipelineContext) -> PipelineContext:
        if not context.nn_results:
            return context
        for idx in context.nn_results:
            candidates: list[tuple[int, str]] = []
            for nid, _ in context.nn_results[idx]:
                content = await self._load_content(nid)
                candidates.append((nid, content))
            trees = await self._llm.find_abstractions(
                context.new_nodes[idx].content if idx < len(context.new_nodes) else "",
                candidates,
            )
            for tree in trees:
                tree.source_node_index = idx
            context.cp_abstraction_trees.extend(trees)
        return context
