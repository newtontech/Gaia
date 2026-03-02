from libs.storage.vector_search.base import VectorSearchClient


class VectorRecall:
    def __init__(self, vector_client: VectorSearchClient):
        self._client = vector_client

    async def recall(self, embedding: list[float], k: int = 100) -> list[tuple[int, float]]:
        """Returns [(node_id, distance), ...] sorted by distance ascending."""
        return await self._client.search(embedding, k=k)
