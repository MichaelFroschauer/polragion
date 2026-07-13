import logging
import uuid
from typing import Any

from qdrant_client import QdrantClient, models
from model.QdrantModel import IngestModel
from config import VectorDBConfig
from vectordb.VectorDbBase import VectorDbBase


logger = logging.getLogger(__name__)

def _qdrant_point_id(id_string: str) -> str:
    POINT_NAMESPACE = uuid.UUID("8604873a-0779-49ef-81c4-840c4567d718")
    return str(uuid.uuid5(POINT_NAMESPACE, id_string))


class QdrantVectorDb(VectorDbBase):

    def __init__(self) -> None:
        self.config = VectorDBConfig()

        self.collection_name = self.config.qdrant.collection_name
        self.batch_size = self.config.qdrant.batch_size
        self.parallel = self.config.qdrant.parallel
        self.model_name = self.config.fastembed.model_name

        self.client = QdrantClient(url=self.config.qdrant.client_connection)
        self._ensure_collection()
        logger.info("Initializing Qdrant vector database for collection '%s'", self.collection_name)

    def _ensure_collection(self) -> None:
        if self.client.collection_exists(self.collection_name):
            logger.debug("Qdrant collection '%s' already exists",self.collection_name)
            return

        logger.info("Creating Qdrant collection '%s' using model '%s'",self.collection_name, self.model_name)
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=self.client.get_embedding_size(self.model_name),
                distance=models.Distance.COSINE,
            ),
        )
        logger.info("Created Qdrant collection '%s'", self.collection_name)


    def ingest(self, data: list[IngestModel]) -> None:
        if not data:
            logger.debug("Skipping Qdrant ingestion because no data was provided")
            return

        logger.info("Ingesting %d points into Qdrant collection '%s'", len(data), self.collection_name)

        vector_ids: list[str] = [_qdrant_point_id(d.id) for d in data]
        documents: list[models.Document] = [models.Document(text=d.text, model=self.model_name) for d in data]
        payloads: list[dict] = [d.payload for d in data]

        self.client.upload_collection(
            collection_name=self.collection_name,
            vectors=documents,
            payload=payloads,
            ids=vector_ids,
            batch_size=self.batch_size,
            parallel=self.parallel
        )

        logger.info("Successfully ingested %d points into Qdrant collection '%s'", len(data), self.collection_name)


    def search(self, text: str, limit: int = 5) -> list[dict[str, Any]]:
        logger.debug("Searching Qdrant collection '%s' with limit %d", self.collection_name, limit)

        response = self.client.query_points(
            collection_name=self.collection_name,
            query=models.Document(text=text, model=self.model_name),
            limit=limit,
            with_payload=True,
        )
        found_points = [point.payload for point in response.points if point.payload is not None]

        logger.debug("Qdrant search returned %d results from collection '%s'", len(found_points), self.collection_name)
        return found_points
