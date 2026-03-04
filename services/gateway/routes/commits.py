from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from libs.models import CommitRequest, CommitResponse, MergeResult
from services.gateway.deps import deps

router = APIRouter(prefix="/commits", tags=["commits"])


class MergeRequest(BaseModel):
    force: bool = False


@router.get("")
async def list_commits():
    commits = await deps.commit_engine.list_commits()
    return [c.model_dump() for c in commits]


@router.post("", response_model=CommitResponse)
async def submit_commit(request: CommitRequest):
    return await deps.commit_engine.submit(request)


@router.get("/{commit_id}")
async def get_commit(commit_id: str):
    commit = await deps.commit_engine.get_commit(commit_id)
    if not commit:
        raise HTTPException(status_code=404, detail="Commit not found")
    return commit.model_dump()


@router.post("/{commit_id}/review")
async def review_commit(commit_id: str):
    """Submit async review job for a commit."""
    commit = await deps.commit_engine.get_commit(commit_id)
    if not commit:
        raise HTTPException(status_code=404, detail="Commit not found")
    try:
        job = await deps.commit_engine.submit_review(commit_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"job_id": job.job_id, "status": job.status.value}


@router.get("/{commit_id}/review")
async def get_review_status(commit_id: str):
    """Get review job status."""
    commit = await deps.commit_engine.get_commit(commit_id)
    if not commit or not commit.review_job_id:
        raise HTTPException(status_code=404, detail="No review job found")
    job = await deps.commit_engine.job_manager.get_status(commit.review_job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Review job not found")
    return {"job_id": job.job_id, "status": job.status.value, "progress": job.progress}


@router.delete("/{commit_id}/review")
async def cancel_review(commit_id: str):
    """Cancel a running review job."""
    commit = await deps.commit_engine.get_commit(commit_id)
    if not commit or not commit.review_job_id:
        raise HTTPException(status_code=404, detail="No review job found")
    cancelled = await deps.commit_engine.job_manager.cancel(commit.review_job_id)
    return {"cancelled": cancelled}


@router.get("/{commit_id}/review/result")
async def get_review_result(commit_id: str):
    """Get the detailed review result."""
    commit = await deps.commit_engine.get_commit(commit_id)
    if not commit or not commit.review_job_id:
        raise HTTPException(status_code=404, detail="No review job found")
    result = await deps.commit_engine.job_manager.get_result(commit.review_job_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Review result not available yet")
    return result


@router.post("/{commit_id}/merge", response_model=MergeResult)
async def merge_commit(commit_id: str, request: MergeRequest = MergeRequest()):
    commit = await deps.commit_engine.get_commit(commit_id)
    if not commit:
        raise HTTPException(status_code=404, detail="Commit not found")
    return await deps.commit_engine.merge(commit_id, force=request.force)
