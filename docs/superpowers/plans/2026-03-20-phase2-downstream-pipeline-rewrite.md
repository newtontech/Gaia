# Phase 2: Downstream Pipeline Rewrite — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite the downstream pipeline (review → infer → publish) to work with Typst-native Graph IR, eliminating all `lang_models.Package` dependencies, then delete all YAML-era code.

**Architecture:** Phase 1 built `Typst → RawGraph → LocalCanonicalGraph`. Phase 2 bridges the gap from `LocalCanonicalGraph` to storage (LanceDB/Kuzu) by rewriting `pipeline_review()`, `pipeline_infer()`, and `pipeline_publish()` to accept `graph_data` dict + `LocalCanonicalGraph` instead of `lang_models.Package`. A new `ReviewOutput` dataclass replaces `ReviewResult.merged_package`. A new converter replaces `cli/lang_to_storage.py`.

**Tech Stack:** Python 3.12, Pydantic v2, pytest (asyncio_mode=auto), litellm (LLM review), LanceDB, Kuzu

**Fixtures:** `tests/fixtures/gaia_language_packages/galileo_falling_bodies_v3/` (primary Typst v3 fixture)

**Critical notes from plan review:**
1. **Belief ID mismatch**: `adapter._display_label()` returns `"module.name"` but storage Knowledge uses `"pkg/name"`. Fix: adjust belief snapshot converter to use `source_ref.knowledge_name` directly (not the label).
2. **V2IngestData relocation**: Must move `V2IngestData` dataclass into `libs/pipeline.py` before deleting `cli/lang_to_storage.py` in Chunk 7.
3. **Chain.type Literal**: `"equivalence"` is not in `storage_models.Chain.type`. Fix: add `"equivalence"` to the Literal in Chunk 1.
4. **Factor ID hash change**: Normalizing `"reasoning"` → `"infer"` changes factor_id hashes. This is intentional and breaks compatibility with Phase 1 test artifacts (acceptable).

---

## Chunk 1: Fix Factor Type Compatibility

The typst_compiler outputs factor types (`"reasoning"`, `"mutex_constraint"`, `"equiv_constraint"`) that the adapter and storage models don't recognize. Normalize to the canonical set: `"infer"`, `"contradiction"`, `"equivalence"`.

### Task 1.1: Update typst_compiler factor types

**Files:**
- Modify: `libs/graph_ir/typst_compiler.py`
- Test: `tests/libs/graph_ir/test_typst_compiler.py`

- [ ] **Step 1: Write failing test for normalized factor types**

```python
# In tests/libs/graph_ir/test_typst_compiler.py — add new test
def test_reasoning_factor_type_is_infer():
    """Reasoning factors should have type='infer' for adapter compatibility."""
    graph_data = {
        "package": "test_pkg",
        "version": "0.1.0",
        "nodes": [
            {"name": "premise_a", "type": "setting", "content": "A", "module": "mod"},
            {"name": "conclusion_b", "type": "claim", "content": "B", "module": "mod"},
        ],
        "factors": [
            {"type": "reasoning", "premise": ["premise_a"], "conclusion": "conclusion_b"},
        ],
        "constraints": [],
    }
    raw_graph = compile_typst_to_raw_graph(graph_data)
    factor = raw_graph.factor_nodes[0]
    assert factor.type == "infer"


def test_constraint_factor_types_are_canonical():
    """Constraint factors should use canonical types for adapter compatibility."""
    graph_data = {
        "package": "test_pkg",
        "version": "0.1.0",
        "nodes": [
            {"name": "claim_a", "type": "claim", "content": "A", "module": "mod"},
            {"name": "claim_b", "type": "claim", "content": "B", "module": "mod"},
            {"name": "contra", "type": "contradiction", "content": "C", "module": "mod"},
        ],
        "factors": [],
        "constraints": [
            {"name": "contra", "type": "contradiction", "between": ["claim_a", "claim_b"]},
        ],
    }
    raw_graph = compile_typst_to_raw_graph(graph_data)
    constraint_factor = [f for f in raw_graph.factor_nodes if f.conclusion is not None]
    assert len(constraint_factor) == 1
    assert constraint_factor[0].type == "contradiction"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/libs/graph_ir/test_typst_compiler.py::test_reasoning_factor_type_is_infer -v`
Expected: FAIL — `assert "reasoning" == "infer"`

- [ ] **Step 3: Update typst_compiler to use canonical types**

In `libs/graph_ir/typst_compiler.py`:

1. Change the `_CONSTRAINT_TYPE_TO_FACTOR_TYPE` map:
```python
_CONSTRAINT_TYPE_TO_FACTOR_TYPE = {
    "contradiction": "contradiction",
    "equivalence": "equivalence",
}
```

2. In the reasoning factor compilation (around line 113):
```python
factor_nodes.append(
    FactorNode(
        factor_id=factor_id("infer", conclusion_module, conclusion_name),
        type="infer",
        ...
    )
)
```

- [ ] **Step 4: Update existing tests that assert old type names**

Search for assertions on `"reasoning"`, `"mutex_constraint"`, `"equiv_constraint"` in test files and update them.

- [ ] **Step 5: Run all typst_compiler tests**

Run: `pytest tests/libs/graph_ir/test_typst_compiler.py -v`
Expected: ALL PASS

- [ ] **Step 6: Add `"equivalence"` to storage Chain.type Literal**

In `libs/storage/models.py`, update the `Chain.type` field:
```python
type: Literal["deduction", "induction", "abstraction", "contradiction", "retraction", "equivalence"]
```

- [ ] **Step 7: Commit**

```bash
git add libs/graph_ir/typst_compiler.py tests/libs/graph_ir/test_typst_compiler.py libs/storage/models.py
git commit -m "fix: normalize typst_compiler factor types to match adapter/storage canonical set"
```

---

## Chunk 2: Unify BuildResult + Rewrite pipeline_build

Merge `BuildResult` and `TypstBuildResult` into a single Typst-native `BuildResult`. Replace `pipeline_build()` with the Typst pipeline.

### Task 2.1: Unify BuildResult dataclass

**Files:**
- Modify: `libs/pipeline.py`
- Test: `tests/test_pipeline_typst.py`

- [ ] **Step 1: Write test for new unified BuildResult**

