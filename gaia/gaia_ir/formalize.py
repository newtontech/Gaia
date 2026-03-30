"""IR-side formalization of named strategies into FormalStrategy skeletons.

Named reasoning families lower to canonical FormalExpr templates inside Gaia IR.
This module generates both the explicit intermediate Knowledge nodes and the
matching FormalStrategy for those templates.
"""

from __future__ import annotations

import hashlib
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from gaia.gaia_ir.knowledge import Knowledge, KnowledgeType
from gaia.gaia_ir.operator import Operator
from gaia.gaia_ir.strategy import (
    FormalExpr,
    FormalStrategy,
    Step,
    StrategyType,
)


_NAMED_TEMPLATE_TYPES = frozenset(
    {
        StrategyType.DEDUCTION,
        StrategyType.REDUCTIO,
        StrategyType.ELIMINATION,
        StrategyType.MATHEMATICAL_INDUCTION,
        StrategyType.CASE_ANALYSIS,
        StrategyType.ABDUCTION,
        StrategyType.INDUCTION,
        StrategyType.ANALOGY,
        StrategyType.EXTRAPOLATION,
    }
)

_HELPER_KIND_BY_OPERATOR = {
    "conjunction": "conjunction_result",
    "disjunction": "disjunction_result",
    "equivalence": "equivalence_result",
    "contradiction": "contradiction_result",
    "complement": "complement_result",
}


@dataclass
class FormalizationResult:
    """Generated intermediate claims plus the fully-expanded FormalStrategy."""

    knowledges: list[Knowledge]
    strategy: FormalStrategy


def _sha256_hex(data: str, length: int = 16) -> str:
    return hashlib.sha256(data.encode()).hexdigest()[:length]


def _generated_claim_id(
    scope: str,
    strategy_type: StrategyType,
    premises: list[str],
    conclusion: str,
    role: str,
    index: int,
) -> str:
    prefix = "lcn_" if scope == "local" else "gcn_"
    payload = f"{scope}|{strategy_type.value}|{premises}|{conclusion}|{role}|{index}"
    return f"{prefix}{_sha256_hex(payload)}"


class _TemplateBuilder:
    def __init__(self, scope: str, strategy_type: StrategyType, premises: list[str], conclusion: str):
        self.scope = scope
        self.strategy_type = strategy_type
        self.premises = premises
        self.conclusion = conclusion
        self.knowledges: list[Knowledge] = []
        self._role_counters: dict[str, int] = defaultdict(int)

    def add_latent(self, role: str, canonical_name: str) -> Knowledge:
        return self._add_claim(role=role, canonical_name=canonical_name, kind="latent_claim")

    def add_helper(self, operator_name: str, canonical_name: str) -> Knowledge:
        return self._add_claim(
            role=_HELPER_KIND_BY_OPERATOR[operator_name],
            canonical_name=canonical_name,
            kind="helper_claim",
            helper_kind=_HELPER_KIND_BY_OPERATOR[operator_name],
        )

    def _add_claim(
        self,
        *,
        role: str,
        canonical_name: str,
        kind: str,
        helper_kind: str | None = None,
    ) -> Knowledge:
        index = self._role_counters[role]
        self._role_counters[role] += 1

        metadata: dict[str, Any] = {
            "generated": True,
            "generated_kind": kind,
            "intermediate_role": role,
            "visibility": "formal_internal",
            "canonical_name": canonical_name,
            "owning_strategy_type": self.strategy_type.value,
        }
        if helper_kind is not None:
            metadata["helper_kind"] = helper_kind
            metadata["helper_visibility"] = "formal_internal"

        knowledge = Knowledge(
            id=_generated_claim_id(
                self.scope,
                self.strategy_type,
                self.premises,
                self.conclusion,
                role,
                index,
            ),
            type=KnowledgeType.CLAIM,
            content=canonical_name,
            metadata=metadata,
        )
        self.knowledges.append(knowledge)
        return knowledge


def _all_true_name(variables: list[str]) -> str:
    return f"all_true({','.join(variables)})"


def _any_true_name(variables: list[str]) -> str:
    return f"any_true({','.join(variables)})"


def _same_truth_name(left: str, right: str) -> str:
    return f"same_truth({left},{right})"


def _not_both_true_name(left: str, right: str) -> str:
    return f"not_both_true({left},{right})"


def _opposite_truth_name(left: str, right: str) -> str:
    return f"opposite_truth({left},{right})"


def _build_deduction(builder: _TemplateBuilder) -> list[Operator]:
    if len(builder.premises) < 2:
        raise ValueError("deduction formalization requires at least 2 premises")
    conjunction = builder.add_helper("conjunction", _all_true_name(builder.premises))
    return [
        Operator(operator="conjunction", variables=builder.premises, conclusion=conjunction.id),
        Operator(operator="implication", variables=[conjunction.id], conclusion=builder.conclusion),
    ]


