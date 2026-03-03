from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.gateway.deps import deps
from services.search_engine.models import NodeFilters, EdgeFilters

router = APIRouter(prefix="/search", tags=["search"])


class SearchNodesRequest(BaseModel):
    query: str
    embedding: list[float]
    k: int = 50
    filters: NodeFilters | None = None
    paths: list[str] | None = None


class SearchEdgesRequest(BaseModel):
    query: str
    embedding: list[float]
    k: int = 50
    filters: EdgeFilters | None = None
    paths: list[str] | None = None


@router.post("/nodes")
async def search_nodes(request: SearchNodesRequest):
    results = await deps.search_engine.search_nodes(
        query=request.query,
        embedding=request.embedding,
        k=request.k,
        filters=request.filters,
        paths=request.paths,
    )
    return [r.model_dump() for r in results]


@router.post("/hyperedges")
async def search_hyperedges(request: SearchEdgesRequest):
    results = await deps.search_engine.search_edges(
        query=request.query,
        embedding=request.embedding,
        k=request.k,
        filters=request.filters,
        paths=request.paths,
    )
    return [r.model_dump() for r in results]
