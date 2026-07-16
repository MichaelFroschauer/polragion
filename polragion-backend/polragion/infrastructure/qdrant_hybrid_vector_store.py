import logging
from collections.abc import Iterable, Mapping
from typing import Any, Final

from fastembed import SparseEmbedding, SparseTextEmbedding, TextEmbedding
from fastembed.rerank.cross_encoder import TextCrossEncoder
from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse

from polragion.domain.vector_store import JsonValue, VectorDocument, VectorSearchHit
from polragion.infrastructure.errors import (
    VectorStoreConfigurationError,
    VectorStoreUnavailableError,
)
from polragion.infrastructure.qdrant_utils import (
    _DOCUMENT_ID_PAYLOAD_KEY,
    _INDEX_MODEL_PAYLOAD_KEY,
    _INDEX_SCHEMA_PAYLOAD_KEY,
    _RESERVED_PAYLOAD_KEYS,
    qdrant_point_id,
)
from polragion.settings import Settings

logger = logging.getLogger(__name__)

_DENSE_VECTOR_NAME: Final = "text-dense"
_SPARSE_VECTOR_NAME: Final = "text-sparse"
_DOCUMENT_TEXT_PAYLOAD_KEY: Final = "_document_text"

# These sparse models calculate corpus-level IDF inside Qdrant.
_SPARSE_MODELS_REQUIRING_IDF: Final = frozenset(
    {
        "Qdrant/bm25",
        "Qdrant/bm42-all-minilm-l6-v2-attentions",
        "Qdrant/minicoil-v1",
    }
)


