import asyncio

import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, MagicMock

from services.gateway.app import create_app
from services.gateway.deps import Dependencies
from services.job_manager.manager import JobManager
from services.job_manager.models import JobType
from services.job_manager.store import InMemoryJobStore


@pytest.fixture
def test_deps():
    deps = Dependencies()
    deps.storage = MagicMock()
    deps.storage.graph = None
    deps.storage.vector = AsyncMock()
    deps.search_engine = MagicMock()
    deps.commit_engine = MagicMock()
    deps.job_manager = JobManager(store=InMemoryJobStore())
    return deps


@pytest.fixture
async def client(test_deps):
    app = create_app(dependencies=test_deps)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_get_job_status(client, test_deps):
    async def work(job_id):
        return {"done": True}

    job = await test_deps.job_manager.submit(JobType.REVIEW, "ref1", work)
    await asyncio.sleep(0.1)
    resp = await client.get(f"/jobs/{job.job_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"


async def test_get_job_result(client, test_deps):
    async def work(job_id):
        return {"answer": 42}

    job = await test_deps.job_manager.submit(JobType.REVIEW, "ref2", work)
    await asyncio.sleep(0.1)
    resp = await client.get(f"/jobs/{job.job_id}/result")
    assert resp.status_code == 200
    assert resp.json()["result"] == {"answer": 42}


async def test_delete_job(client, test_deps):
    async def slow(job_id):
        await asyncio.sleep(10)

    job = await test_deps.job_manager.submit(JobType.REVIEW, "ref3", slow)
    resp = await client.delete(f"/jobs/{job.job_id}")
    assert resp.status_code == 200


async def test_get_nonexistent_job(client):
    resp = await client.get("/jobs/nonexistent")
    assert resp.status_code == 404