```python
# In tests/test_pipeline_typst.py — update imports and add test
from libs.pipeline import BuildResult, pipeline_build

GALILEO_V3 = (
    Path(__file__).parent / "fixtures" / "gaia_language_packages" / "galileo_falling_bodies_v3"
)


@pytest.mark.asyncio
async def test_pipeline_build_returns_build_result():
    result = await pipeline_build(GALILEO_V3)
    assert isinstance(result, BuildResult)
    assert "nodes" in result.graph_data
    assert result.raw_graph.package == "galileo_falling_bodies"
    assert len(result.local_graph.knowledge_nodes) > 0
    assert "lib.typ" in result.source_files
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_pipeline_typst.py::test_pipeline_build_returns_build_result -v`
Expected: FAIL — `pipeline_build` signature incompatible or `BuildResult` has wrong fields

- [ ] **Step 3: Rewrite BuildResult and pipeline_build**

In `libs/pipeline.py`:

```python
@dataclass
class BuildResult:
    """Unified build result for Typst packages."""
    graph_data: dict                    # typst_loader output (for renderer, proof_state)
    raw_graph: RawGraph
    local_graph: LocalCanonicalGraph
    canonicalization_log: list
    source_files: dict[str, str] = field(default_factory=dict)


async def pipeline_build(pkg_path: Path) -> BuildResult:
    """Load, compile, and canonicalize a Typst package — all in memory."""
    from libs.graph_ir.build_utils import build_singleton_local_graph
    from libs.graph_ir.typst_compiler import compile_typst_to_raw_graph
    from libs.lang.typst_loader import load_typst_package

    graph_data = load_typst_package(pkg_path)
    raw_graph = compile_typst_to_raw_graph(graph_data)
    canonicalization = build_singleton_local_graph(raw_graph)
    source_files = {p.name: p.read_text() for p in pkg_path.glob("*.typ") if p.is_file()}

    return BuildResult(
        graph_data=graph_data,
        raw_graph=raw_graph,
        local_graph=canonicalization.local_graph,
        canonicalization_log=canonicalization.log,
        source_files=source_files,
    )
```

Remove `TypstBuildResult` and `pipeline_build_typst`. Keep old `pipeline_build` as `_pipeline_build_yaml` (private, for CLI backward compat during transition).

Remove imports no longer needed: `from libs.lang.elaborator import ElaboratedPackage`, `from libs.lang import models as lang_models`.

- [ ] **Step 4: Update all existing tests that import TypstBuildResult/pipeline_build_typst**

In `tests/test_pipeline_typst.py`: change `pipeline_build_typst` → `pipeline_build`, `TypstBuildResult` → `BuildResult`.

- [ ] **Step 5: Run tests**

Run: `pytest tests/test_pipeline_typst.py -v`
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add libs/pipeline.py tests/test_pipeline_typst.py
git commit -m "refactor: unify BuildResult, make pipeline_build Typst-native"
```

---

## Chunk 3: Rewrite pipeline_review

Create `ReviewOutput` dataclass. Update `MockReviewClient` for v3 graph_data. Rewrite `pipeline_review()` to use `graph_data` + `typst_renderer`.

### Task 3.1: Create ReviewOutput and update MockReviewClient

**Files:**
- Modify: `libs/pipeline.py` (ReviewOutput)
- Modify: `cli/llm_client.py` (MockReviewClient)
- Create: `tests/test_pipeline_review.py`

- [ ] **Step 1: Write failing test for pipeline_review with v3 fixture**

```python
# tests/test_pipeline_review.py
from pathlib import Path

import pytest

from libs.pipeline import BuildResult, ReviewOutput, pipeline_build, pipeline_review

GALILEO_V3 = (
    Path(__file__).parent / "fixtures" / "gaia_language_packages" / "galileo_falling_bodies_v3"
)


@pytest.mark.asyncio
async def test_pipeline_review_mock_returns_review_output():
    build = await pipeline_build(GALILEO_V3)
    review = await pipeline_review(build, mock=True)
    assert isinstance(review, ReviewOutput)
    assert review.model == "mock"


@pytest.mark.asyncio
async def test_pipeline_review_mock_has_node_priors():
    build = await pipeline_build(GALILEO_V3)
    review = await pipeline_review(build, mock=True)
    # Every knowledge node should have a prior
    for node in build.local_graph.knowledge_nodes:
        assert node.local_canonical_id in review.node_priors
        assert 0 < review.node_priors[node.local_canonical_id] <= 1.0


@pytest.mark.asyncio
async def test_pipeline_review_mock_has_factor_params():
    build = await pipeline_build(GALILEO_V3)
    review = await pipeline_review(build, mock=True)
    # Each infer factor should have a conditional probability
    for factor in build.local_graph.factor_nodes:
        if factor.type == "infer":
            assert factor.factor_id in review.factor_params
            assert 0 < review.factor_params[factor.factor_id].conditional_probability <= 1.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_pipeline_review.py -v`
Expected: FAIL — `ReviewOutput` not defined, `pipeline_review` expects old `BuildResult`

- [ ] **Step 3: Create ReviewOutput dataclass**

In `libs/pipeline.py`:

```python
from libs.graph_ir.models import FactorParams


@dataclass
class ReviewOutput:
    """Result of reviewing a knowledge package (v3 Typst)."""
    review: dict                              # raw LLM/mock review data
    node_priors: dict[str, float]             # lcn_id → prior π
    factor_params: dict[str, FactorParams]    # factor_id → FactorParams
    model: str
    source_fingerprint: str | None = None
```

- [ ] **Step 4: Update MockReviewClient to support v3 graph_data**

In `cli/llm_client.py`, add method to `MockReviewClient`:

```python
def review_from_graph_data(self, graph_data: dict) -> dict:
    """Generate mock review from v3 Typst graph_data."""
    chains = []
    for factor in graph_data.get("factors", []):
        if factor.get("type") != "reasoning":
            continue
        conclusion = factor["conclusion"]
        chains.append({
            "chain": conclusion,
            "steps": [{
                "step": f"{conclusion}.1",
                "conditional_prior": 0.85,
                "weak_points": [],
                "explanation": "Mock review — accepted at default prior.",
            }],
        })
    return {"summary": "Mock review — all factors accepted at default priors.", "chains": chains}
