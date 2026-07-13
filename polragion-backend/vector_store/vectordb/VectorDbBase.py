from abc import ABC, abstractmethod
from typing import Any

from vector_store.model.QdrantModel import IngestModel

class VectorDbBase(ABC):

    @abstractmethod
    def ingest(self, data: list[IngestModel]) -> None:
        pass

    @abstractmethod
    def search(self, text: str) -> list[dict[str, Any]]:
        pass
