from collections.abc import Mapping, Iterable
from dataclasses import dataclass
from typing import Protocol, Collection

from polragion.infrastructure.db_filter import DbFilter

JsonValue = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]
Metadata = dict[str, JsonValue]


@dataclass(frozen=True, slots=True)
class VectorDocument:
    """Vector-store-independent document to be embedded and indexed."""

    id: str
    dense_text: str
    sparse_text: str
    reranker_text: str
    metadata: Metadata


@dataclass(frozen=True, slots=True)
class VectorSearchHit:
    """Vector-store-independent search result."""

    document_id: str
    point_id: str
    score: float
    reranker_score: float | None
    metadata: Mapping[str, JsonValue]


class VectorStore(Protocol):
    """Port implemented by concrete vector database adapters."""

    def initialize(self) -> None:
        """Create or validate all required infrastructure."""
        ...

    def upsert(self, documents: Iterable[VectorDocument]) -> None:
        """Insert or replace documents using their stable logical IDs."""
        ...

    def search(
        self,
        query: str,
        *,
        limit: int,
        db_filters: Collection[DbFilter] | None = None,
        exact_search: bool = False,
        score_threshold: float | None = None,
        **kwargs
    ) -> list[VectorSearchHit]:
        """Find documents ordered by descending semantic similarity."""
        ...

    def get_facet(self, key: str) -> list[str]:
        """Find facet of the vector database by key."""
        ...

    def is_ready(self) -> bool:
        """Return whether the backing service can currently be reached."""
        ...

    def close(self) -> None:
        """Release resources held by the adapter."""
        ...