```

- [ ] **Step 5: Rewrite pipeline_review**

In `libs/pipeline.py`:

```python
async def pipeline_review(
    build: BuildResult,
    *,
    mock: bool = False,
    model: str = "gpt-5-mini",
    source_fingerprint: str | None = None,
) -> ReviewOutput:
    """Review the package via LLM or mock reviewer."""
    from cli.llm_client import MockReviewClient, ReviewClient
    from libs.lang.typst_renderer import render_typst_to_markdown

    graph_data = build.graph_data
    package_name = graph_data.get("package", "unknown")

    if mock:
        client = MockReviewClient()
        result = client.review_from_graph_data(graph_data)
        actual_model = "mock"
    else:
        # Render markdown for LLM review
        # render_typst_to_markdown needs pkg_path; use graph_data directly with client
        client = ReviewClient(model=model)
        md = _render_markdown_from_graph_data(graph_data)
        result = await client.areview_package({"package": package_name, "markdown": md})
        actual_model = model

    # Build node_priors: default by knowledge_type
    node_priors = _extract_node_priors(build.local_graph)

    # Build factor_params from review results
    factor_params = _extract_factor_params(build.local_graph, result)

    return ReviewOutput(
        review=result,
        node_priors=node_priors,
        factor_params=factor_params,
        model=actual_model,
        source_fingerprint=source_fingerprint,
    )
```

- [ ] **Step 6: Implement helper functions**

In `libs/pipeline.py`:

```python
def _default_node_prior(knowledge_type: str) -> float:
    """Default prior by knowledge type."""
    if knowledge_type in ("contradiction", "equivalence", "corroboration"):
        return 0.5
    if knowledge_type == "question":
        return 0.5
    if knowledge_type in ("setting", "observation"):
        return 1.0
    return 0.5  # claim default


def _extract_node_priors(local_graph: LocalCanonicalGraph) -> dict[str, float]:
    """Extract node priors from local graph using type-based defaults."""
    return {
        node.local_canonical_id: _default_node_prior(node.knowledge_type)
        for node in local_graph.knowledge_nodes
    }


def _extract_factor_params(
    local_graph: LocalCanonicalGraph,
    review_result: dict,
) -> dict[str, FactorParams]:
    """Map review chain results to factor parameters."""
    from libs.graph_ir.models import FactorParams

    # Build conclusion_name → factor mapping
    name_to_factor: dict[str, str] = {}
    for factor in local_graph.factor_nodes:
        if factor.type == "infer" and factor.source_ref:
            name_to_factor[factor.source_ref.knowledge_name] = factor.factor_id

    # Parse review chains
    factor_params: dict[str, FactorParams] = {}
    for chain_entry in review_result.get("chains", []):
        chain_name = chain_entry.get("chain", "")
        factor_id = name_to_factor.get(chain_name)
        if factor_id is None:
            continue
        steps = chain_entry.get("steps", [])
        if steps:
            cp = steps[0].get("conditional_prior", 0.85)
            factor_params[factor_id] = FactorParams(conditional_probability=cp)

    # Default for factors not covered by review
    for factor in local_graph.factor_nodes:
        if factor.type == "infer" and factor.factor_id not in factor_params:
            factor_params[factor.factor_id] = FactorParams(conditional_probability=1.0)

    return factor_params


def _render_markdown_from_graph_data(graph_data: dict) -> str:
    """Render markdown from graph_data dict for LLM review (no filesystem needed)."""
    lines = []
    package_name = graph_data.get("package", "unknown")
    lines.append(f"# Package: {package_name}\n")

    # Render nodes grouped by type
    for node in graph_data.get("nodes", []):
        name = node["name"]
        node_type = node.get("type", "claim")
        content = node.get("content", "")
        lines.append(f"### {name} [{node_type}]")
        lines.append(f"> {content}\n")

    # Render factors with step markers for mock review compatibility
    for factor in graph_data.get("factors", []):
        if factor.get("type") != "reasoning":
            continue
        conclusion = factor["conclusion"]
        premises = factor.get("premise", [])
        lines.append(f"### {conclusion} [proof]")
        lines.append(f"**Premises:** {', '.join(premises)}")
        lines.append(f"**[step:{conclusion}.1]** (prior=0.85)\n")

    return "\n".join(lines)
```

- [ ] **Step 7: Run tests**

Run: `pytest tests/test_pipeline_review.py -v`
Expected: ALL PASS

- [ ] **Step 8: Commit**

```bash
git add libs/pipeline.py cli/llm_client.py tests/test_pipeline_review.py
git commit -m "feat: rewrite pipeline_review for Typst v3 with ReviewOutput"
```

---

## Chunk 4: Rewrite Parameterization + pipeline_infer

Replace `derive_local_parameterization()` with a version that uses `ReviewOutput` instead of `lang_models.Package`. Rewrite `pipeline_infer()`.

### Task 4.1: New derive_local_parameterization + pipeline_infer

**Files:**
- Modify: `libs/pipeline.py`
- Create: `tests/test_pipeline_infer.py`

- [ ] **Step 1: Write failing test for pipeline_infer**

```python
# tests/test_pipeline_infer.py
from pathlib import Path

import pytest

from libs.pipeline import InferResult, pipeline_build, pipeline_infer, pipeline_review

GALILEO_V3 = (
    Path(__file__).parent / "fixtures" / "gaia_language_packages" / "galileo_falling_bodies_v3"
)


@pytest.mark.asyncio
async def test_pipeline_infer_returns_result():
    build = await pipeline_build(GALILEO_V3)
    review = await pipeline_review(build, mock=True)
    infer = await pipeline_infer(build, review)
    assert isinstance(infer, InferResult)


@pytest.mark.asyncio
async def test_pipeline_infer_has_beliefs():
    build = await pipeline_build(GALILEO_V3)
    review = await pipeline_review(build, mock=True)
    infer = await pipeline_infer(build, review)
    assert len(infer.beliefs) > 0
    for name, belief in infer.beliefs.items():
        assert 0.0 <= belief <= 1.0


