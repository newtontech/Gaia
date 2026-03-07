"""Execute a DSL package — walk chains, call actions."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .models import (
    ChainExpr,
    Declaration,
    InferAction,
    Package,
    Ref,
    StepApply,
    StepLambda,
    StepRef,
    ToolCallAction,
)


class ActionExecutor(ABC):
    """Abstract interface for executing actions (LLM, tools, etc.)."""

    @abstractmethod
    def execute_infer(self, content: str, args: dict[str, str]) -> str:
        """Execute an InferAction. Returns the reasoning result text."""

    @abstractmethod
    def execute_lambda(self, content: str, input_text: str) -> str:
        """Execute a Lambda step. Returns the reasoning result text."""


def execute_package(pkg: Package, executor: ActionExecutor) -> None:
    """Execute all ChainExprs in the package, filling in empty claims.

    Walks each chain's steps in order. For Application and Lambda steps,
    calls the executor and writes the result to the output claim.
    """
    # Build lookup: name -> Declaration (across all modules, resolving refs)
    decls: dict[str, Declaration] = {}
    actions: dict[str, InferAction | ToolCallAction] = {}

    for module in pkg.loaded_modules:
        for decl in module.declarations:
            if isinstance(decl, Ref):
                if decl._resolved is not None:
                    decls[decl.name] = decl._resolved
            else:
                decls[decl.name] = decl
                if isinstance(decl, (InferAction, ToolCallAction)):
                    actions[decl.name] = decl

    # Execute each ChainExpr
    for module in pkg.loaded_modules:
        for decl in module.declarations:
            if isinstance(decl, ChainExpr):
                _execute_chain(decl, decls, actions, executor)


def _execute_chain(
    chain: ChainExpr,
    decls: dict[str, Declaration],
    actions: dict[str, InferAction | ToolCallAction],
    executor: ActionExecutor,
) -> None:
    """Execute a single ChainExpr."""
    steps = chain.steps

    for i, step in enumerate(steps):
        if isinstance(step, StepApply):
            action = actions.get(step.apply)
            if action is None:
                continue

            # Build args dict: param_name -> content
            args_content: dict[str, str] = {}
            for j, arg in enumerate(step.args):
                ref_decl = decls.get(arg.ref)
                if ref_decl is not None and hasattr(ref_decl, "content"):
                    param_name = action.params[j].name if j < len(action.params) else arg.ref
                    args_content[param_name] = ref_decl.content

            # Execute
            result = executor.execute_infer(action.content, args_content)

            # Write result to the next step's claim (if empty)
            if i + 1 < len(steps):
                next_step = steps[i + 1]
                if isinstance(next_step, StepRef):
                    target = decls.get(next_step.ref)
                    if target is not None and hasattr(target, "content"):
                        if not target.content or not target.content.strip():
                            target.content = result

        elif isinstance(step, StepLambda):
            # Get input from previous step
            input_text = ""
            if i > 0:
                prev = steps[i - 1]
                if isinstance(prev, StepRef):
                    prev_decl = decls.get(prev.ref)
                    if prev_decl is not None and hasattr(prev_decl, "content"):
                        input_text = prev_decl.content

            result = executor.execute_lambda(step.lambda_, input_text)

            # Write result to the next step's claim (if empty)
            if i + 1 < len(steps):
                next_step = steps[i + 1]
                if isinstance(next_step, StepRef):
                    target = decls.get(next_step.ref)
                    if target is not None and hasattr(target, "content"):
                        if not target.content or not target.content.strip():
                            target.content = result
