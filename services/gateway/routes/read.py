import asyncio

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from services.gateway.deps import deps

router = APIRouter(tags=["read"])


class NodeResponse(BaseModel):
    """Node response model with full details."""
    id: int = Field(description="Unique node identifier")
    type: str = Field(description="Node type (e.g., paper-extract, deduction)")
    subtype: Optional[str] = Field(None, description="Optional subtype")
    title: Optional[str] = Field(None, description="Node title")
    content: str = Field(description="Node content")
    keywords: List[str] = Field(default=[], description="Associated keywords")
    belief: Optional[float] = Field(None, description="Belief score (0-1)")
    status: str = Field(description="Node status (active, deleted)")
    metadata: dict = Field(default={}, description="Additional metadata")


class HyperEdgeResponse(BaseModel):
    """HyperEdge response model with full details."""
    id: int = Field(description="Unique edge identifier")
    type: str = Field(description="Edge type (e.g., paper-extract, deduction)")
    subtype: Optional[str] = Field(None, description="Optional subtype")
    tail: List[int] = Field(description="Tail node IDs")
    head: List[int] = Field(description="Head node IDs")
    verified: bool = Field(description="Whether the edge is verified")
    reasoning: List = Field(default=[], description="Reasoning chain")
    metadata: dict = Field(default={}, description="Additional metadata")


class SubgraphResponse(BaseModel):
    """Subgraph response containing nodes and edges."""
    node_ids: List[int] = Field(description="IDs of nodes in the subgraph")
    edge_ids: List[int] = Field(description="IDs of edges in the subgraph")


class HydratedSubgraphResponse(BaseModel):
    """Hydrated subgraph response with full node and edge data."""
    nodes: List[dict] = Field(description="Full node objects")
    edges: List[dict] = Field(description="Full edge objects")


class PaginatedNodesResponse(BaseModel):
    """Paginated list of nodes."""
    items: List[dict] = Field(description="List of nodes")
    total: int = Field(description="Total number of nodes")
    page: int = Field(description="Current page number")
    size: int = Field(description="Page size")


class PaginatedEdgesResponse(BaseModel):
    """Paginated list of hyperedges."""
    items: List[dict] = Field(description="List of hyperedges")
    total: int = Field(description="Total number of hyperedges")
    page: int = Field(description="Current page number")
    size: int = Field(description="Page size")


class StatsResponse(BaseModel):
    """System statistics response."""
    node_count: int = Field(description="Total number of nodes")
    graph_available: bool = Field(description="Whether graph store is available")
    edge_count: int = Field(description="Total number of edges")
    node_types: dict = Field(description="Count of nodes by type")


@router.get(
    "/nodes/{node_id}",
    summary="Get node by ID",
    description="Retrieve a single node by its unique identifier.",
    response_model=NodeResponse,
    responses={
        200: {
            "description": "Node retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 251,
                        "type": "paper-extract",
                        "subtype": "premise",
                        "title": "YH10 高压超导 Tc≈303K",
                        "content": "fcc YH10 相在 400GPa 下超导，Tc≈303K",
                        "keywords": ["YH10", "超导", "高压氢化物"],
                        "belief": 0.65,
                        "status": "active",
                        "metadata": {"paper_id": "arxiv:2301.12345"}
                    }
                }
            }
        },
        404: {
            "description": "Node not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Node not found"}
                }
            }
        }
    }
)
async def get_node(node_id: int):
    """
    Get a single node by its ID.
    
    Returns complete node information including content, metadata, and belief scores.
    """
    node = await deps.storage.lance.load_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node.model_dump()


@router.get(
    "/hyperedges/{edge_id}",
    summary="Get hyperedge by ID",
    description="Retrieve a single hyperedge by its unique identifier.",
    response_model=HyperEdgeResponse,
    responses={
        200: {
            "description": "Hyperedge retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1234,
                        "type": "paper-extract",
                        "tail": [102, 5001],
                        "head": [5002],
                        "verified": True,
                        "reasoning": [{"title": "DFT+Eliashberg", "content": "基于 DFT 和 Eliashberg 方程的理论预测"}],
                        "metadata": {}
                    }
                }
            }
        },
        404: {
            "description": "Hyperedge not found",
            "content": {
                "application/json": {
                    "example": {"detail": "HyperEdge not found"}
                }
            }
        },
        503: {
            "description": "Graph store not available",
            "content": {
                "application/json": {
                    "example": {"detail": "Graph store not available"}
                }
            }
        }
    }
)
async def get_hyperedge(edge_id: int):
    """
    Get a single hyperedge by its ID.
    
    Returns complete hyperedge information including tail/head nodes and reasoning chain.
    Requires the graph store (Neo4j) to be available.
    """
    if not deps.storage.graph:
        raise HTTPException(status_code=503, detail="Graph store not available")
    edge = await deps.storage.graph.get_hyperedge(edge_id)
    if not edge:
        raise HTTPException(status_code=404, detail="HyperEdge not found")
    return edge.model_dump()