@pytest.mark.asyncio
async def test_pipeline_infer_has_bp_run_id():
    build = await pipeline_build(GALILEO_V3)
    review = await pipeline_review(build, mock=True)
    infer = await pipeline_infer(build, review)
    assert infer.bp_run_id  # non-empty string
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_pipeline_infer.py -v`
Expected: FAIL — `pipeline_infer` expects old `BuildResult` with `.package` field, or `ReviewResult` with `.merged_package`

- [ ] **Step 3: Rewrite pipeline_infer**

In `libs/pipeline.py`:

```python
async def pipeline_infer(
    build: BuildResult,
    review: ReviewOutput,
) -> InferResult:
    """Adapt local graph to factor graph and run Belief Propagation."""
    from libs.graph_ir.adapter import adapt_local_graph_to_factor_graph
    from libs.graph_ir.models import LocalParameterization
    from libs.inference.bp import BeliefPropagation

    # 1. Build LocalParameterization from ReviewOutput
    local_parameterization = LocalParameterization(
        graph_hash=build.local_graph.graph_hash(),
        node_priors=review.node_priors,
        factor_parameters=review.factor_params,
    )

    # 2. Adapt to factor graph
    adapted = adapt_local_graph_to_factor_graph(build.local_graph, local_parameterization)

    # 3. Run BP
    bp = BeliefPropagation()
    raw_beliefs = bp.run(adapted.factor_graph)

    # 4. Map var IDs back to names
    var_id_to_local = {var_id: local_id for local_id, var_id in adapted.local_id_to_var_id.items()}
    named_beliefs = {
        adapted.local_id_to_label[var_id_to_local[var_id]]: belief
        for var_id, belief in raw_beliefs.items()
    }

    bp_run_id = str(uuid.uuid4())

    return InferResult(
        beliefs=named_beliefs,
        bp_run_id=bp_run_id,
        local_parameterization=local_parameterization,
        adapted_graph=adapted,
    )
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_pipeline_infer.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add libs/pipeline.py tests/test_pipeline_infer.py
git commit -m "feat: rewrite pipeline_infer for Typst v3 ReviewOutput"
```

---

## Chunk 5: Rewrite pipeline_publish

Create a new converter that builds `V2IngestData` from `LocalCanonicalGraph` + `ReviewOutput` instead of `lang_models.Package`. Rewrite `pipeline_publish()`.

### Task 5.1: New convert_local_graph_to_storage

**Files:**
- Modify: `libs/pipeline.py`
- Create: `tests/test_pipeline_publish.py`

- [ ] **Step 1: Write failing test for the new converter**

```python
# tests/test_pipeline_publish.py
from pathlib import Path

import pytest

from libs.pipeline import (
    BuildResult,
    pipeline_build,
    pipeline_infer,
    pipeline_publish,
    pipeline_review,
)

GALILEO_V3 = (
    Path(__file__).parent / "fixtures" / "gaia_language_packages" / "galileo_falling_bodies_v3"
)


@pytest.mark.asyncio
async def test_pipeline_publish_to_lancedb(tmp_path):
    build = await pipeline_build(GALILEO_V3)
    review = await pipeline_review(build, mock=True)
    infer = await pipeline_infer(build, review)
    result = await pipeline_publish(build, review, infer, db_path=str(tmp_path / "db"))
    assert result.package_id == "galileo_falling_bodies"
    assert result.stats["knowledge_items"] > 0


@pytest.mark.asyncio
async def test_pipeline_publish_has_chains(tmp_path):
    build = await pipeline_build(GALILEO_V3)
    review = await pipeline_review(build, mock=True)
    infer = await pipeline_infer(build, review)
    result = await pipeline_publish(build, review, infer, db_path=str(tmp_path / "db"))
    # Galileo v3 has reasoning factors → should produce chains
    assert result.stats["chains"] > 0


@pytest.mark.asyncio
async def test_pipeline_publish_idempotent(tmp_path):
    db_path = str(tmp_path / "db")
    build = await pipeline_build(GALILEO_V3)
    review = await pipeline_review(build, mock=True)
    infer = await pipeline_infer(build, review)
    await pipeline_publish(build, review, infer, db_path=db_path)
    # Second publish should not error
    result = await pipeline_publish(build, review, infer, db_path=db_path)
    assert result.stats["knowledge_items"] > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_pipeline_publish.py -v`
Expected: FAIL — `pipeline_publish` expects old `ReviewResult` with `.merged_package`

- [ ] **Step 3: Move V2IngestData into pipeline.py + implement converter**

First, move the `V2IngestData` dataclass from `cli/lang_to_storage.py` into `libs/pipeline.py` (to avoid importing from a file that will be deleted in Chunk 7):

```python
@dataclass
class V2IngestData:
    """Result of converting to v2 storage models."""
    package: storage_models.Package
    modules: list[storage_models.Module] = field(default_factory=list)
    knowledge_items: list[storage_models.Knowledge] = field(default_factory=list)
    chains: list[storage_models.Chain] = field(default_factory=list)
    probabilities: list[storage_models.ProbabilityRecord] = field(default_factory=list)
    belief_snapshots: list[storage_models.BeliefSnapshot] = field(default_factory=list)
