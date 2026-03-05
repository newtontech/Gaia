# tests/services/test_gateway/test_batch.py
import asyncio

import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, MagicMock

from libs.models import CommitResponse, MergeResult
from services.gateway.app import create_app
from services.gateway.deps import Dependencies
from services.job_manager.manager import JobManager
from services.job_manager.models import Job, JobStatus, JobType
from services.job_manager.store import InMemoryJobStore


def _make_completed_review_job():
    """Create a mock completed review job."""
    job = Job(job_type=JobType.REVIEW, reference_id="c1")
    job.status = JobStatus.COMPLETED
    job.result = {"overall_verdict": "pass"}
    return job


@pytest.fixture
def deps():
    d = Dependencies()
    d.storage = MagicMock()
    d.storage.graph = None
    d.storage.lance = MagicMock()
    d.storage.vector = AsyncMock()
    d.search_engine = MagicMock()
    d.commit_engine = MagicMock()
    d.commit_engine.submit = AsyncMock(
        return_value=CommitResponse(commit_id="c1", status="pending_review")
    )
    d.commit_engine.submit_review = AsyncMock(return_value=MagicMock(job_id="rj1"))
    d.commit_engine.job_manager = MagicMock()
    d.commit_engine.job_manager.get_status = AsyncMock(
        return_value=_make_completed_review_job()
    )
    d.commit_engine.job_manager.get_result = AsyncMock(
        return_value={"overall_verdict": "pass"}
    )
    d.commit_engine.merge = AsyncMock(
        return_value=MergeResult(success=True, new_node_ids=[1], new_edge_ids=[10])
    )
    d.job_manager = JobManager(store=InMemoryJobStore())
    d.inference_engine = MagicMock()
    return d


@pytest.fixture
async def client(deps):
    app = create_app(dependencies=deps)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_batch_commit_returns_job(client):
    resp = await client.post(
        "/commits/batch",
        json={
            "commits": [
                {"message": "paper 1", "operations": []},
                {"message": "paper 2", "operations": []},
            ],
            "auto_review": True,
            "auto_merge": True,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "job_id" in data
    assert data["total_commits"] == 2


async def test_batch_commit_result(client):
    resp = await client.post(
        "/commits/batch",
        json={
            "commits": [{"message": "paper 1", "operations": []}],
            "auto_review": True,
            "auto_merge": True,
        },
    )
    job_id = resp.json()["job_id"]
    await asyncio.sleep(0.3)

    resp = await client.get(f"/jobs/{job_id}/result")
    assert resp.status_code == 200
    result = resp.json()["result"]
    assert "commits" in result
