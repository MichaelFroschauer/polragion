from abc import ABC, abstractmethod
from typing import Self, Any

from pydantic import BaseModel

from model.QdrantModel import IngestModel


class VectorStoreModel(BaseModel, ABC):

    def to_dictionary(self) -> dict:
        """JSON-Compatible Qdrant-Payload."""
        return self.model_dump(mode="json")

    @classmethod
    def from_dictionary(cls, data: dict[str, Any]) -> Self:
        """Convert generic dictionary to PolarionWorkItem."""
        return cls.model_validate(data, extra="ignore")

    @abstractmethod
    def to_ingest_model(self) -> IngestModel:
        pass
