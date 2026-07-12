from abc import ABC, abstractmethod
from typing import Any

from model.QdrantModel import IngestModel

class VectorDbBase(ABC):

    @abstractmethod
    def ingest(self, data: IngestModel) -> None:
        pass

    @abstractmethod
    def search(self, text: str) -> list[dict[str, Any]]:
        pass
