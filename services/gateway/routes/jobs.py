"""Job management routes — GET/DELETE /jobs/{job_id}."""

from fastapi import APIRouter, HTTPException

from services.gateway.deps import deps

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}")
async def get_job_status(job_id: str):
    job = await deps.job_manager.get_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": job.job_id,
        "type": job.job_type,
        "status": job.status,
        "progress": job.progress,
        "created_at": job.created_at.isoformat(),
        "updated_at": job.updated_at.isoformat(),
    }


@router.get("/{job_id}/result")
async def get_job_result(job_id: str):
    job = await deps.job_manager.get_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "completed":
        raise HTTPException(status_code=409, detail=f"Job status is {job.status}")
    return {"job_id": job.job_id, "status": job.status, "result": job.result}


@router.delete("/{job_id}")
async def cancel_job(job_id: str):
    job = await deps.job_manager.get_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    await deps.job_manager.cancel(job_id)
    return {"job_id": job.job_id, "status": "cancelled"}
