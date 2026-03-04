"""Data models for search engine results and filters."""

from pydantic import BaseModel

from libs.models import HyperEdge, Node


class NodeFilters(BaseModel):
    type: list[str] | None = None
    status: list[str] = ["active"]
    min_belief: float | None = None
    keywords: list[str] | None = None
    paper_id: str | None = None
    min_quality: float | None = None
    edge_type: list[str] | None = None


class EdgeFilters(BaseModel):
    type: list[str] | None = None
    verified: bool | None = None


class ScoredNode(BaseModel):
    node: Node
    score: float
    sources: list[str]  # ["vector", "bm25", "topology"]


class ScoredHyperEdge(BaseModel):
    edge: HyperEdge
    score: float
    sources: list[str]
