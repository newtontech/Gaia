import pytest
from services.review_pipeline.operators.verify import (
    AbstractionTreeVerifyOperator,
    VerifyAgainOperator,
    StubVerifyLLM,
)
from services.review_pipeline.context import AbstractionTree, PipelineContext
from libs.models import CommitRequest, ModifyNodeOp


@pytest.fixture
def context_with_trees():
    req = CommitRequest(
        message="t",
        operations=[ModifyNodeOp(node_id=1, changes={"x": 1})],
    )
    ctx = PipelineContext.from_commit_request(req)
    ctx.cc_abstraction_trees = [
        AbstractionTree(source_node_index=0, target_node_id=100, relation="partial_overlap"),
        AbstractionTree(source_node_index=0, target_node_id=200, relation="equivalent"),
    ]
    ctx.cp_abstraction_trees = [
        AbstractionTree(source_node_index=1, target_node_id=300, relation="subsumes"),
    ]
    return ctx


async def test_verify_marks_trees(context_with_trees):
    op = AbstractionTreeVerifyOperator(verify_llm=StubVerifyLLM())
    result = await op.execute(context_with_trees)
    # Stub auto-verifies all trees
    all_trees = result.cc_abstraction_trees + result.cp_abstraction_trees
    assert all(t.verified for t in all_trees)


async def test_verify_again_filters(context_with_trees):
    # Mark one as verified, one not
    context_with_trees.cc_abstraction_trees[0].verified = True
    context_with_trees.cc_abstraction_trees[1].verified = False
    context_with_trees.cp_abstraction_trees[0].verified = True

    op = VerifyAgainOperator(verify_llm=StubVerifyLLM())
    result = await op.execute(context_with_trees)
    assert len(result.verified_trees) == 3  # stub verifies all
