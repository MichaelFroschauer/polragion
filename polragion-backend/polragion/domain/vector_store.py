from collections.abc import Mapping, Iterable
from dataclasses import dataclass
from typing import Protocol

JsonValue = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]
Metadata = dict[str, JsonValue]


@dataclass(frozen=True, slots=True)
class VectorDocument:
    """Vector-store-independent document to be embedded and indexed."""

    id: str
    text: str
    metadata: Metadata


@dataclass(frozen=True, slots=True)
class VectorSearchHit:
    """Vector-store-independent search result."""

    document_id: str
    point_id: str
    score: float
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
        project_id: str | None = None,
        score_threshold: float | None = None,
    ) -> list[VectorSearchHit]:
        """Find documents ordered by descending semantic similarity."""
        ...

    def is_ready(self) -> bool:
        """Return whether the backing service can currently be reached."""
        ...

    def close(self) -> None:
        """Release resources held by the adapter."""
        ...
