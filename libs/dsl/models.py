"""Gaia DSL Pydantic models — the type system as Python classes."""

from __future__ import annotations

from pydantic import BaseModel, Field


# ── Terminals ──────────────────────────────────────────────

class Param(BaseModel):
    name: str
    type: str


class Arg(BaseModel):
    ref: str
    dependency: str | None = None  # "direct" | "indirect" (V3)


class Manifest(BaseModel):
    description: str | None = None
    authors: list[str] = Field(default_factory=list)
    license: str | None = None


# ── Steps (in a ChainExpr) ────────────────────────────────

class StepRef(BaseModel):
    step: int
    ref: str


class StepApply(BaseModel):
    step: int
    apply: str
    args: list[Arg] = Field(default_factory=list)
    prior: float | None = None


class StepLambda(BaseModel):
    step: int
    lambda_: str = Field(alias="lambda")
    prior: float | None = None

    model_config = {"populate_by_name": True}


Step = StepRef | StepApply | StepLambda


# ── Declarations (unified — everything is Knowledge) ──────

class Declaration(BaseModel):
    """Base for all declarations. Subclasses set type as a literal."""

    type: str
    name: str
    metadata: dict | None = None
    prior: float | None = None


class Claim(Declaration):
    type: str = "claim"
    content: str = ""


class Question(Declaration):
    type: str = "question"
    content: str = ""


class Setting(Declaration):
    type: str = "setting"
    content: str = ""


class InferAction(Declaration):
    type: str = "infer_action"
    params: list[Param] = Field(default_factory=list)
    return_type: str | None = None
    content: str = ""


class ToolCallAction(Declaration):
    type: str = "toolcall_action"
    params: list[Param] = Field(default_factory=list)
    return_type: str | None = None
    content: str = ""
    tool: str | None = None


class ChainExpr(Declaration):
    type: str = "chain_expr"
    steps: list[Step] = Field(default_factory=list)


class Ref(Declaration):
    type: str = "ref"
    target: str = ""


# ── Module ────────────────────────────────────────────────

DECLARATION_TYPE_MAP: dict[str, type[Declaration]] = {
    "claim": Claim,
    "question": Question,
    "setting": Setting,
    "infer_action": InferAction,
    "toolcall_action": ToolCallAction,
    "chain_expr": ChainExpr,
    "ref": Ref,
}


class Module(BaseModel):
    type: str  # reasoning_module, setting_module, etc.
    name: str
    declarations: list[Declaration] = Field(default_factory=list)
    export: list[str] = Field(default_factory=list)


# ── Package ───────────────────────────────────────────────

class Package(BaseModel):
    name: str
    version: str | None = None
    manifest: Manifest | None = None
    modules_list: list[str] = Field(default_factory=list, alias="modules")
    export: list[str] = Field(default_factory=list)
    # Populated after loading module files:
    loaded_modules: list[Module] = Field(default_factory=list, exclude=True)

    model_config = {"populate_by_name": True}
