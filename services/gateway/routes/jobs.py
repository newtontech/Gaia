"""Job management routes — GET/DELETE /jobs/{job_id}."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Any
from services.gateway.deps import deps

router = APIRouter(prefix="/jobs", tags=["jobs"])


class JobStatusResponse(BaseModel):
    """Job status response model."""
    job_id: str = Field(description="Unique job identifier")
    type: str = Field(description="Job type (e.g., review, batch)")
    status: str = Field(description="Current status (pending, running, completed, failed, cancelled)")
    progress: float = Field(description="Progress percentage (0-100)")
    created_at: str = Field(description="Job creation timestamp")
    updated_at: str = Field(description="Last update timestamp")


class JobResultResponse(BaseModel):
    """Job result response model."""
    job_id: str = Field(description="Unique job identifier")
    status: str = Field(description="Job status")
    result: Optional[Any] = Field(None, description="Job result data (if completed)")


class CancelJobResponse(BaseModel):
    """Cancel job response model."""
    job_id: str = Field(description="Unique job identifier")
    status: str = Field(description="New status after cancellation")


@router.get(
    "/{job_id}",
    summary="Get job status",
    description="Retrieve the current status and progress of a job.",
    response_model=JobStatusResponse,
    responses={
        200: {
            "description": "Job status retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "job_id": "job_review_abc123",
                        "type": "review",
                        "status": "running",
                        "progress": 45.5,
                        "created_at": "2026-03-01T10:00:00Z",
                        "updated_at": "2026-03-01T10:05:30Z"
                    }
                }
            }
        },
        404: {
            "description": "Job not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Job not found"}
                }
            }
        }
    }
)
async def get_job_status(job_id: str):
    """
    Get the status of a job.
    
    Returns current job information including:
    - Job type (review, batch, etc.)
    - Status (pending, running, completed, failed, cancelled)
    - Progress percentage
    - Creation and update timestamps
    
    Use this endpoint to poll for job completion.
    """
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


@router.get(
    "/{job_id}/result",
    summary="Get job result",
    description="Retrieve the result of a completed job. Only available when status is 'completed'.",
    response_model=JobResultResponse,
    responses={
        200: {
            "description": "Job result retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "job_id": "job_review_abc123",
                        "status": "completed",
                        "result": {
                            "operations": [{"index": 0, "verdict": "pass"}],
                            "overall_verdict": "pass",
                            "bp_results": {"belief_updates": {}, "converged": True}
                        }
                    }
                }
            }
        },
        404: {
            "description": "Job not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Job not found"}
                }
            }
        },
        409: {
            "description": "Job not completed yet",
            "content": {
                "application/json": {
                    "example": {"detail": "Job status is running"}
                }
            }
        }
    }
)
async def get_job_result(job_id: str):
    """
    Get the result of a completed job.
    
    **Note**: Results are only available when job status is 'completed'.
    For other statuses, this endpoint returns 409 Conflict.
    
    Result format varies by job type:
    - Review jobs: Review results including verdicts and belief updates
    - Batch jobs: Batch processing results and statistics
    """
    job = await deps.job_manager.get_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "completed":
        raise HTTPException(status_code=409, detail=f"Job status is {job.status}")
    return {"job_id": job.job_id, "status": job.status, "result": job.result}


@router.delete(
    "/{job_id}",
    summary="Cancel job",
    description="Cancel a running or pending job. Cannot cancel completed or already cancelled jobs.",
    response_model=CancelJobResponse,
    responses={
        200: {
            "description": "Job cancelled successfully",
            "content": {
                "application/json": {
                    "example": {
                        "job_id": "job_review_abc123",
                        "status": "cancelled"
                    }
                }
            }
        },
        404: {
            "description": "Job not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Job not found"}
                }
            }
        },
        409: {
            "description": "Job cannot be cancelled",
            "content": {
                "application/json": {
                    "example": {"detail": "Cannot cancel completed job"}
                }
            }
        }
    }
)
async def cancel_job(job_id: str):
    """
    Cancel a job.
    
    Cancels a running or pending job. This action is irreversible.
    
    **Limitations**:
    - Cannot cancel already completed jobs
    - Cannot cancel already cancelled jobs
    - Cancellation may not immediately stop all in-progress operations
    """
    job = await deps.job_manager.get_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    await deps.job_manager.cancel(job_id)
    return {"job_id": job.job_id, "status": "cancelled"}