def _build_mathematical_induction(builder: _TemplateBuilder) -> list[Operator]:
    if len(builder.premises) != 2:
        raise ValueError("mathematical_induction formalization requires exactly 2 premises")
    conjunction = builder.add_helper("conjunction", _all_true_name(builder.premises))
    return [
        Operator(operator="conjunction", variables=builder.premises, conclusion=conjunction.id),
        Operator(operator="implication", variables=[conjunction.id], conclusion=builder.conclusion),
    ]


def _build_reductio(builder: _TemplateBuilder) -> list[Operator]:
    if len(builder.premises) != 1:
        raise ValueError("reductio formalization requires exactly 1 premise")
    premise = builder.premises[0]
    assumption = builder.add_latent(
        "reductio_assumption",
        f"reductio_assumption_against({builder.conclusion})",
    )
    consequence = builder.add_latent(
        "reductio_consequence",
        f"reductio_consequence({assumption.id})",
    )
    contradiction = builder.add_helper(
        "contradiction",
        _not_both_true_name(consequence.id, premise),
    )
    complement = builder.add_helper(
        "complement",
        _opposite_truth_name(assumption.id, builder.conclusion),
    )
    return [
        Operator(operator="implication", variables=[assumption.id], conclusion=consequence.id),
        Operator(
            operator="contradiction",
            variables=[consequence.id, premise],
            conclusion=contradiction.id,
        ),
        Operator(
            operator="complement",
            variables=[assumption.id, builder.conclusion],
            conclusion=complement.id,
        ),
    ]


def _build_elimination(builder: _TemplateBuilder) -> list[Operator]:
    if len(builder.premises) != 3:
        raise ValueError("elimination formalization requires exactly 3 premises")
    evidence_1, evidence_2, _exhaustiveness = builder.premises
    h1 = builder.add_latent("elimination_hypothesis", f"elimination_hypothesis({builder.conclusion},1)")
    h2 = builder.add_latent("elimination_hypothesis", f"elimination_hypothesis({builder.conclusion},2)")
    not_h1 = builder.add_latent("elimination_negated_hypothesis", f"negation_of({h1.id})")
    not_h2 = builder.add_latent("elimination_negated_hypothesis", f"negation_of({h2.id})")
    contra_1 = builder.add_helper("contradiction", _not_both_true_name(h1.id, evidence_1))
    contra_2 = builder.add_helper("contradiction", _not_both_true_name(h2.id, evidence_2))
    comp_1 = builder.add_helper("complement", _opposite_truth_name(h1.id, not_h1.id))
    comp_2 = builder.add_helper("complement", _opposite_truth_name(h2.id, not_h2.id))
    conjunction = builder.add_helper("conjunction", _all_true_name([not_h1.id, not_h2.id]))
    return [
        Operator(operator="contradiction", variables=[h1.id, evidence_1], conclusion=contra_1.id),
        Operator(operator="contradiction", variables=[h2.id, evidence_2], conclusion=contra_2.id),
        Operator(operator="complement", variables=[h1.id, not_h1.id], conclusion=comp_1.id),
        Operator(operator="complement", variables=[h2.id, not_h2.id], conclusion=comp_2.id),
        Operator(
            operator="conjunction",
            variables=[not_h1.id, not_h2.id],
            conclusion=conjunction.id,
        ),
        Operator(operator="implication", variables=[conjunction.id], conclusion=builder.conclusion),
    ]


def _build_case_analysis(builder: _TemplateBuilder) -> list[Operator]:
    if len(builder.premises) < 3:
        raise ValueError("case_analysis formalization requires at least 3 premises")
    _exhaustiveness, *case_supports = builder.premises
    case_claims = [
        builder.add_latent("case_branch", f"case_branch({builder.conclusion},{index + 1})")
        for index in range(len(case_supports))
    ]
    disjunction = builder.add_helper(
        "disjunction",
        _any_true_name([case_claim.id for case_claim in case_claims]),
    )
    operators = [
        Operator(
            operator="disjunction",
            variables=[case_claim.id for case_claim in case_claims],
            conclusion=disjunction.id,
        )
    ]
    for case_claim, support in zip(case_claims, case_supports, strict=True):
        conjunction = builder.add_helper(
            "conjunction",
            _all_true_name([case_claim.id, support]),
        )
        operators.append(
            Operator(
                operator="conjunction",
                variables=[case_claim.id, support],
                conclusion=conjunction.id,
            )
        )
        operators.append(
            Operator(
                operator="implication",
                variables=[conjunction.id],
                conclusion=builder.conclusion,
            )
        )
    return operators


