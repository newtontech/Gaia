"""Gaia DSL Elaborator — deterministic template expansion.

Walks ChainExprs and produces rendered prompts for each StepApply/StepLambda.
Does NOT call any LLM — purely deterministic.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field

from .models import (
    Action,
    ChainExpr,
    Declaration,
    Package,
    Ref,
    StepApply,
    StepLambda,
)


@dataclass
class ElaboratedPackage:
    """Result of elaboration: the resolved package + rendered prompts."""

    package: Package
    prompts: list[dict] = field(default_factory=list)


def elaborate_package(pkg: Package) -> ElaboratedPackage:
    """Elaborate a resolved package: substitute templates, record rendered prompts.

    The original package is NOT modified — a deep copy is used internally.
    """
    pkg_copy = copy.deepcopy(pkg)

    # Build name->declaration index, resolving Refs to their targets
    decls_by_name: dict[str, Declaration] = {}
    for mod in pkg_copy.loaded_modules:
        for decl in mod.declarations:
            if isinstance(decl, Ref) and decl._resolved is not None:
                decls_by_name[decl.name] = decl._resolved
            else:
                decls_by_name[decl.name] = decl

    # Walk chains and elaborate
    prompts: list[dict] = []
    for mod in pkg_copy.loaded_modules:
        for decl in mod.declarations:
            if isinstance(decl, ChainExpr):
                chain_prompts = _elaborate_chain(decl, decls_by_name)
                prompts.extend(chain_prompts)

    return ElaboratedPackage(package=pkg_copy, prompts=prompts)


def _elaborate_chain(
    chain: ChainExpr, decls: dict[str, Declaration]
) -> list[dict]:
    """Elaborate a single chain's steps, returning rendered prompt dicts."""
    prompts = []

    for step in chain.steps:
        if isinstance(step, StepApply):
            action = decls.get(step.apply)
            if not action or not isinstance(action, Action):
                continue

            # Resolve args to content
            arg_records = []
            resolved_contents: list[str] = []
            for arg in step.args:
                target = decls.get(arg.ref)
                content = getattr(target, "content", "") if target else ""
                resolved_contents.append(content)
                arg_records.append({
                    "ref": arg.ref,
                    "dependency": arg.dependency,
                    "content": content,
                })

            # Substitute {param} templates
            rendered = action.content
            for param, content in zip(action.params, resolved_contents):
                rendered = rendered.replace(f"{{{param.name}}}", content)

            prompts.append({
                "chain": chain.name,
                "step": step.step,
                "action": step.apply,
                "rendered": rendered,
                "args": arg_records,
            })

        elif isinstance(step, StepLambda):
            prompts.append({
                "chain": chain.name,
                "step": step.step,
                "action": "__lambda__",
                "rendered": step.lambda_,
                "args": [],
            })

    return prompts