```

Then add the converter function:

```python
def _convert_local_graph_to_storage(
    build: BuildResult,
    review: ReviewOutput,
    beliefs: dict[str, float],
    bp_run_id: str,
) -> V2IngestData:
    """Convert LocalCanonicalGraph + ReviewOutput to V2 storage models."""
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    graph_data = build.graph_data
    local_graph = build.local_graph
    package_name = graph_data.get("package", "unknown")
    version = graph_data.get("version", "0.1.0")

    # 1. Package
    storage_package = storage_models.Package(
        package_id=package_name,
        name=package_name,
        version=version,
        description=None,
        modules=[f"{package_name}.{m}" for m in graph_data.get("modules", [])],
        exports=[f"{package_name}/{e}" for e in graph_data.get("exports", [])],
        submitter="cli",
        submitted_at=now,
        status="merged",
    )

    # 2. Modules
    module_titles = graph_data.get("module_titles", {})
    storage_modules = []
    for mod_name in graph_data.get("modules", []):
        role = _infer_module_role(mod_name)
        storage_modules.append(
            storage_models.Module(
                module_id=f"{package_name}.{mod_name}",
                package_id=package_name,
                package_version=version,
                name=mod_name,
                role=role,
            )
        )

    # 3. Knowledge items from local canonical nodes
    storage_knowledge = []
    lcn_to_kid: dict[str, str] = {}
    for node in local_graph.knowledge_nodes:
        sr = node.source_refs[0]
        knowledge_id = f"{sr.package}/{sr.knowledge_name}"
        lcn_to_kid[node.local_canonical_id] = knowledge_id

        # Map knowledge_type to storage type
        ktype = node.knowledge_type
        if ktype in ("observation",):
            ktype = "setting"  # observation stored as setting
        if ktype == "corroboration":
            ktype = "claim"
        valid_types = {"claim", "question", "setting", "action", "contradiction", "equivalence"}
        if ktype not in valid_types:
            ktype = "claim"

        prior = review.node_priors.get(node.local_canonical_id, 0.5)
        prior = max(prior, 1e-6)
        prior = min(prior, 1.0)

        storage_knowledge.append(
            storage_models.Knowledge(
                knowledge_id=knowledge_id,
                version=1,
                type=ktype,
                content=node.representative_content.strip(),
                prior=prior,
                keywords=[],
                source_package_id=sr.package,
                source_package_version=sr.version,
                source_module_id=f"{sr.package}.{sr.module}",
                created_at=now,
            )
        )

    # 4. Chains from factor nodes (each infer factor → single-step chain)
    storage_chains = []
    for factor in local_graph.factor_nodes:
        if factor.type not in ("infer", "abstraction"):
            continue
        if factor.conclusion is None:
            continue

        conclusion_kid = lcn_to_kid.get(factor.conclusion)
        if conclusion_kid is None:
            continue

        premise_refs = [
            storage_models.KnowledgeRef(knowledge_id=lcn_to_kid[p], version=1)
            for p in factor.premises
            if p in lcn_to_kid
        ]
        if not premise_refs:
            continue

        module_id = f"{package_name}.{factor.source_ref.module}" if factor.source_ref else package_name
        chain_type = "abstraction" if factor.type == "abstraction" else "deduction"

        storage_chains.append(
            storage_models.Chain(
                chain_id=f"{module_id}.{factor.source_ref.knowledge_name}" if factor.source_ref else factor.factor_id,
                module_id=module_id,
                package_id=package_name,
                package_version=version,
                type=chain_type,
                steps=[
                    storage_models.ChainStep(
                        step_index=0,
                        premises=premise_refs,
                        reasoning=node.representative_content.strip() if (node := _find_node(local_graph, factor.conclusion)) else "",
                        conclusion=storage_models.KnowledgeRef(knowledge_id=conclusion_kid, version=1),
                    )
                ],
            )
        )

    # 5. Relation chains (contradiction/equivalence factors)
    for factor in local_graph.factor_nodes:
        if factor.type not in ("contradiction", "equivalence"):
            continue
        if factor.conclusion is None:
            continue
        conclusion_kid = lcn_to_kid.get(factor.conclusion)
        if conclusion_kid is None:
            continue

        premise_refs = [
            storage_models.KnowledgeRef(knowledge_id=lcn_to_kid[p], version=1)
            for p in factor.premises
            if p in lcn_to_kid
        ]
        if not premise_refs:
            continue

        module_id = f"{package_name}.{factor.source_ref.module}" if factor.source_ref else package_name
        chain_type = factor.type  # "contradiction" or "equivalence" — valid Chain types

        storage_chains.append(
            storage_models.Chain(
                chain_id=f"{module_id}.{factor.source_ref.knowledge_name}" if factor.source_ref else factor.factor_id,
                module_id=module_id,
                package_id=package_name,
                package_version=version,
                type=chain_type,
                steps=[
                    storage_models.ChainStep(
                        step_index=0,
                        premises=premise_refs,
                        reasoning="",
                        conclusion=storage_models.KnowledgeRef(knowledge_id=conclusion_kid, version=1),
                    )
                ],
            )
        )

    # 6. Probabilities from review
    storage_probabilities = []
    for chain in storage_chains:
        for step in chain.steps:
            # Find factor param for this chain
            factor_id_match = None
            for factor in local_graph.factor_nodes:
                if factor.source_ref and f"{package_name}.{factor.source_ref.module}.{factor.source_ref.knowledge_name}" == chain.chain_id:
                    factor_id_match = factor.factor_id
                    break
            if factor_id_match and factor_id_match in review.factor_params:
                cp = review.factor_params[factor_id_match].conditional_probability
                storage_probabilities.append(
                    storage_models.ProbabilityRecord(
                        chain_id=chain.chain_id,
                        step_index=step.step_index,
                        value=max(min(cp, 1.0), 1e-6),
                        source="llm_review",
                        recorded_at=now,
                    )
                )

    # 7. Belief snapshots
    # NOTE: beliefs dict keys are "module.knowledge_name" (from adapter._display_label).
    # Storage knowledge_id is "package/knowledge_name". Build a mapping.
    label_to_kid: dict[str, str] = {}
    for node in local_graph.knowledge_nodes:
        if node.source_refs:
            sr = node.source_refs[0]
            label = f"{sr.module}.{sr.knowledge_name}"
            label_to_kid[label] = f"{sr.package}/{sr.knowledge_name}"

    seen_kids = {k.knowledge_id for k in storage_knowledge}
    storage_snapshots = []
    for var_label, belief_value in beliefs.items():
        knowledge_id = label_to_kid.get(var_label)
        if knowledge_id is None or knowledge_id not in seen_kids:
            continue
        storage_snapshots.append(
            storage_models.BeliefSnapshot(
                knowledge_id=knowledge_id,
                version=1,
                belief=max(min(belief_value, 1.0), 0.0),
                bp_run_id=bp_run_id,
                computed_at=now,
            )
        )

    return V2IngestData(
        package=storage_package,
        modules=storage_modules,
        knowledge_items=storage_knowledge,
        chains=storage_chains,
        probabilities=storage_probabilities,
        belief_snapshots=storage_snapshots,
    )


def _find_node(local_graph: LocalCanonicalGraph, lcn_id: str):
    """Find a knowledge node by local canonical ID."""
    for node in local_graph.knowledge_nodes:
        if node.local_canonical_id == lcn_id:
            return node
    return None