def _build_abduction(builder: _TemplateBuilder) -> list[Operator]:
    if len(builder.premises) != 1:
        raise ValueError("abduction formalization requires exactly 1 premise")
    observation = builder.premises[0]
    prediction = builder.add_latent("prediction", f"prediction({builder.conclusion},{observation})")
    equivalence = builder.add_helper(
        "equivalence",
        _same_truth_name(prediction.id, observation),
    )
    return [
        Operator(operator="implication", variables=[builder.conclusion], conclusion=prediction.id),
        Operator(
            operator="equivalence",
            variables=[prediction.id, observation],
            conclusion=equivalence.id,
        ),
    ]


def _build_induction(builder: _TemplateBuilder) -> list[Operator]:
    if not builder.premises:
        raise ValueError("induction formalization requires at least 1 premise")
    operators: list[Operator] = []
    for index, observation in enumerate(builder.premises, start=1):
        instance = builder.add_latent(
            "instance",
            f"instance({builder.conclusion},{index},{observation})",
        )
        equivalence = builder.add_helper(
            "equivalence",
            _same_truth_name(instance.id, observation),
        )
        operators.append(
            Operator(operator="implication", variables=[builder.conclusion], conclusion=instance.id)
        )
        operators.append(
            Operator(
                operator="equivalence",
                variables=[instance.id, observation],
                conclusion=equivalence.id,
            )
        )
    return operators


def _build_analogy(builder: _TemplateBuilder) -> list[Operator]:
    if len(builder.premises) != 2:
        raise ValueError("analogy formalization requires exactly 2 premises")
    conjunction = builder.add_helper("conjunction", _all_true_name(builder.premises))
    return [
        Operator(operator="conjunction", variables=builder.premises, conclusion=conjunction.id),
        Operator(operator="implication", variables=[conjunction.id], conclusion=builder.conclusion),
    ]


def _build_extrapolation(builder: _TemplateBuilder) -> list[Operator]:
    if len(builder.premises) != 2:
        raise ValueError("extrapolation formalization requires exactly 2 premises")
    conjunction = builder.add_helper("conjunction", _all_true_name(builder.premises))
    return [
        Operator(operator="conjunction", variables=builder.premises, conclusion=conjunction.id),
        Operator(operator="implication", variables=[conjunction.id], conclusion=builder.conclusion),
    ]


_BUILDERS = {
    StrategyType.DEDUCTION: _build_deduction,
    StrategyType.REDUCTIO: _build_reductio,
    StrategyType.ELIMINATION: _build_elimination,
    StrategyType.MATHEMATICAL_INDUCTION: _build_mathematical_induction,
    StrategyType.CASE_ANALYSIS: _build_case_analysis,
    StrategyType.ABDUCTION: _build_abduction,
    StrategyType.INDUCTION: _build_induction,
    StrategyType.ANALOGY: _build_analogy,
    StrategyType.EXTRAPOLATION: _build_extrapolation,
}


def formalize_named_strategy(
    *,
    scope: str,
    type_: StrategyType | str,
    premises: list[str],
    conclusion: str,
    background: list[str] | None = None,
    steps: list[Step] | None = None,
    metadata: dict[str, Any] | None = None,
) -> FormalizationResult:
    """Generate the canonical FormalStrategy skeleton for a named strategy family."""
    strategy_type = StrategyType(type_)
    if strategy_type not in _NAMED_TEMPLATE_TYPES:
        allowed = ", ".join(sorted(t.value for t in _NAMED_TEMPLATE_TYPES))
        raise ValueError(
            f"formalize_named_strategy only supports named FormalStrategy types: {allowed}; "
            f"got {strategy_type.value}"
        )

    builder = _TemplateBuilder(scope=scope, strategy_type=strategy_type, premises=premises, conclusion=conclusion)
    operators = _BUILDERS[strategy_type](builder)
    strategy_metadata = dict(metadata or {})
    strategy_metadata["generated_formal_expr"] = True
    strategy_metadata["formalization_template"] = strategy_type.value

    strategy = FormalStrategy(
        scope=scope,
        type=strategy_type,
        premises=premises,
        conclusion=conclusion,
        background=background,
        steps=steps,
        metadata=strategy_metadata,
        formal_expr=FormalExpr(operators=operators),
    )

    for knowledge in builder.knowledges:
        knowledge.metadata = dict(knowledge.metadata or {})
        knowledge.metadata["owning_strategy_id"] = strategy.strategy_id

    return FormalizationResult(knowledges=builder.knowledges, strategy=strategy)
