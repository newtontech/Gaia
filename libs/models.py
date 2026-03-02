"""Shared data models for Gaia — Node, HyperEdge, and commit operations."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


# ── Core Graph Entities ──


class Node(BaseModel):
    id: int
    type: str  # paper-extract | join | deduction | conjecture | ...
    subtype: str | None = None
    title: str | None = None
    content: str | dict | list
    keywords: list[str] = []
    prior: float = 1.0
    belief: float | None = None
    status: Literal["active", "deleted"] = "active"
    metadata: dict = {}
    extra: dict = {}
    created_at: datetime | None = None


class HyperEdge(BaseModel):
    id: int
    type: str  # paper-extract | join | meet | contradiction | retraction
    subtype: str | None = None
    tail: list[int]
    head: list[int]
    probability: float | None = None
    verified: bool = False
    reasoning: list = []
    metadata: dict = {}
    extra: dict = {}
    created_at: datetime | None = None


# ── Commit Operations ──


class NewNode(BaseModel):
    content: str | dict | list
    keywords: list[str] = []
    extra: dict = {}


class NodeRef(BaseModel):
    node_id: int


class AddEdgeOp(BaseModel):
    op: Literal["add_edge"] = "add_edge"
    tail: list[NewNode | NodeRef]
    head: list[NewNode | NodeRef]
    type: str
    reasoning: list


class ModifyEdgeOp(BaseModel):
    op: Literal["modify_edge"] = "modify_edge"
    edge_id: int
    changes: dict


class ModifyNodeOp(BaseModel):
    op: Literal["modify_node"] = "modify_node"
    node_id: int
    changes: dict
