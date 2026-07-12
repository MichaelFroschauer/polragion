import logging
import uuid
from typing import List, Any

from qdrant_client import QdrantClient, models
from model.QdrantModel import IngestModel
from config import VectorDBConfig, QdrantConfig
from vectordb.VectorDbBase import VectorDbBase


def _qdrant_point_id(id_string: str) -> str:
    POINT_NAMESPACE = uuid.UUID("8604873a-0779-49ef-81c4-840c4567d718")
    return str(uuid.uuid5(POINT_NAMESPACE, id_string))


class QdrantVectorDb(VectorDbBase):

    def __init__(self) -> None:
        self.config = VectorDBConfig()

        self.collection_name = self.config.qdrant.collection_name
        self.model_name = self.config.fastembed.model_name

        self.client = QdrantClient(url=self.config.qdrant.client_connection)
        self._ensure_collection()
        self.logger = logging.getLogger(__name__)

    def _ensure_collection(self) -> None:
        if self.client.collection_exists(self.collection_name):
            return

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=self.client.get_embedding_size(self.model_name),
                distance=models.Distance.COSINE,
            ),
        )


    def ingest(self, data: IngestModel) -> None:
        vector_id: str = _qdrant_point_id(data.id)
        document: str = data.text
        payload: dict = data.payload

        self.client.upload_collection(
            collection_name=self.collection_name,
            vectors=[
                models.Document(
                    text=document,
                    model=self.model_name,
                )
            ],
            payload=[payload],
            ids=[vector_id]
        )


    def ingest_many(self, data: List[IngestModel]) -> None:
        """TODO: Currently a test method"""
        docs = [
            "Qdrant has a LangChain integration for chatbots.",
            "Qdrant has a LlamaIndex integration for agents.",
        ]
        metadata = [
            {"source": "langchain-docs"},
            {"source": "llamaindex-docs"},
        ]
        ids = [42, 2]

        payloads = [
            {
                "document": document,
                **document_metadata,
            }
            for document, document_metadata in zip(docs, metadata)
        ]
        self.client.upload_collection(
            collection_name=self.collection_name,
            vectors=[
                models.Document(
                    text=document,
                    model=self.model_name,
                )
                for document in docs
            ],
            payload=payloads,
            ids=ids,
        )

    def search(self, text: str, limit: int = 5) -> list[dict[str, Any]]:
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=models.Document(text=text, model=self.model_name),
            limit=limit,
            with_payload=True,
        )
        found_points = [point.payload for point in response.points if point.payload is not None]
        return found_points