_MODULE_ROLE_KEYWORDS = {
    "motivation": "motivation",
    "setting": "setting",
    "reasoning": "reasoning",
    "follow_up": "follow_up_question",
    "question": "follow_up_question",
}


def _infer_module_role(module_name: str) -> str:
    """Infer module role from name conventions."""
    name_lower = module_name.lower()
    for keyword, role in _MODULE_ROLE_KEYWORDS.items():
        if keyword in name_lower:
            return role
    return "other"
```

- [ ] **Step 4: Rewrite pipeline_publish**

In `libs/pipeline.py`:

```python
async def pipeline_publish(
    build: BuildResult,
    review: ReviewOutput,
    infer: InferResult,
    *,
    storage_manager: "StorageManager | None" = None,
    storage_config: "StorageConfig | None" = None,
    db_path: str | None = None,
    embed_dim: int = 512,
) -> PublishResult:
    """Convert to storage models and ingest into StorageManager."""
    from libs.embedding import StubEmbeddingModel
    from libs.storage.config import StorageConfig
    from libs.storage.manager import StorageManager
    from libs.storage.models import KnowledgeEmbedding

    package_name = build.graph_data.get("package", "unknown")

    # 1. Convert to v2 storage models
    data = _convert_local_graph_to_storage(
        build=build,
        review=review,
        beliefs=infer.beliefs,
        bp_run_id=infer.bp_run_id,
    )

    # 2. Map Graph IR factors
    factors = _map_graph_ir_factors(build.local_graph, package_name)

    # 3. Build submission artifact
    submission_artifact = _build_submission_artifact_in_memory(build, package_name)

    # 4. Generate embeddings
    embed_model = StubEmbeddingModel(dim=embed_dim)
    texts = [k.content for k in data.knowledge_items]
    vectors = await embed_model.embed(texts) if texts else []
    embeddings = [
        KnowledgeEmbedding(knowledge_id=k.knowledge_id, version=k.version, embedding=vec)
        for k, vec in zip(data.knowledge_items, vectors)
    ]

    # 5. Resolve StorageManager
    _owns_mgr = storage_manager is None
    if _owns_mgr:
        if storage_config is None:
            if db_path is None:
                raise ValueError("Provide storage_manager, storage_config, or db_path")
            storage_config = StorageConfig(
                lancedb_path=db_path,
                graph_backend="kuzu",
                kuzu_path=f"{db_path}/kuzu",
            )
        mgr = StorageManager(storage_config)
        await mgr.initialize()
    else:
        mgr = storage_manager

    try:
        await mgr.ingest_package(
            package=data.package,
            modules=data.modules,
            knowledge_items=data.knowledge_items,
            chains=data.chains,
            factors=factors or None,
            submission_artifact=submission_artifact,
            embeddings=embeddings,
        )
        if data.probabilities:
            await mgr.add_probabilities(data.probabilities)
        if data.belief_snapshots:
            await mgr.write_beliefs(data.belief_snapshots)
    finally:
        if _owns_mgr:
            await mgr.close()

    stats = {
        "knowledge_items": len(data.knowledge_items),
        "chains": len(data.chains),
        "factors": len(factors),
        "probabilities": len(data.probabilities),
        "belief_snapshots": len(data.belief_snapshots),
    }

    return PublishResult(package_id=data.package.package_id, stats=stats)
```

- [ ] **Step 5: Update _build_submission_artifact_in_memory**

Update the type hint from `BuildResult` (old) to accept new `BuildResult`:

```python
def _build_submission_artifact_in_memory(
    build: BuildResult,
    package_name: str,
) -> storage_models.PackageSubmissionArtifact:
    """Build a PackageSubmissionArtifact from in-memory build results."""
    raw_graph_dict = json.loads(build.raw_graph.model_dump_json())
    local_graph_dict = json.loads(build.local_graph.model_dump_json())
    canon_log = [
        entry.model_dump() if hasattr(entry, "model_dump") else entry
        for entry in build.canonicalization_log
    ]
    return storage_models.PackageSubmissionArtifact(
        package_name=package_name,
        commit_hash="in-memory",
        source_files=build.source_files,
        raw_graph=raw_graph_dict,
        local_canonical_graph=local_graph_dict,
        canonicalization_log=canon_log,
        submitted_at=datetime.now(timezone.utc),
    )
```

- [ ] **Step 6: Run tests**

Run: `pytest tests/test_pipeline_publish.py -v`
Expected: ALL PASS

- [ ] **Step 7: Commit**

```bash
git add libs/pipeline.py tests/test_pipeline_publish.py
git commit -m "feat: rewrite pipeline_publish with new LocalCanonicalGraph converter"
```

---

## Chunk 6: End-to-End Integration Test + CLI Update

Write an E2E test that exercises the full pipeline with a Typst v3 fixture. Update CLI commands to use the new pipeline.

### Task 6.1: E2E integration test

**Files:**
- Create: `tests/test_pipeline_e2e_typst.py`

- [ ] **Step 1: Write E2E test**

```python
# tests/test_pipeline_e2e_typst.py
"""End-to-end test: build -> review(mock) -> infer -> publish for Typst v3 packages."""

from pathlib import Path

import pytest

from libs.pipeline import pipeline_build, pipeline_infer, pipeline_publish, pipeline_review

GALILEO_V3 = (
    Path(__file__).parent / "fixtures" / "gaia_language_packages" / "galileo_falling_bodies_v3"
)


@pytest.mark.asyncio
async def test_typst_v3_full_pipeline(tmp_path):
    """Galileo v3: build -> review(mock) -> infer -> publish."""
    db_path = str(tmp_path / "db")

    # Build
    build = await pipeline_build(GALILEO_V3)
    assert build.graph_data["package"] == "galileo_falling_bodies"
    assert len(build.local_graph.knowledge_nodes) > 0

    # Review (mock)
    review = await pipeline_review(build, mock=True)
    assert review.model == "mock"
    assert len(review.node_priors) == len(build.local_graph.knowledge_nodes)

    # Infer
    infer = await pipeline_infer(build, review)
    assert len(infer.beliefs) > 0

    # Publish
    result = await pipeline_publish(build, review, infer, db_path=db_path)
    assert result.package_id == "galileo_falling_bodies"
    assert result.stats["knowledge_items"] > 0
    assert result.stats["chains"] > 0

    # Verify data in LanceDB
    from libs.storage.config import StorageConfig
    from libs.storage.manager import StorageManager

    config = StorageConfig(lancedb_path=db_path, graph_backend="kuzu", kuzu_path=f"{db_path}/kuzu")
    mgr = StorageManager(config)
    await mgr.initialize()
    try:
        pkg = await mgr.content_store.get_package("galileo_falling_bodies")
        assert pkg is not None
        assert pkg.name == "galileo_falling_bodies"
    finally:
        await mgr.close()