@router.get(
    "/nodes/{node_id}/subgraph",
    summary="Get node subgraph (IDs only)",
    description="Get subgraph around a node, returning only node and edge IDs.",
    response_model=SubgraphResponse,
    responses={
        200: {
            "description": "Subgraph retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "node_ids": [251, 102, 5001, 5002],
                        "edge_ids": [1234, 1235]
                    }
                }
            }
        },
        503: {
            "description": "Graph store not available",
            "content": {
                "application/json": {
                    "example": {"detail": "Graph store not available"}
                }
            }
        }
    }
)
async def get_node_subgraph(
    node_id: int,
    hops: int = Query(1, ge=1, le=5, description="Number of hops to traverse")
):
    """
    Get subgraph around a node (IDs only).
    
    Returns node and edge IDs within specified hop distance from the center node.
    Use the /nodes/{id}/subgraph/hydrated endpoint to get full node/edge data.
    """
    if not deps.storage.graph:
        raise HTTPException(status_code=503, detail="Graph store not available")
    node_ids, edge_ids = await deps.storage.graph.get_subgraph([node_id], hops=hops)
    return {"node_ids": list(node_ids), "edge_ids": list(edge_ids)}


@router.get(
    "/nodes/{node_id}/subgraph/hydrated",
    summary="Get hydrated subgraph",
    description="Get subgraph with full node and edge data, avoiding N+1 requests.",
    response_model=HydratedSubgraphResponse,
    responses={
        200: {
            "description": "Hydrated subgraph retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "nodes": [
                            {"id": 251, "type": "paper-extract", "content": "..."},
                            {"id": 102, "type": "paper-extract", "content": "..."}
                        ],
                        "edges": [
                            {"id": 1234, "type": "paper-extract", "tail": [102, 5001], "head": [5002]}
                        ]
                    }
                }
            }
        },
        503: {
            "description": "Graph store not available",
            "content": {
                "application/json": {
                    "example": {"detail": "Graph store not available"}
                }
            }
        }
    }
)
async def get_node_subgraph_hydrated(
    node_id: int,
    hops: int = Query(1, ge=1, le=5, description="Number of hops to traverse")
):
    """
    Get subgraph with full node and edge data.
    
    Returns complete node and edge objects within specified hop distance.
    This endpoint is more efficient than calling /nodes/{id}/subgraph followed by
    multiple individual node/edge lookups.
    """
    if not deps.storage.graph:
        raise HTTPException(status_code=503, detail="Graph store not available")

    node_ids, edge_ids = await deps.storage.graph.get_subgraph([node_id], hops=hops)

    # Load nodes and edges in parallel
    nodes_task = deps.storage.lance.load_nodes_bulk(list(node_ids))
    edges_task = asyncio.gather(*[deps.storage.graph.get_hyperedge(eid) for eid in edge_ids])
    nodes, edges = await asyncio.gather(nodes_task, edges_task)
    edges = [e for e in edges if e is not None]

    return {
        "nodes": [n.model_dump() for n in nodes],
        "edges": [e.model_dump() for e in edges],
    }


@router.get(
    "/nodes",
    summary="List nodes (paginated)",
    description="Get paginated list of nodes with optional type filtering.",
    response_model=PaginatedNodesResponse,
    responses={
        200: {
            "description": "Nodes retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {"id": 1, "type": "paper-extract", "title": "...", "content": "..."}
                        ],
                        "total": 1000,
                        "page": 1,
                        "size": 50
                    }
                }
            }
        }
    }
)
async def list_nodes(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    size: int = Query(50, ge=1, le=200, description="Number of items per page (max 200)"),
    type: Optional[str] = Query(None, description="Filter by node type")
):
    """
    List nodes with pagination and optional type filter.
    
    - **page**: Page number (1-indexed)
    - **size**: Items per page (1-200)
    - **type**: Optional filter by node type (e.g., 'paper-extract', 'deduction')
    """
    nodes = await deps.storage.lance.list_nodes(page=page, size=size, node_type=type)
    total = await deps.storage.lance.count_nodes(node_type=type)
    return {
        "items": [n.model_dump() for n in nodes],
        "total": total,
        "page": page,
        "size": size,
    }


