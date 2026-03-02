"""Dependency injection — singleton services created at startup."""

from __future__ import annotations

from libs.storage import StorageConfig, StorageManager
from services.search_engine.engine import SearchEngine
from services.commit_engine.engine import CommitEngine
from services.commit_engine.store import CommitStore
from services.inference_engine.engine import InferenceEngine


class Dependencies:
    """Holds all service singletons."""

    def __init__(self, config: StorageConfig | None = None):
        self.config = config or StorageConfig()
        self.storage: StorageManager | None = None
        self.search_engine: SearchEngine | None = None
        self.commit_engine: CommitEngine | None = None
        self.inference_engine: InferenceEngine | None = None

    def initialize(self, storage_config: StorageConfig | None = None):
        """Create all services. Call once at startup."""
        config = storage_config or self.config
        self.storage = StorageManager(config)
        self.search_engine = SearchEngine(self.storage)
        commit_store = CommitStore(storage_path=config.lancedb_path + "/commits")
        self.commit_engine = CommitEngine(
            storage=self.storage,
            commit_store=commit_store,
            search_engine=self.search_engine,
        )
        self.inference_engine = InferenceEngine(self.storage)

    async def cleanup(self):
        """Shut down services gracefully."""
        if self.storage:
            await self.storage.close()


# Global instance
deps = Dependencies()
