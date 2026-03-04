from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List
from libs.models import CommitRequest, CommitResponse, MergeResult
from services.gateway.deps import deps

router = APIRouter(prefix="/commits", tags=["commits"])


class ReviewRequest(BaseModel):
    """Request body for reviewing a commit."""
    depth: str = Field(
        default="standard",
        description="Review depth: 'standard' for full pipeline, 'quick' for basic dedup only",
        examples=["standard"]
    )


class ReviewResponse(BaseModel):
    """Response from reviewing a commit."""
    approved: bool = Field(description="Whether the commit is approved")
    issues: List[str] = Field(default=[], description="List of issues found during review")
    suggestions: List[str] = Field(default=[], description="List of suggestions for improvement")


class MergeRequest(BaseModel):
    """Request body for merging a commit."""
    force: bool = Field(
        default=False,
        description="Force merge even if review has issues",
        examples=[False]
    )


class CommitListItem(BaseModel):
    """Single commit item in the list."""
    commit_id: str = Field(description="Unique identifier for the commit")
    status: str = Field(description="Current status of the commit")
    message: str = Field(description="Commit message")
    created_at: str = Field(description="Creation timestamp")


class CommitListResponse(BaseModel):
    """Response containing list of commits."""
    commits: List[CommitListItem] = Field(description="List of commits")
    total: int = Field(description="Total number of commits")


@router.get(
    "",
    summary="List all commits",
    description="Returns a list of all commits in the system, ordered by creation time (newest first).",
    response_model=CommitListResponse,
    responses={
        200: {
            "description": "List of commits retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "commits": [
                            {
                                "commit_id": "abc123",
                                "status": "pending_review",
                                "message": "Add YH10 superconductivity findings",
                                "created_at": "2026-03-01T12:00:00Z"
                            }
                        ],
                        "total": 1
                    }
                }
            }
        }
    }
)
async def list_commits():
    """
    List all commits in the system.
    
    Returns commits ordered by creation time (newest first).
    Each commit includes its ID, status, message, and creation timestamp.
    """
    commits = await deps.commit_engine.list_commits()
    return CommitListResponse(
        commits=[
            CommitListItem(
                commit_id=c.commit_id,
                status=c.status,
                message=c.message,
                created_at=c.created_at.isoformat() if c.created_at else ""
            )
            for c in commits
        ],
        total=len(commits)
    )


@router.post(
    "",
    summary="Submit a new commit",
    description="Submit a new commit with graph operations. Performs lightweight structural validation synchronously.",
    response_model=CommitResponse,
    responses={
        200: {
            "description": "Commit submitted successfully",
            "content": {
                "application/json": {
                    "example": {
                        "commit_id": "abc123",
                        "status": "pending_review",
                        "check_results": {
                            "operations": [
                                {"index": 0, "op": "add_edge", "structural_valid": True}
                            ]
                        }
                    }
                }
            }
        },
        400: {
            "description": "Invalid request - structural validation failed",
            "content": {
                "application/json": {
                    "example": {"detail": "Operation 0: tail cannot be empty"}
                }
            }
        }
    }
)
async def submit_commit(request: CommitRequest):
    """
    Submit a new commit with graph operations.
    
    Performs lightweight structural validation synchronously:
    - Validates tail/head are non-empty
    - Validates operation types are valid
    - Validates references for modify operations
    
    The commit enters 'pending_review' state and can be reviewed asynchronously.
    """
    return await deps.commit_engine.submit(request)


@router.get(
    "/{commit_id}",
    summary="Get commit details",
    description="Retrieve detailed information about a specific commit by its ID.",
    responses={
        200: {
            "description": "Commit details retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "commit_id": "abc123",
                        "status": "pending_review",
                        "message": "Add YH10 superconductivity findings",
                        "operations": [],
                        "check_results": {},
                        "created_at": "2026-03-01T12:00:00Z",
                        "updated_at": "2026-03-01T12:00:00Z"
                    }
                }
            }
        },
        404: {
            "description": "Commit not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Commit not found"}
                }
            }
        }
    }
)
async def get_commit(commit_id: str):
    """
    Get detailed information about a specific commit.
    
    Returns full commit details including:
    - Commit metadata (ID, status, message)
    - List of operations
    - Check results from structural validation
    - Review results (if available)
    - Merge results (if available)
    """
    commit = await deps.commit_engine.get_commit(commit_id)
    if not commit:
        raise HTTPException(status_code=404, detail="Commit not found")
    return commit.model_dump()


@router.post(
    "/{commit_id}/review",
    summary="Review a commit",
    description="Submit a commit for review with specified depth. Review is performed asynchronously.",
    response_model=ReviewResponse,
    responses={
        200: {
            "description": "Review completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "approved": True,
                        "issues": [],
                        "suggestions": ["Consider adding more context to the reasoning"]
                    }
                }
            }
        },
        404: {
            "description": "Commit not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Commit not found"}
                }
            }
        }
    }
)
async def review_commit(commit_id: str, request: ReviewRequest = ReviewRequest()):
    """
    Submit a commit for review.
    
    Review depth options:
    - **standard**: Full review pipeline including embedding, NN search, join detection, verification, and BP
    - **quick**: Basic dedup detection only (faster but less thorough)
    
    The review process checks for:
    - Duplicate or semantically equivalent nodes
    - Logical contradictions
    - Reasoning chain validity
    - Quality metrics (tightness, substantiveness, novelty)
    """
    commit = await deps.commit_engine.get_commit(commit_id)
    if not commit:
        raise HTTPException(status_code=404, detail="Commit not found")
    result = await deps.commit_engine.review(commit_id, depth=request.depth)
    return result


@router.post(
    "/{commit_id}/merge",
    summary="Merge a commit",
    description="Merge an approved commit into the knowledge graph. Requires the commit to have passed review unless force=true.",
    response_model=MergeResult,
    responses={
        200: {
            "description": "Commit merged successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "new_node_ids": [1001, 1002],
                        "new_edge_ids": [5001],
                        "errors": []
                    }
                }
            }
        },
        400: {
            "description": "Merge failed - commit not approved",
            "content": {
                "application/json": {
                    "example": {"detail": "Commit has not been approved for merge"}
                }
            }
        },
        404: {
            "description": "Commit not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Commit not found"}
                }
            }
        }
    }
)
async def merge_commit(commit_id: str, request: MergeRequest = MergeRequest()):
    """
    Merge an approved commit into the knowledge graph.
    
    The merge process:
    1. Creates new nodes for add_edge operations
    2. Creates hyperedges connecting nodes
    3. Persists embeddings from review pipeline
    4. Persists belief values from BP calculation
    5. Indexes all new data
    
    **Note**: By default, only commits with 'reviewed' status can be merged.
    Use force=true to bypass this check (requires appropriate permissions).
    """
    commit = await deps.commit_engine.get_commit(commit_id)
    if not commit:
        raise HTTPException(status_code=404, detail="Commit not found")
    return await deps.commit_engine.merge(commit_id, force=request.force)
