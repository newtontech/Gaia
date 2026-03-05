"""Batch API routes -- all async via JobManager."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from libs.models import CommitRequest
from services.gateway.deps import deps
from services.job_manager.models import JobType

router = APIRouter(tags=["batch"])


# -- Batch Commit (#9) -------------------------------------------------------


class BatchCommitRequest(BaseModel):
    commits: list[CommitRequest]
    auto_review: bool = True
    auto_merge: bool = True


@router.post("/commits/batch")
async def batch_commit(request: BatchCommitRequest):
    async def work(job_id: str) -> dict:
        results = []
        for req in request.commits:
            commit_resp = await deps.commit_engine.submit(req)
            entry = {
                "commit_id": commit_resp.commit_id,
                "message": req.message,
                "status": commit_resp.status,
            }
            if commit_resp.status == "rejected":
                results.append(entry)
                continue

            if request.auto_review:
                job = await deps.commit_engine.submit_review(commit_resp.commit_id)
                for _ in range(100):
                    status = await deps.commit_engine.job_manager.get_status(job.job_id)
                    if status.status.value in ("completed", "failed"):
                        break
                    await asyncio.sleep(0.05)

                review_result = await deps.commit_engine.job_manager.get_result(
                    job.job_id
                )
                approved = (
                    review_result.get("overall_verdict") == "pass"
                    if isinstance(review_result, dict)
                    else False
                )
                entry["status"] = "reviewed" if approved else "rejected"

                if approved and request.auto_merge:
                    merge_result = await deps.commit_engine.merge(commit_resp.commit_id)
                    entry["status"] = (
                        "merged" if merge_result.success else "merge_failed"
                    )
                    entry["merge_result"] = merge_result.model_dump()

            results.append(entry)
        return {"commits": results, "total": len(results)}

    job = await deps.job_manager.submit(
        job_type=JobType.BATCH_COMMIT,
        reference_id=f"batch_{len(request.commits)}",
        work_fn=work,
    )
    return {
        "job_id": job.job_id,
        "total_commits": len(request.commits),
        "status": job.status,
    }
