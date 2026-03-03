from fastapi import APIRouter, HTTPException
from services.gateway.deps import deps

router = APIRouter(tags=["read"])


@router.get("/nodes/{node_id}")
async def get_node(node_id: int):
    node = await deps.storage.lance.load_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node.model_dump()


@router.get("/hyperedges/{edge_id}")
async def get_hyperedge(edge_id: int):
    if not deps.storage.graph:
        raise HTTPException(status_code=503, detail="Graph store not available")
    edge = await deps.storage.graph.get_hyperedge(edge_id)
    if not edge:
        raise HTTPException(status_code=404, detail="HyperEdge not found")
    return edge.model_dump()


@router.get("/nodes/{node_id}/subgraph")
async def get_node_subgraph(node_id: int, hops: int = 1):
    if not deps.storage.graph:
        raise HTTPException(status_code=503, detail="Graph store not available")
    node_ids, edge_ids = await deps.storage.graph.get_subgraph([node_id], hops=hops)
    return {"node_ids": list(node_ids), "edge_ids": list(edge_ids)}
