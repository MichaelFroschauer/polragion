from __future__ import annotations

from collections.abc import Sequence

from polragion.domain.vector_store import (
    VectorDocument,
    VectorSearchHit,
)
from polragion.settings import Settings


class FakeVectorStore:
    def __init__(self, _settings: Settings | None = None) -> None:
        self.documents: list[VectorDocument] = []
        self.search_results: list[VectorSearchHit] = []
        self.initialized = False
        self.closed = False
        self.ready = True
        self.last_search: dict[str, object] | None = None

    def initialize(self) -> None:
        self.initialized = True

    def upsert(self, documents: Sequence[VectorDocument]) -> None:
        self.documents.extend(documents)

    def search(
        self,
        query: str,
        *,
        limit: int,
        project_id: str | None = None,
        score_threshold: float | None = None,
    ) -> list[VectorSearchHit]:
        self.last_search = {
            "query": query,
            "limit": limit,
            "project_id": project_id,
            "score_threshold": score_threshold,
        }
        return self.search_results[:limit]

    def is_ready(self) -> bool:
        return self.ready

    def close(self) -> None:
        self.closed = True
