from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Optional
from services.gateway.deps import deps
from services.search_engine.models import NodeFilters, EdgeFilters

router = APIRouter(prefix="/search", tags=["search"])


class TextSearchRequest(BaseModel):
    """Request for BM25 text search."""
    query: str = Field(
        description="Search query text",
        examples=["high pressure superconductivity"]
    )
    k: int = Field(
        default=50,
        ge=1,
        le=1000,
        description="Number of results to return",
        examples=[50]
    )


class TextSearchResult(BaseModel):
    """Single text search result."""
    node: dict = Field(description="Node object")
    score: float = Field(description="BM25 relevance score")


@router.post(
    "/text",
    summary="Text search (BM25)",
    description="Pure BM25 text search without requiring embeddings. Suitable for fast keyword-based search.",
    response_model=List[TextSearchResult],
    responses={
        200: {
            "description": "Search results retrieved successfully",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "node": {
                                "id": 251,
                                "type": "paper-extract",
                                "title": "YH10 high-pressure superconductivity",
                                "content": "fcc YH10 phase superconducts at 400GPa with Tc≈303K"
                            },
                            "score": 0.95
                        }
                    ]
                }
            }
        }
    }
)
async def search_text(request: TextSearchRequest):
    """
    BM25-only text search — no embedding required.
    
    This endpoint performs pure keyword-based search using BM25 algorithm.
    It's faster than vector search and doesn't require embedding generation.
    
    Use cases:
    - Quick keyword lookup
    - Exact phrase matching
    - When embedding service is unavailable
    """
    results = await deps.storage.lance.fts_search(request.query, k=request.k)
    node_ids = [nid for nid, _ in results]
    nodes = await deps.storage.lance.load_nodes_bulk(node_ids)
    scores = {nid: score for nid, score in results}
    return [{"node": n.model_dump(), "score": scores.get(n.id, 0.0)} for n in nodes]


class SearchNodesRequest(BaseModel):
    """Request for semantic node search."""
    query: str = Field(
        description="Search query text",
        examples=["high pressure superconductivity"]
    )
    embedding: Optional[List[float]] = Field(
        default=None,
        description="DEPRECATED: Embedding is now generated internally. This field will be removed in v3.1.",
        deprecated=True
    )
    k: int = Field(
        default=50,
        ge=1,
        le=1000,
        description="Number of results to return",
        examples=[50]
    )
    filters: Optional[NodeFilters] = Field(
        default=None,
        description="Optional filters to apply"
    )
    paths: Optional[List[str]] = Field(
        default=None,
        description="Optional path filters"
    )


class SearchEdgesRequest(BaseModel):
    """Request for semantic edge search."""
    query: str = Field(
        description="Search query text",
        examples=["DFT calculation methods"]
    )
    embedding: Optional[List[float]] = Field(
        default=None,
        description="DEPRECATED: Embedding is now generated internally. This field will be removed in v3.1.",
        deprecated=True
    )
    k: int = Field(
        default=50,
        ge=1,
        le=1000,
        description="Number of results to return",
        examples=[50]
    )
    filters: Optional[EdgeFilters] = Field(
        default=None,
        description="Optional filters to apply"
    )
    paths: Optional[List[str]] = Field(
        default=None,
        description="Optional path filters"
    )


@router.post(
    "/nodes",
    summary="Semantic node search",
    description="Search nodes using semantic similarity. Embeddings are generated internally.",
    response_model=List[dict],
    responses={
        200: {
            "description": "Search results retrieved successfully",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "node_id": 251,
                            "title": "YH10 high-pressure superconductivity",
                            "content": "fcc YH10 phase superconducts at 400GPa with Tc≈303K",
                            "similarity": 0.89,
                            "belief": 0.65,
                            "type": "paper-extract"
                        }
                    ]
                }
            }
        }
    }
)
async def search_nodes(request: SearchNodesRequest):
    """
    Search nodes using semantic similarity.
    
    **Note on embedding parameter (deprecated):**
    The `embedding` field is deprecated and will be removed in v3.1.
    Embeddings are now generated internally by the search engine.
    
    This endpoint uses multi-way recall:
    - Vector similarity search
    - BM25 text search
    - Topology-based search
    
    Results are fused and re-ranked for optimal relevance.
    """
    results = await deps.search_engine.search_nodes(
        query=request.query,
        embedding=request.embedding,
        k=request.k,
        filters=request.filters,
        paths=request.paths,
    )
    return [r.model_dump() for r in results]


@router.post(
    "/hyperedges",
    summary="Semantic hyperedge search",
    description="Search hyperedges using semantic similarity. Embeddings are generated internally.",
    response_model=List[dict],
    responses={
        200: {
            "description": "Search results retrieved successfully",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "edge_id": 1234,
                            "type": "paper-extract",
                            "reasoning": [{"title": "DFT+Eliashberg", "content": "..."}],
                            "tail_summary": ["DFT calculation", "phonon dynamics"],
                            "head_summary": ["YH10 Tc≈303K"],
                            "similarity": 0.87
                        }
                    ]
                }
            }
        }
    }
)
async def search_hyperedges(request: SearchEdgesRequest):
    """
    Search hyperedges using semantic similarity.
    
    **Note on embedding parameter (deprecated):**
    The `embedding` field is deprecated and will be removed in v3.1.
    Embeddings are now generated internally by the search engine.
    
    Searches through edge reasoning and summaries to find relevant hyperedges.
    """
    results = await deps.search_engine.search_edges(
        query=request.query,
        embedding=request.embedding,
        k=request.k,
        filters=request.filters,
        paths=request.paths,
    )
    return [r.model_dump() for r in results]