@router.get(
    "/hyperedges",
    summary="List hyperedges (paginated)",
    description="Get paginated list of hyperedges. Requires Neo4j graph store.",
    response_model=PaginatedEdgesResponse,
    responses={
        200: {
            "description": "Hyperedges retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {"id": 1234, "type": "paper-extract", "tail": [102, 5001], "head": [5002]}
                        ],
                        "total": 500,
                        "page": 1,
                        "size": 50
                    }
                }
            }
        },
        503: {
            "description": "Graph store not available",
            "content": {
                "application/json": {
                    "example": {"detail": "Graph store not available"}
                }
            }
        }
    }
)
async def list_hyperedges(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    size: int = Query(50, ge=1, le=200, description="Number of items per page (max 200)")
):
    """
    List hyperedges with pagination.
    
    - **page**: Page number (1-indexed)
    - **size**: Items per page (1-200)
    
    **Note**: Requires Neo4j graph store to be available.
    """
    if not deps.storage.graph:
        raise HTTPException(status_code=503, detail="Graph store not available")

    # Use Neo4j to list edges with pagination
    async with deps.storage.graph._driver.session(database=deps.storage.graph._db) as session:
        skip = (page - 1) * size
        result = await session.run(
            "MATCH (h:Hyperedge) RETURN h.id AS id ORDER BY h.id SKIP $skip LIMIT $limit",
            skip=skip,
            limit=size,
        )
        edge_ids = [record["id"] async for record in result]

        count_result = await session.run("MATCH (h:Hyperedge) RETURN count(h) AS total")
        count_record = await count_result.single()
        total = count_record["total"] if count_record else 0

    edges = await asyncio.gather(*[deps.storage.graph.get_hyperedge(eid) for eid in edge_ids])
    edges = [e for e in edges if e is not None]

    return {
        "items": [e.model_dump() for e in edges],
        "total": total,
        "page": page,
        "size": size,
    }


@router.get(
    "/contradictions",
    summary="List contradiction hyperedges",
    description="Get all contradiction-type hyperedges. Requires Neo4j graph store.",
    response_model=List[dict],
    responses={
        200: {
            "description": "Contradictions retrieved successfully",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 2001,
                            "type": "contradiction",
                            "tail": [300, 301],
                            "head": [302],
                            "verified": True
                        }
                    ]
                }
            }
        },
        503: {
            "description": "Graph store not available",
            "content": {
                "application/json": {
                    "example": {"detail": "Graph store not available"}
                }
            }
        }
    }
)
async def list_contradictions():
    """
    List all contradiction hyperedges.
    
    Returns hyperedges of type 'contradiction' which represent detected
    logical contradictions between propositions in the knowledge graph.
    
    **Note**: Requires Neo4j graph store to be available.
    """
    if not deps.storage.graph:
        raise HTTPException(status_code=503, detail="Graph store not available")

    async with deps.storage.graph._driver.session(database=deps.storage.graph._db) as session:
        result = await session.run(
            "MATCH (h:Hyperedge {type: 'contradiction'}) RETURN h.id AS id ORDER BY h.id"
        )
        edge_ids = [record["id"] async for record in result]

    edges = await asyncio.gather(*[deps.storage.graph.get_hyperedge(eid) for eid in edge_ids])
    edges = [e for e in edges if e is not None]
    return [e.model_dump() for e in edges]


@router.get(
    "/stats",
    summary="Get system statistics",
    description="Get overview statistics about the knowledge graph.",
    response_model=StatsResponse,
    responses={
        200: {
            "description": "Statistics retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "node_count": 10000,
                        "graph_available": True,
                        "edge_count": 5000,
                        "node_types": {
                            "paper-extract": 8000,
                            "abstraction": 500,
                            "deduction": 1500
                        }
                    }
                }
            }
        }
    }
)
async def get_stats():
    """
    Get system statistics overview.
    
    Returns:
    - Total node count
    - Total edge count (if graph available)
    - Node count by type
    - Graph store availability status
    """
    node_count = await deps.storage.lance.count_nodes()
    graph_available = deps.storage.graph is not None

    stats = {
        "node_count": node_count,
        "graph_available": graph_available,
        "edge_count": 0,
        "node_types": {},
    }

    if graph_available:
        async with deps.storage.graph._driver.session(database=deps.storage.graph._db) as session:
            result = await session.run("MATCH (h:Hyperedge) RETURN count(h) AS total")
            record = await result.single()
            stats["edge_count"] = record["total"] if record else 0

    # Count nodes by type
    for ntype in ["paper-extract", "abstraction", "deduction", "conjecture"]:
        count = await deps.storage.lance.count_nodes(node_type=ntype)
        if count > 0:
            stats["node_types"][ntype] = count

    return stats
