from abc import ABC, abstractmethod
from model.IngestModel import IngestModel

class VectorDbBase(ABC):

    @abstractmethod
    def ingest(self, data: IngestModel) -> None:
        pass

    @abstractmethod
    def search(self):
        pass
