import logging
import uuid
from collections.abc import Mapping, Iterable
from typing import Any

from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse

from polragion.domain.vector_store import (
    JsonValue,
    VectorDocument,
    VectorSearchHit,
)
from polragion.infrastructure.errors import (
    VectorStoreConfigurationError,
    VectorStoreUnavailableError,
)
from polragion.settings import Settings

logger = logging.getLogger(__name__)

_POINT_NAMESPACE = uuid.UUID("8604873a-0779-49ef-81c4-840c4567d718")
_DOCUMENT_ID_PAYLOAD_KEY = "_polragion_document_id"
_INDEX_MODEL_PAYLOAD_KEY = "_polragion_embedding_model"
_INDEX_SCHEMA_PAYLOAD_KEY = "_polragion_schema_version"
_RESERVED_PAYLOAD_KEYS = {
    _DOCUMENT_ID_PAYLOAD_KEY,
    _INDEX_MODEL_PAYLOAD_KEY,
    _INDEX_SCHEMA_PAYLOAD_KEY,
}


def qdrant_point_id(logical_id: str) -> str:
    """Create a deterministic UUID accepted by Qdrant."""

    return str(uuid.uuid5(_POINT_NAMESPACE, logical_id))


class QdrantVectorStore:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._collection_name = settings.qdrant_collection_name
        self._model_name = settings.fastembed_model
        self._client = QdrantClient(url=settings.qdrant_url)

    def initialize(self) -> None:
        try:
            expected_size = self._client.get_embedding_size(self._model_name)

            if not self._client.collection_exists(self._collection_name):
                logger.info(
                    "Creating Qdrant collection '%s' for model '%s'",
                    self._collection_name,
                    self._model_name,
                )
                self._client.create_collection(
                    collection_name=self._collection_name,
                    vectors_config=models.VectorParams(
                        size=expected_size,
                        distance=models.Distance.COSINE,
                    ),
                )
                return

            collection_info = self._client.get_collection(self._collection_name)
            self._validate_collection(collection_info, expected_size)
            logger.info(
                "Using validated Qdrant collection '%s'",
                self._collection_name,
            )
        except VectorStoreConfigurationError:
            raise
        except Exception as exc:
            raise VectorStoreUnavailableError(
                f"Could not initialize Qdrant at {self._settings.qdrant_url}"
            ) from exc

    def _validate_collection(self, collection_info: Any, expected_size: int) -> None:
        vectors = collection_info.config.params.vectors

        if isinstance(vectors, Mapping):
            raise VectorStoreConfigurationError(
                f"Collection '{self._collection_name}' uses named vectors, "
                "but Polragion expects one unnamed vector."
            )

        actual_size = getattr(vectors, "size", None)
        actual_distance = getattr(vectors, "distance", None)

        if actual_size != expected_size:
            raise VectorStoreConfigurationError(
                f"Collection '{self._collection_name}' has vector size "
                f"{actual_size}, expected {expected_size} for model "
                f"'{self._model_name}'. Use a new collection prefix or schema version."
            )

        if actual_distance != models.Distance.COSINE:
            raise VectorStoreConfigurationError(
                f"Collection '{self._collection_name}' uses distance "
                f"{actual_distance}, expected cosine distance."
            )

    def upsert(self, documents: Iterable[VectorDocument]) -> None:
        if not documents:
            return

        payloads: list[dict[str, Any]] = []
        for document in documents:
            payload = dict(document.metadata)
            payload[_DOCUMENT_ID_PAYLOAD_KEY] = document.id
            payload[_INDEX_MODEL_PAYLOAD_KEY] = self._model_name
            payload[_INDEX_SCHEMA_PAYLOAD_KEY] = self._settings.index_schema_version
            payloads.append(payload)

        try:
            self._client.upload_collection(
                collection_name=self._collection_name,
                vectors=[
                    models.Document(text=document.text, model=self._model_name)
                    for document in documents
                ],
                payload=payloads,
                ids=[qdrant_point_id(document.id) for document in documents],
                batch_size=self._settings.qdrant_batch_size,
                parallel=self._settings.qdrant_parallel,
                wait=True,
            )
        except Exception as exc:
            raise VectorStoreUnavailableError("Qdrant ingestion failed") from exc

    def search(
        self,
        query: str,
        *,
        limit: int,
        project_id: str | None = None,
        score_threshold: float | None = None,
    ) -> list[VectorSearchHit]:
        query_filter = None
        if project_id is not None:
            query_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="project_id",
                        match=models.MatchValue(value=project_id),
                    )
                ]
            )

        try:
            response = self._client.query_points(
                collection_name=self._collection_name,
                query=models.Document(text=query, model=self._model_name),
                query_filter=query_filter,
                limit=limit,
                score_threshold=score_threshold,
                with_payload=True,
            )
        except (UnexpectedResponse, OSError, TimeoutError) as exc:
            raise VectorStoreUnavailableError("Qdrant search failed") from exc
        except Exception as exc:
            raise VectorStoreUnavailableError("Qdrant search failed") from exc

        hits: list[VectorSearchHit] = []
        for point in response.points:
            if point.payload is None:
                continue

            payload = dict(point.payload)
            document_id = str(payload.pop(_DOCUMENT_ID_PAYLOAD_KEY, point.id))
            for key in _RESERVED_PAYLOAD_KEYS:
                payload.pop(key, None)

            hits.append(
                VectorSearchHit(
                    document_id=document_id,
                    point_id=str(point.id),
                    score=float(point.score),
                    metadata=self._as_json_mapping(payload),
                )
            )

        return hits

    @staticmethod
    def _as_json_mapping(payload: Mapping[str, Any]) -> dict[str, JsonValue]:
        # Qdrant payloads are JSON-compatible. The conversion keeps the type
        # boundary explicit without coupling the domain layer to Qdrant types.
        return dict(payload)  # type: ignore[return-value]

    def is_ready(self) -> bool:
        try:
            return self._client.collection_exists(self._collection_name)
        except Exception:
            logger.exception("Qdrant readiness check failed")
            return False

    def close(self) -> None:
        self._client.close()
