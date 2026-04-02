"""Gaia Lang v5 — core runtime objects for Python DSL."""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any


_current_package: ContextVar[Package | None] = ContextVar("_current_package", default=None)


@dataclass
class Knowledge:
    """A knowledge declaration (claim, setting, or question)."""

    content: str
    type: str  # "claim" | "setting" | "question"
    background: list[Knowledge] = field(default_factory=list)
    parameters: list[dict] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    label: str | None = None
    strategy: Strategy | None = None

    def __post_init__(self):
        pkg = _current_package.get()
        if pkg is not None:
            pkg._register_knowledge(self)


@dataclass
class Strategy:
    """A reasoning declaration."""

    type: str
    premises: list[Knowledge] = field(default_factory=list)
    conclusion: Knowledge | None = None
    background: list[Knowledge] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)
    reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    label: str | None = None
    formal_expr: list | None = None
    sub_strategies: list[Strategy] = field(default_factory=list)

    def __post_init__(self):
        pkg = _current_package.get()
        if pkg is not None:
            pkg._register_strategy(self)


@dataclass
class Operator:
    """A deterministic logical constraint."""

    operator: str
    variables: list[Knowledge] = field(default_factory=list)
    conclusion: Knowledge | None = None
    reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        pkg = _current_package.get()
        if pkg is not None:
            pkg._register_operator(self)


class Package:
    """Context manager that collects all DSL declarations."""

    def __init__(self, name: str, *, namespace: str = "reg", version: str = "0.1.0"):
        self.name = name
        self.namespace = namespace
        self.version = version
        self.knowledge: list[Knowledge] = []
        self.strategies: list[Strategy] = []
        self.operators: list[Operator] = []
        self._token = None

    def __enter__(self):
        self._token = _current_package.set(self)
        return self

    def __exit__(self, *exc):
        _current_package.reset(self._token)
        self._token = None

    def _register_knowledge(self, k: Knowledge):
        self.knowledge.append(k)

    def _register_strategy(self, s: Strategy):
        self.strategies.append(s)

    def _register_operator(self, o: Operator):
        self.operators.append(o)

    @property
    def exported(self) -> list[str]:
        return [k.label for k in self.knowledge if k.label is not None]