class QdrantHybridVectorStore:
    """Dense+sparse retrieval with Qdrant RRF and FastEmbed reranking.

    ``score_threshold`` in :meth:`search` applies to the final cross-encoder
    score. Cross-encoder score ranges are model-specific.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._collection_name = settings.qdrant_collection_name
        self._dense_model_name = settings.fastembed_dense_model
        self._sparse_model_name = settings.fastembed_sparse_model
        self._reranker_model_name = settings.fastembed_reranker_model
        self._candidate_limit = max(1, int(getattr(settings, "qdrant_hybrid_candidate_limit", 50)))

        self._client = QdrantClient(url=settings.qdrant_url)
        self._sparse_model: SparseTextEmbedding | None = None
        self._dense_model: TextEmbedding | None = None
        self._reranker: TextCrossEncoder | None = None

    def initialize(self) -> None:
        try:
            if not self._reranker_model_name:
                raise VectorStoreConfigurationError("fastembed_reranker_model must be configured")

            self._sparse_model = SparseTextEmbedding(model_name=self._sparse_model_name)
            self._dense_model = TextEmbedding(model_name=self._dense_model_name)
            self._reranker = TextCrossEncoder(model_name=self._reranker_model_name)

            expected_size = self._client.get_embedding_size(self._dense_model_name)

            if not self._client.collection_exists(self._collection_name):
                logger.info(
                    "Creating Qdrant collection '%s' with dense model '%s', "
                    "sparse model '%s', and reranker '%s'",
                    self._collection_name,
                    self._dense_model_name,
                    self._sparse_model_name,
                    self._reranker_model_name,
                )
                self._client.create_collection(
                    collection_name=self._collection_name,
                    vectors_config={
                        _DENSE_VECTOR_NAME: models.VectorParams(
                            size=expected_size,
                            distance=models.Distance.COSINE,
                        )
                    },
                    sparse_vectors_config={
                        _SPARSE_VECTOR_NAME: models.SparseVectorParams(
                            index=models.SparseIndexParams(on_disk=True),
                            modifier=self._sparse_modifier(),
                        )
                    },
                )

            self._validate_collection_layout(expected_size)
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

    def upsert(self, documents: Iterable[VectorDocument]) -> None:
        document_list = list(documents)
        if not document_list:
            return

        self._ensure_initialized()
        self._validate_document_metadata(document_list)

        texts = [document.text for document in document_list]

        try:
            dense_embeddings = self._make_dense_passage_embeddings(texts)
            sparse_embeddings = self._make_sparse_passage_embeddings(texts)

            if not (
                len(document_list)
                == len(dense_embeddings)
                == len(sparse_embeddings)
            ):
                raise VectorStoreUnavailableError(
                    "FastEmbed returned an unexpected number of embeddings"
                )

            points: list[models.PointStruct] = []
            for document, dense_embedding, sparse_embedding in zip(
                document_list,
                dense_embeddings,
                sparse_embeddings,
                strict=True,
            ):
                payload = dict(document.metadata)
                payload[_DOCUMENT_ID_PAYLOAD_KEY] = document.id
                payload[_INDEX_MODEL_PAYLOAD_KEY] = self._dense_model_name
                payload[_INDEX_SCHEMA_PAYLOAD_KEY] = (
                    self._settings.index_schema_version
                )
                payload[_DOCUMENT_TEXT_PAYLOAD_KEY] = document.text

                points.append(
                    models.PointStruct(
                        id=qdrant_point_id(document.id),
                        vector={
                            _DENSE_VECTOR_NAME: dense_embedding.tolist(),
                            _SPARSE_VECTOR_NAME: models.SparseVector(
                                indices=sparse_embedding.indices.tolist(),
                                values=sparse_embedding.values.tolist(),
                            ),
                        },
                        payload=payload,
                    )
                )

            self._client.upload_points(
                collection_name=self._collection_name,
                points=points,
                batch_size=self._settings.qdrant_batch_size,
                parallel=self._settings.qdrant_parallel,
                wait=True,
            )
        except VectorStoreConfigurationError:
            raise
        except VectorStoreUnavailableError:
            raise
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
        if limit <= 0 or not query.strip():
            return []

        self._ensure_initialized()

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

        candidate_limit = max(limit, self._candidate_limit)

        try:
            dense_query = self._make_dense_query_embedding(query)
            sparse_query = self._make_sparse_query_embedding(query)

            response = self._client.query_points(
                collection_name=self._collection_name,
                prefetch=[
                    models.Prefetch(
                        query=dense_query,
                        using=_DENSE_VECTOR_NAME,
                        limit=candidate_limit,
                    ),
                    models.Prefetch(
                        query=sparse_query,
                        using=_SPARSE_VECTOR_NAME,
                        limit=candidate_limit,
                    ),
                ],
                query=models.FusionQuery(fusion=models.Fusion.RRF),
                query_filter=query_filter,
                limit=candidate_limit,
                with_payload=True,
            )

            candidates: list[
                tuple[models.ScoredPoint, dict[str, Any], str]
            ] = []
            for point in response.points:
                if point.payload is None:
                    continue

                payload = dict(point.payload)
                document_text = payload.get(_DOCUMENT_TEXT_PAYLOAD_KEY)
                if not isinstance(document_text, str):
                    logger.warning(
                        "Skipping Qdrant point %s because its document text is missing",
                        point.id,
                    )
                    continue

                candidates.append((point, payload, document_text))

            if not candidates:
                return []

            reranker = self._require_reranker()
            rerank_scores = list(
                reranker.rerank(
                    query,
                    [document_text for _, _, document_text in candidates],
                    batch_size=self._settings.qdrant_batch_size,
                )
            )
            if len(rerank_scores) != len(candidates):
                raise VectorStoreUnavailableError(
                    "FastEmbed reranker returned an unexpected number of scores"
                )

            ranked = sorted(
                zip(candidates, rerank_scores, strict=True),
                key=lambda item: (
                    float(item[1]),
                    float(item[0][0].score),
                ),
                reverse=True,
            )

            hits: list[VectorSearchHit] = []
            for (point, payload, _), rerank_score in ranked:
                score = float(rerank_score)
                if score_threshold is not None and score < score_threshold:
                    continue

                document_id = str(
                    payload.pop(_DOCUMENT_ID_PAYLOAD_KEY, point.id)
                )
                payload.pop(_DOCUMENT_TEXT_PAYLOAD_KEY, None)
                for key in _RESERVED_PAYLOAD_KEYS:
                    payload.pop(key, None)

                hits.append(
                    VectorSearchHit(
                        document_id=document_id,
                        point_id=str(point.id),
                        score=score,
                        metadata=self._as_json_mapping(payload),
                    )
                )
                if len(hits) >= limit:
                    break

            return hits
        except VectorStoreConfigurationError:
            raise
        except VectorStoreUnavailableError:
            raise
        except (UnexpectedResponse, OSError, TimeoutError) as exc:
            raise VectorStoreUnavailableError("Qdrant search failed") from exc
        except Exception as exc:
            raise VectorStoreUnavailableError("Qdrant search failed") from exc

    def _make_sparse_passage_embeddings(
        self, texts: Iterable[str]
    ) -> list[SparseEmbedding]:
        model = self._require_sparse_model()
        return list(
            model.passage_embed(
                texts,
                batch_size=self._settings.qdrant_batch_size,
                parallel=self._settings.qdrant_parallel,
            )
        )

    def _make_dense_passage_embeddings(self, texts: Iterable[str]) -> list[Any]:
        model = self._require_dense_model()
        return list(
            model.passage_embed(
                texts,
                batch_size=self._settings.qdrant_batch_size,
                parallel=self._settings.qdrant_parallel,
            )
        )

    def _make_sparse_query_embedding(self, query: str) -> models.SparseVector:
        model = self._require_sparse_model()
        embedding = next(
            iter(
                model.query_embed(
                    query,
                    batch_size=1,
                    parallel=self._settings.qdrant_parallel,
                )
            )
        )
        return models.SparseVector(
            indices=embedding.indices.tolist(),
            values=embedding.values.tolist(),
        )

    def _make_dense_query_embedding(self, query: str) -> list[float]:
        model = self._require_dense_model()
        embedding = next(
            iter(
                model.query_embed(
                    query,
                    batch_size=1,
                    parallel=self._settings.qdrant_parallel,
                )
            )
        )
        return embedding.tolist()

    def _validate_collection_layout(self, expected_dense_size: int) -> None:
        collection = self._client.get_collection(self._collection_name)
        vectors = collection.config.params.vectors
        sparse_vectors = collection.config.params.sparse_vectors or {}

        if not isinstance(vectors, dict):
            raise VectorStoreConfigurationError(
                f"Collection '{self._collection_name}' uses an unnamed dense "
                "vector and must be recreated or migrated for hybrid search"
            )

        dense_config = vectors.get(_DENSE_VECTOR_NAME)
        if dense_config is None:
            raise VectorStoreConfigurationError(
                f"Collection '{self._collection_name}' is missing dense vector "
                f"'{_DENSE_VECTOR_NAME}'"
            )
        if dense_config.size != expected_dense_size:
            raise VectorStoreConfigurationError(
                f"Dense vector '{_DENSE_VECTOR_NAME}' has size "
                f"{dense_config.size}, expected {expected_dense_size}"
            )
        if dense_config.distance != models.Distance.COSINE:
            raise VectorStoreConfigurationError(
                f"Dense vector '{_DENSE_VECTOR_NAME}' must use cosine distance"
            )

        sparse_config = sparse_vectors.get(_SPARSE_VECTOR_NAME)
        if sparse_config is None:
            raise VectorStoreConfigurationError(
                f"Collection '{self._collection_name}' is missing sparse vector "
                f"'{_SPARSE_VECTOR_NAME}'"
            )

        expected_modifier = self._sparse_modifier()
        if expected_modifier is not None and sparse_config.modifier != expected_modifier:
            raise VectorStoreConfigurationError(
                f"Sparse vector '{_SPARSE_VECTOR_NAME}' must use modifier "
                f"'{expected_modifier.value}' for model '{self._sparse_model_name}'"
            )

    def _validate_document_metadata(
        self, documents: Iterable[VectorDocument]
    ) -> None:
        reserved_keys = set(_RESERVED_PAYLOAD_KEYS)
        reserved_keys.update(
            {
                _DOCUMENT_ID_PAYLOAD_KEY,
                _INDEX_MODEL_PAYLOAD_KEY,
                _INDEX_SCHEMA_PAYLOAD_KEY,
                _DOCUMENT_TEXT_PAYLOAD_KEY,
            }
        )

        for document in documents:
            collisions = reserved_keys.intersection(document.metadata)
            if collisions:
                keys = ", ".join(sorted(collisions))
                raise VectorStoreConfigurationError(
                    f"Document '{document.id}' metadata uses reserved keys: {keys}"
                )

    def _sparse_modifier(self) -> models.Modifier | None:
        if self._sparse_model_name in _SPARSE_MODELS_REQUIRING_IDF:
            return models.Modifier.IDF
        return None

    def _ensure_initialized(self) -> None:
        self._require_dense_model()
        self._require_sparse_model()
        self._require_reranker()

    def _require_dense_model(self) -> TextEmbedding:
        if self._dense_model is None:
            raise VectorStoreConfigurationError(
                "QdrantHybridVectorStore.initialize() must be called first"
            )
        return self._dense_model

    def _require_sparse_model(self) -> SparseTextEmbedding:
        if self._sparse_model is None:
            raise VectorStoreConfigurationError(
                "QdrantHybridVectorStore.initialize() must be called first"
            )
        return self._sparse_model

    def _require_reranker(self) -> TextCrossEncoder:
        if self._reranker is None:
            raise VectorStoreConfigurationError(
                "QdrantHybridVectorStore.initialize() must be called first"
            )
        return self._reranker

    @staticmethod
    def _as_json_mapping(payload: Mapping[str, Any]) -> dict[str, JsonValue]:
        return dict(payload)  # type: ignore[return-value]

    def is_ready(self) -> bool:
        try:
            models_ready = (
                self._dense_model is not None
                and self._sparse_model is not None
                and self._reranker is not None
            )
            return models_ready and self._client.collection_exists(
                self._collection_name
            )
        except Exception:
            logger.exception("Qdrant readiness check failed")
            return False

    def close(self) -> None:
        self._client.close()