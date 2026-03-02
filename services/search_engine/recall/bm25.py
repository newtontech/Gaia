# services/search_engine/recall/bm25.py
from libs.storage.lance_store import LanceStore


class BM25Recall:
    def __init__(self, lance_store: LanceStore):
        self._store = lance_store

    async def recall(self, query: str, k: int = 100) -> list[tuple[int, float]]:
        return await self._store.fts_search(query, k=k)