@pytest.mark.asyncio
async def test_typst_v3_beliefs_are_reasonable(tmp_path):
    """Beliefs should be between 0 and 1 and settings should have high belief."""
    build = await pipeline_build(GALILEO_V3)
    review = await pipeline_review(build, mock=True)
    infer = await pipeline_infer(build, review)

    for name, belief in infer.beliefs.items():
        assert 0.0 <= belief <= 1.0, f"Belief for {name} out of range: {belief}"
```

- [ ] **Step 2: Run E2E test**

Run: `pytest tests/test_pipeline_e2e_typst.py -v`
Expected: ALL PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_pipeline_e2e_typst.py
git commit -m "test: add E2E integration test for Typst v3 full pipeline"
```

### Task 6.2: Update CLI commands for Typst

**Files:**
- Modify: `cli/main.py`

- [ ] **Step 4: Update CLI build command**

Update `_build_typst` in `cli/main.py` to also save Graph IR artifacts (like `_build_yaml` does):

```python
def _build_typst(pkg_path: Path, format: str, proof_state: bool = False) -> None:
    """Build a Typst-based knowledge package."""
    import json as json_mod

    from libs.graph_ir import save_canonicalization_log, save_local_canonical_graph, save_raw_graph
    from libs.pipeline import pipeline_build

    build_dir = pkg_path / ".gaia" / "build"
    graph_dir = pkg_path / ".gaia" / "graph"
    build_dir.mkdir(parents=True, exist_ok=True)

    # Run unified pipeline
    result = asyncio.run(pipeline_build(pkg_path))

    # Save Graph IR artifacts
    save_raw_graph(result.raw_graph, graph_dir)
    save_local_canonical_graph(result.local_graph, graph_dir)
    save_canonicalization_log(result.canonicalization_log, graph_dir)

    # Save graph_data as JSON
    json_path = build_dir / "graph_data.json"
    json_path.write_text(json_mod.dumps(result.graph_data, ensure_ascii=False, indent=2))

    # Save markdown
    if format in ("md", "all"):
        from libs.lang.typst_renderer import render_typst_to_markdown
        md = render_typst_to_markdown(pkg_path)
        md_path = build_dir / "package.md"
        md_path.write_text(md)
        typer.echo(f"Markdown: {md_path}")

    if format in ("typst", "all"):
        from libs.lang.typst_clean_renderer import render_typst_to_clean_typst
        typ = render_typst_to_clean_typst(pkg_path)
        typ_path = build_dir / "package.typ"
        typ_path.write_text(typ)
        typer.echo(f"Typst: {typ_path}")

    if proof_state:
        from libs.lang.proof_state import analyze_proof_state
        state = analyze_proof_state(result.graph_data)
        report_path = build_dir / "proof_state.txt"
        report_path.write_text(state["report"])
        typer.echo(f"Proof state: {report_path}")
        typer.echo(state["report"])

    n_nodes = len(result.local_graph.knowledge_nodes)
    n_factors = len(result.local_graph.factor_nodes)
    typer.echo(f"Built {result.graph_data['package']}: {n_nodes} nodes, {n_factors} factors")
    typer.echo(f"Artifacts: {graph_dir}/")
```

- [ ] **Step 5: Update CLI review command for Typst**

The current `review` command loads `pkg` from manifest.json (YAML format). For Typst, it should load graph_data from `graph_data.json` and use the new pipeline:

```python
@app.command()
def review(
    path: str = typer.Argument(".", help="Path to knowledge package directory"),
    mock: bool = typer.Option(False, "--mock", help="Use mock reviewer (no LLM calls)"),
    model: str = typer.Option("gpt-5-mini", "--model", help="LLM model for review"),
) -> None:
    """LLM reviews knowledge package -> sidecar report (.gaia/reviews/)."""
    import json as json_mod
    from datetime import datetime, timezone

    from cli.llm_client import MockReviewClient, ReviewClient

    pkg_path = Path(path)
    build_dir = pkg_path / ".gaia" / "build"
    reviews_dir = pkg_path / ".gaia" / "reviews"

    # Detect Typst vs YAML
    graph_data_path = build_dir / "graph_data.json"
    if graph_data_path.exists():
        _review_typst(pkg_path, mock, model)
        return

    # Legacy YAML path (kept during transition)
    _review_yaml(pkg_path, mock, model)
```

Implement `_review_typst`:

```python
def _review_typst(pkg_path: Path, mock: bool, model: str) -> None:
    """Review a Typst package using graph_data.json."""
    import json as json_mod
    from datetime import datetime, timezone

    from cli.llm_client import MockReviewClient, ReviewClient
    from libs.lang.typst_renderer import render_typst_to_markdown

    build_dir = pkg_path / ".gaia" / "build"
    reviews_dir = pkg_path / ".gaia" / "reviews"
    reviews_dir.mkdir(parents=True, exist_ok=True)

    graph_data = json_mod.loads((build_dir / "graph_data.json").read_text())
    package_name = graph_data.get("package", "unknown")

    # Get markdown for review
    md_path = build_dir / "package.md"
    if md_path.exists():
        md_content = md_path.read_text()
    else:
        md_content = render_typst_to_markdown(pkg_path)

    if mock:
        client = MockReviewClient()
        result = client.review_from_graph_data(graph_data)
        actual_model = "mock"
    else:
        client = ReviewClient(model=model)
        result = asyncio.run(
            client.areview_package({"package": package_name, "markdown": md_content})
        )
        actual_model = model

    now = datetime.now(timezone.utc)
    review_data = {
        "package": package_name,
        "model": actual_model,
        "timestamp": now.isoformat(),
        "source_fingerprint": _compute_source_fingerprint_typst(pkg_path),
        "summary": result.get("summary", ""),
        "chains": result.get("chains", []),
    }

    # Write review sidecar
    safe_ts = now.isoformat().replace(":", "-").split(".")[0]
    review_path = reviews_dir / f"review_{safe_ts}.yaml"
    review_path.write_text(yaml.dump(review_data, allow_unicode=True, sort_keys=False))

    n_chains = len(review_data["chains"])
    typer.echo(f"Reviewed {n_chains} reasoning factors for {package_name}")
    typer.echo(f"Report: {review_path}")


def _compute_source_fingerprint_typst(pkg_path: Path) -> str:
    """SHA-256 of all Typst source files sorted by name."""
    import hashlib
    h = hashlib.sha256()
    for typ_file in sorted(pkg_path.glob("*.typ")):
        h.update(typ_file.read_bytes())
    return h.hexdigest()[:16]
```

- [ ] **Step 6: Run full test suite**

Run: `pytest tests/ -v --ignore=tests/integration`
Expected: ALL PASS (some YAML tests may still pass via backward compat)

- [ ] **Step 7: Commit**

```bash
git add cli/main.py tests/test_pipeline_e2e_typst.py
git commit -m "feat: update CLI commands for Typst v3 pipeline"
```

---

## Chunk 7: YAML Cleanup

Delete all YAML-era files and tests. Move `plausible_core.py` to `future/`.

### Task 7.1: Delete YAML-era files

**Files to delete:**
- `libs/lang/loader.py`
- `libs/lang/resolver.py`
- `libs/lang/elaborator.py`
- `libs/lang/compiler.py`
- `libs/lang/models.py`
- `libs/lang/build_store.py`
- `libs/lang/runtime.py`
- `libs/lang/executor.py`
- `libs/graph_ir/build.py`
- `cli/lang_to_storage.py` (replaced by `_convert_local_graph_to_storage` in pipeline.py)
- `cli/review_store.py` (YAML review merge logic)
- `cli/manifest.py` (YAML manifest serialization)
- `cli/commands/lang.py` (YAML runtime CLI)

**Files to move to future/:**
- `libs/lang/plausible_core.py` → `future/lang/plausible_core.py` (already done in Phase 1)
- `tests/libs/lang/test_plausible_core.py` → `future/tests/test_plausible_core.py` (already done)

- [ ] **Step 1: Identify all import references to deleted files**

Run: `grep -r "from libs.lang.loader" --include="*.py" .`
Run: `grep -r "from libs.lang.models" --include="*.py" .`
(repeat for each deleted file)

Document which files need import updates.

- [ ] **Step 2: Remove old YAML imports from pipeline.py**

Remove any remaining imports of `lang_models`, `ElaboratedPackage`, `merge_review`, etc. from `libs/pipeline.py`. The old `_pipeline_build_yaml` function (if kept for transition) should also be removed.

- [ ] **Step 3: Remove old YAML imports from cli/main.py**

Update `cli/main.py`:
- Remove `_build_yaml()` function
- Remove `_load_with_deps()` function
- Remove YAML-specific `review` and `infer` code paths
- Remove `show` command (depends on `lang_models`)
- Update `build` to only handle Typst
- Remove imports of `cli.manifest`, `cli.review_store`, `libs.lang.loader`, `libs.lang.resolver`

- [ ] **Step 4: Delete the files**

```bash
git rm libs/lang/loader.py libs/lang/resolver.py libs/lang/elaborator.py \
  libs/lang/compiler.py libs/lang/models.py libs/lang/build_store.py \
  libs/lang/runtime.py libs/lang/executor.py \
  libs/graph_ir/build.py \
  cli/lang_to_storage.py cli/review_store.py cli/manifest.py \
  cli/commands/lang.py
```

- [ ] **Step 5: Delete YAML test files and fixtures**

Identify and delete test files that test YAML-era code:
```bash
# Test files for deleted modules
git rm tests/libs/lang/test_loader.py tests/libs/lang/test_resolver.py \
  tests/libs/lang/test_elaborator.py tests/libs/lang/test_compiler.py \
  tests/libs/lang/test_models.py tests/libs/lang/test_build_store.py \
  tests/libs/lang/test_runtime.py tests/libs/lang/test_executor.py \
  tests/libs/graph_ir/test_build.py \
  tests/cli/test_lang_to_storage.py tests/cli/test_review_store.py \
  tests/cli/test_manifest.py

# YAML fixture packages (keep v3 Typst fixtures)
git rm -r tests/fixtures/gaia_language_packages/galileo_falling_bodies/
git rm -r tests/fixtures/gaia_language_packages/newton_principia/
git rm -r tests/fixtures/gaia_language_packages/einstein_gravity/
```

Note: only delete files that actually exist. Use `ls` to verify before each `git rm`. Some test files may not exist or may have different names.

- [ ] **Step 6: Update libs/lang/__init__.py if it re-exports deleted modules**

- [ ] **Step 7: Update libs/graph_ir/__init__.py**

Remove re-exports of `build_raw_graph`, `derive_local_parameterization` from `build.py`. Keep re-exports from `build_utils.py`.

- [ ] **Step 8: Run full test suite**

Run: `pytest tests/ -v`
Expected: ALL PASS — no remaining references to deleted files

- [ ] **Step 9: Run lint**

Run: `ruff check . && ruff format --check .`
Expected: PASS

- [ ] **Step 10: Commit**

```bash
git add -A
git commit -m "chore: delete YAML-era code and tests (Phase 2 cleanup)"
```

---

## Post-Completion: Final Verification

After all chunks are done:

- [ ] Run full test suite: `pytest tests/ -v`
- [ ] Run lint: `ruff check . && ruff format --check .`
- [ ] Run E2E pipeline: `pytest tests/test_pipeline_e2e_typst.py -v`
- [ ] Verify CI passes on the PR branch

## Dependency Graph

```
Chunk 1 (factor types)
    ↓
Chunk 2 (BuildResult unification)
    ↓
Chunk 3 (pipeline_review)
    ↓
Chunk 4 (pipeline_infer)
    ↓
Chunk 5 (pipeline_publish)
    ↓
Chunk 6 (E2E test + CLI)
    ↓
Chunk 7 (YAML cleanup)
```

All chunks are sequential — each depends on the previous.
